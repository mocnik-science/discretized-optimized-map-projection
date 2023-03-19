from collections import OrderedDict
import geopandas as gpd
import gzip
import numpy as np
import os
import pandas as pd
import pickle
from PIL import Image, ImageDraw, ImageFont
import pyproj
from scipy.optimize import minimize_scalar
from scipy.spatial import KDTree
import shapely
import shutil
from sklearn.neighbors import BallTree
import warnings

from src.common import *
from src.dggrid import DGGRID
from src.geo import *
from src.timer import timer
from src.geoGrid.geoGridCell import *

warnings.filterwarnings('ignore')

class GeoGrid:
  def __init__(self, settings, callbackStatus=lambda _: None):
    # save settings
    self.__settings = settings
    # init
    self.__gridStats = None
    self.__cells = None
    self.__pathTmp = '_tmp'
    self.__step = 0
    self.__bounds = None
    self.__ballTree = None
    # load data
    filename = 'cells-{resolution}.pickle.gzip'.format(resolution=self.__settings.resolution)
    if os.path.exists(filename):
      callbackStatus('loading cells from proxy file ...')
      with timer('load cells from proxy file'):
        with gzip.open(filename, 'rb') as f:
          data = pickle.load(f)
    else:
      callbackStatus('creating cells and save to proxy file ...')
      with timer('create cells and save to proxy file'):
        data = self.createCells(resolution=self.__settings.resolution)
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
    # identify neighbours in cartesian space
    for id2 in cells:
      cells[id2]._neighbours = [minBy(cellsById1[n], by=lambda cellNeighbour: cartesianDistance(cellNeighbour._centreOriginal, cells[id2]._centreOriginal))._id2 for n in cells[id2]._neighbours]
      if any(abs(cells[n]._centreOriginal.x - cells[id2]._centreOriginal.x) > 180 for n in cells[id2]._neighbours):
        cells[id2]._neighbours = None
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

  def calibrate(self, callbackStatus):
    callbackStatus('calibrating ...')
    def computeEnergy(k):
      for cell in self.__cells.values():
        cell.setCalibrationFactor(k)
      return self.energy()
    result = minimize_scalar(computeEnergy, method='brent')
    self._bounds = [result.x * -math.pi * radiusEarth, result.x * -math.pi / 2 * radiusEarth, result.x * math.pi * radiusEarth, result.x * math.pi / 2 * radiusEarth]
    callbackStatus(f"calibrated: k = {result.x}, energy = {result.fun}")

  def energy(self):
    energy = 0
    for potential in self.__settings.potentials:
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
    with timer('compute forces', step=self.__step):
      forces = []
      for potential in self.__settings.potentials:
        for cell in self.__cells.values():
          if cell._isActive:
            forces += potential.force(cell, [self.__cells[n] for n in cell._neighbours if n in self.__cells])
    # collect forces
    with timer('collect forces', step=self.__step):
      for force in forces:
        self.__cells[force.id2].addForce(force)

  def __getBallTree(self):
    if self.__ballTree is None:
      with timer('compute ball tree', step=self.__step):
        self.__ballTree = BallTree([np.deg2rad(cell.geometry.coords[0]) for cell in self.__cells.values()], metric='haversine')
    return self.__ballTree

  def project(self, lon, lat):
    dist, ind = self.__getBallTree().query(np.deg2rad([[lon, lat]]), k=3)
    cornerCells = [self.__cells[i] for i in ind[0]]
    cs = GeoGrid.__toBarycentricCoordinatesSpherical([cell.geometryCentre for cell in cornerCells], shapely.Point(lon, lat))
    p = GeoGrid.__fromBarycentricCoordinates([cell.point() for cell in cornerCells], cs)
    return p.coords[0]
  
  @staticmethod
  def __toBarycentricCoordinatesSpherical(triangle, point):
    coordinates = [geoAreaOfTriangle([p if i != n else point for i, p in enumerate(triangle)]) for n in range(0, 3)]
    s = sum(coordinates)
    return [c / s for c in coordinates]

  @staticmethod
  def __fromBarycentricCoordinates(triangle, coordinates):
    x = sum([coordinates[i] * triangle[i].x for i in range(0, 3)])
    y = sum([coordinates[i] * triangle[i].y for i in range(0, 3)])
    return shapely.Point(x, y)

  def getImage(self, viewSettings={}, width=2000, height=1000, border=10, d=6, boundsExtend=1.6, save=False):
    with timer('render', step=self.__step):
      # view settings
      viewSettings = {
        'drawNeighbours': True,
        'selectedPotential': 'ALL',
        'selectedVisualizationMethod': 'SUM',
        **viewSettings,
      }
      # compute
      width -= 2 * border
      height -= 2 * border
      xMin, yMin, xMax, yMax = self._bounds
      xMin *= boundsExtend
      xMax *= boundsExtend
      yMin *= boundsExtend
      yMax *= boundsExtend
      w = min(width, (xMax - xMin) / (yMax - yMin) * height)
      h = min(height, (yMax - yMin) / (xMax - xMin) * width)
      dx2 = border + (width - w) / 2
      dy2 = border + (height - h) / 2
      s = w / (xMax - xMin)
      project = lambda x, y: (dx2 + s * (x - xMin), dy2 + s * (y - yMin))
      d2 = d / 2
      # create image
      im = Image.new('RGB', (width, height), (255, 255, 255))
      draw = ImageDraw.Draw(im)
      # draw original polygons
      if viewSettings['drawOriginalPolygons']:
        for cell in self.__cells.values():
          draw.polygon([project(cell._k * x, cell._k * y) for x, y in cell._polygonOriginal.exterior.coords[:-1]], outline=(255, 100, 100))
      # draw neighbours
      if viewSettings['drawNeighbours']:
        for cell in self.__cells.values():
          for cell2Id2 in cell._neighbours:
            if cell2Id2 in self.__cells:
              draw.line((*project(*cell.xy()), *project(*self.__cells[cell2Id2].xy())), fill=(220, 220, 220))
      # draw forces
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
