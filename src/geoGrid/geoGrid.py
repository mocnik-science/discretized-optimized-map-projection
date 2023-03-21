from collections import OrderedDict
import gzip
import numpy as np
import os
import pandas as pd
import pickle
from PIL import Image, ImageDraw, ImageFont
import pyproj
from scipy.optimize import minimize_scalar
from scipy.spatial import KDTree
import shapefile
import shapely
import shutil
from sklearn.neighbors import BallTree
from sklearn.metrics.pairwise import haversine_distances
import warnings

from src.common.functions import *
from src.common.timer import timer
from src.geometry.common import *
from src.geometry.cartesian import *
from src.geometry.dggrid import DGGRID
from src.geometry.geo import *
from src.geometry.naturalEarth import NaturalEarth
from src.geoGrid.geoGridCell import *

warnings.filterwarnings('ignore')

class GeoGrid:
  def __init__(self, settings, callbackStatus=lambda status, energy: None):
    # save settings
    self.__settings = settings
    # init
    self.__gridStats = None
    self.__cells = None
    self.__pathTmp = '_tmp'
    self.__step = 0
    self.__ballTree = None
    self.__ballTreeCellsId1s = None
    # load data
    filename = 'cells-{resolution}.pickle.gzip'.format(resolution=self.__settings.resolution)
    if os.path.exists(filename):
      callbackStatus('loading cells and indices from proxy file ...', None)
      with timer('load data from proxy file'):
        with gzip.open(filename, 'rb') as f:
          data = pickle.load(f)
    else:
      callbackStatus('creating cells and indices, and save them to proxy file ...', None)
      with timer('create cells'):
        dataCells = self.createCells(resolution=self.__settings.resolution)
      with timer('compute ball tree'):
        dataBallTree = self.createBallTree(dataCells)
      with timer('save data to proxy file'):
        data = {
          **dataCells,
          **dataBallTree,
        }
        with gzip.open(filename, 'wb') as f:
          pickle.dump(data, f)
    for k, v in data.items():
      setattr(self, '_{self.__class__.__name__}{k}'.format(self=self, k=k) if k.startswith('__') else k, v)
    # empty the tmp path
    if os.path.exists(self.__pathTmp):
      shutil.rmtree(self.__pathTmp)
    # update the settings
    self.__settings.updateGridStats(self.__gridStats)
    # calibrate
    with timer('calibrate'):
      self.calibrate(callbackStatus)
    # compute the force without applying the step
    self.performStep(_onlyComputeNextForces=True)

  @staticmethod
  def createCells(resolution):
    dggrid = DGGRID(executable='DGGRID/build/src/apps/dggrid/dggrid')
    # get grid stats
    gridStats, _ = dggrid.stats(resolution=resolution)
    # get grid cells
    dggridCells, _ = dggrid.generate(resolution=resolution)
    # create GeoGridCells
    cells = {}
    cellsById1 = {}
    nextId2 = max(dggridCells.keys()) + 1
    for dLon in [None, -360, 360]:
      for dggridCell in dggridCells.values():
        if dLon is None:
          id2 = dggridCell.id
        else:
          id2 = nextId2
          nextId2 += 1
        cells[id2] = GeoGridCell(id2, dggridCell, dLon=dLon)
        if dggridCell.id not in cellsById1:
          cellsById1[dggridCell.id] = []
        cellsById1[dggridCell.id].append(cells[id2])
    # identify poles
    polesById1 = {}
    for cell in cells.values():
      if cell._id1 == cell._id2 and abs(cell._centreOriginal.x) < 1e-10 and (abs(cell._centreOriginal.y - 90) < 1e-10 or abs(cell._centreOriginal.y + 90) < 1e-10):
        polesById1[cell._id1] = cell
    # identify neighbours in cartesian space
    for id2 in cells:
      cells[id2].initNeighbours([polesById1[n] if n in polesById1 else minBy(cellsById1[n], by=lambda cellNeighbour: Cartesian.distance(cells[id2]._centreOriginal, cellNeighbour._centreOriginal)) for n in cells[id2]._neighbours])
    # identify cells to keep
    bbox = shapely.geometry.box(-180, -90 - 1e-10, 180, 90 + 1e-10)
    shapely.prepare(bbox)
    keepId2s = []
    for cell in cells.values():
      if bbox.contains(cell._centreOriginal) and cell._neighbours is not None:
        cell._isActive = True
        keepId2s.append(cell._id2)
        keepId2s += cell._neighbours
    # remove cells not to keep
    removeId2s = [id2 for id2 in cells if id2 not in keepId2s]
    for id2 in removeId2s:
      del cells[id2]
    # return result
    return {
      '__gridStats': gridStats,
      '__cells': cells,
    }

  @staticmethod
  def createBallTree(dataCells):
    cells = dataCells['__cells']
    cellsById1 = {}
    for cell in cells.values():
      if cell._id1 not in cellsById1:
        cellsById1[cell._id1] = []
      cellsById1[cell._id1].append(cell._id2)
    ballTreeCells = [cell for cell in cells.values() if cell._id1 == cell._id2]
    ballTreeCellsId1s = [cellsById1[cell._id1] for cell in ballTreeCells]
    ballTree = BallTree([(np.deg2rad(cell._centreOriginal.y), np.deg2rad(cell._centreOriginal.x)) for cell in ballTreeCells], metric='haversine')
    return {
      '__ballTree': ballTree,
      '__ballTreeCellsId1s': ballTreeCellsId1s,
    }

  def calibrate(self, callbackStatus):
    energy = 0
    for potential in self.__settings.potentials:
      if potential.calibrationPossible:
        callbackStatus(f"calibrating {potential.kind.lower()} ...", None)
        def computeEnergy(k):
          potential.setCalibrationFactor(abs(k))
          return self.energy(potential=potential)
        result = minimize_scalar(computeEnergy, method='brent', bracket=[.5, 1.5])
        potential.setCalibrationFactor(abs(result.x))
        energy += result.fun
      else:
        energy += self.energy(potential=potential)
    statusPotentials = []
    for potential in self.__settings.potentials:
      if potential.calibrationPossible:
        statusPotentials.append(f"k_{potential.kind.lower()} = {potential.calibrationFactor:.2f}")
    callbackStatus(f"calibrated: {', '.join(statusPotentials)}", energy)

  def energy(self, potential=None):
    with timer('compute energy', log=potential is None, step=self.__step):
      energy = 0
      for potential in [potential] if potential is not None else self.__settings.potentials:
        for cell in self.__cells.values():
          if cell._isActive:
            energy += potential.energy(cell, [self.__cells[n] for n in cell._neighbours if n in self.__cells])
      return energy

  def step(self):
    return self.__step

  def performStep(self, _onlyComputeNextForces=False):
    # increase step
    if not _onlyComputeNextForces:
      self.__step += 1
    # apply forces
    if not _onlyComputeNextForces:
      with timer('apply forces', step=self.__step):
        for cell in self.__cells.values():
          cell.applyForce()
    # compute forces
    forces = []
    for potential in self.__settings.potentials:
      with timer(f"compute forces: {potential.kind.lower()}", step=self.__step):
        for cell in self.__cells.values():
          if cell._isActive:
            forces += potential.force(cell, [self.__cells[n] for n in cell._neighbours if n in self.__cells])
    # collect forces
    with timer('collect forces', step=self.__step):
      for force in forces:
        self.__cells[force.id2].addForce(force)

  def project(self, lon, lat):
    pointLonLat = Point(lon, lat)
    dist, ind = self.__ballTree.query([np.deg2rad([lat, lon])], k=3)
    nearestCell = None
    cornerCells = None
    for id2s in [self.__ballTreeCellsId1s[i] for i in ind[0]]:
      nearestCell = minBy([self.__cells[id2] for id2 in id2s], by=lambda cell: Cartesian.distance(pointLonLat, cell._centreOriginal))
      cornerCells = nearestCell.neighboursWithEnclosingBearing(self.__cells, pointLonLat)
      if cornerCells is not None:
        break
    if nearestCell is None or cornerCells is None:
      raise Exception('No nearest cell found')
    cornerCells = [nearestCell, *cornerCells]
    cs = GeoGrid.__toBarycentricCoordinatesSpherical([cell._centreOriginal for cell in cornerCells], pointLonLat)
    return GeoGrid.__fromBarycentricCoordinates([cell.point() for cell in cornerCells], cs)

  @staticmethod
  def __toBarycentricCoordinatesSpherical(triangle, point):
    coordinates = [Geo.areaOfTriangle([p if i != n else point for i, p in enumerate(triangle)]) for n in range(0, 3)]
    s = sum(coordinates)
    return [c / s for c in coordinates]

  @staticmethod
  def __fromBarycentricCoordinates(triangle, coordinates):
    return sum([coordinates[i] * triangle[i].x for i in range(0, 3)]), sum([coordinates[i] * triangle[i].y for i in range(0, 3)])

  def getImage(self, viewSettings={}, width=2000, height=1000, border=10, d=6, boundsExtend=1.3, save=False):
    if viewSettings['drawContinentsTolerance']:
      NaturalEarth.preparedData()
    with timer('render', step=self.__step):
      # view settings
      viewSettings = {
        'selectedPotential': 'ALL',
        'selectedVisualizationMethod': 'SUM',
        'drawNeighbours': True,
        'drawLabels': False,
        'drawOriginalPolygons': False,
        'drawContinentsTolerance': False,
        'showNthStep': 10,
        **viewSettings,
      }
      # compute
      width -= 2 * border
      height -= 2 * border
      xMin = -math.pi * radiusEarth * boundsExtend
      xMax = -xMin
      yMin = -math.pi / 2 * radiusEarth * boundsExtend
      yMax = -yMin
      w = min(width, (xMax - xMin) / (yMax - yMin) * height)
      h = min(height, (yMax - yMin) / (xMax - xMin) * width)
      dx2 = border + (width - w) / 2
      dy2 = border + (height - h) / 2
      s = w / (xMax - xMin)
      project = lambda x, y: (dx2 + s * (x - xMin), dy2 + s * (-y - yMin))
      k = math.pi / 180 * radiusEarth
      lonLatToCartesian = lambda cs: (k * c for c in cs)
      d2 = d / 2
      # create image
      im = Image.new('RGB', (width, height), (255, 255, 255))
      draw = ImageDraw.Draw(im)
      # draw continental borders
      if viewSettings['drawContinentsTolerance']:
        csExteriors, csInteriors = NaturalEarth.preparedData(viewSettings['drawContinentsTolerance'])
        for cs in csExteriors:
          draw.polygon([project(*self.project(*c)) for c in cs], fill=(230, 230, 230))
          # draw.polygon([project(*lonLatToCartesian(c)) for c in cs], outline=(0, 255, 0))
        for cs in csInteriors:
          draw.polygon([project(*self.project(*c)) for c in cs], fill=(255, 255, 255))
      # draw original polygons
      if viewSettings['drawOriginalPolygons']:
        for cell in self.__cells.values():
          draw.polygon([project(*lonLatToCartesian(c)) for c in cell._polygonOriginal.exterior.coords[:-1]], outline=(255, 100, 100))
      # draw neighbours
      if viewSettings['drawNeighbours']:
        for cell in self.__cells.values():
          if cell._neighbours is not None:
            for cell2Id2 in cell._neighbours:
              if cell2Id2 in self.__cells:
                draw.line((*project(*cell.xy()), *project(*self.__cells[cell2Id2].xy())), fill=(220, 220, 220))
      # draw forces
      if viewSettings['selectedPotential'] is not None:
        if viewSettings['selectedVisualizationMethod'] == 'SUM':
          for cell in self.__cells.values():
            p1, p2 = cell.forceVector(viewSettings['selectedPotential'])
            draw.line((*project(*p1), *project(*p2)), fill=(150, 150, 150))
        else:
          for cell in self.__cells.values():
            p1, p2s = cell.forceVectors(viewSettings['selectedPotential'])
            for p2 in p2s:
              draw.line((*project(*p1), *project(*p2)), fill=(150, 150, 150))
      # draw centres
      if viewSettings['drawLabels']:
        font = ImageFont.truetype('Helvetica', size=12)
      for cell in self.__cells.values():
        x, y = project(*cell.xy())
        draw.ellipse((x - d2, y - d2, x + d2, y + d2), fill=(255, 0, 0) if cell._isActive else (0, 0, 255))
        if viewSettings['drawLabels']:
          draw.text((x, y), str(cell._id2), font=font, fill=(0, 0, 0))
      # save
      if save:
        if not os.path.exists(self.__pathTmp):
          os.mkdir(self.__pathTmp)
        filename = os.path.join(self.__pathTmp, 'cells-{resolution}-{step}.png'.format(resolution=self.__settings.resolution, step=self.__step))
        if not os.path.exists(filename):
          im.save(filename, optimize=False, compress_level=1)
      # return image
      return im

  def data(self):
    return self.__cells
