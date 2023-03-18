from collections import OrderedDict
from dggrid4py import DGGRIDv7
import geopandas as gpd
import gzip
import matplotlib
# matplotlib.use('agg')
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
import pickle
from PIL import Image, ImageDraw
import pyproj
from scipy.optimize import minimize_scalar
from scipy.spatial import KDTree
import shapely
import shutil
from sklearn.neighbors import BallTree
import warnings

from src.common import *
from src.geo import *
from src.timer import *
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
    dggrid = DGGRIDv7(executable='DGGRID/build/src/apps/dggrid/dggrid', working_dir='.', capture_logs=False, silent=True)
    # get grid stats
    gridStats = dggrid.grid_stats_table('ISEA3H', resolution=resolution)
    # get grid cells
    df = dggrid.grid_cellids_for_extent(dggs_type='ISEA3H', resolution=resolution)
    df.columns = ['id', 'longitude', 'latitude']
    # create polygons to identify neighbours
    positions = [
      {'dLon': -360, 'dLat': -180, 'rotate': True}, {'dLat': -180, 'rotate': True}, {'dLon': 360, 'dLat': -180, 'rotate': True},
      {'dLon': -360,}, {'dLon': 360},
      {'dLon': -360, 'dLat': 180, 'rotate': True}, {'dLat': 180, 'rotate': True}, {'dLon': 360, 'dLat': 180, 'rotate': True},
    ]
    df2 = dggrid.grid_cell_polygons_for_extent(dggs_type='ISEA3H', resolution=resolution).set_crs('EPSG:4326').rename(columns={'name': 'id'})
    lonMin, latMin, lonMax, latMax = df2.total_bounds
    delta = 0
    for g in df2.geometry:
      lonMin2, latMin2, lonMax2, latMax2 = g.bounds
      if np.abs(latMin2 - latMin) < 1e-6 and lonMin2 < 0 and lonMax2 > 0:
        delta = lonMax2 + lonMin2
        break
    def polygonsShifted2(dLon=None, dLat=None, rotate=False):
      def alignCellPolygon(g):
        cs = []
        lon1 = None
        lat1 = None
        for lon, lat in list(g.exterior.coords):
          if rotate:
            lon = -lon + 180 + delta
            lat = -lat
          if lon1 is None and lat1 is None:
            lon1 = lon
            lat1 = lat
          if np.abs(lat - latMin) < 1e-6:
            lat = -90
          if np.abs(lat - latMax) < 1e-6:
            lat = 90
          if np.abs(lon1 - lon) >= 160:
            lon += np.sign(lon1 - lon) * 360
          if np.abs(lat1 - lat) >= 80:
            lat += np.sign(lat1 - lat) * 180
          cs.append((lon + (dLon if dLon else 0), lat + (dLat if dLat else 0)))
        return shapely.Polygon(cs)
      ps = df2.copy()
      ps.geometry = ps.geometry.map(alignCellPolygon)
      return ps
    polygons = pd.concat([polygonsShifted2(), *[polygonsShifted2(**kwargs) for kwargs in positions]])
    # extract centres, duplicate them, and assemble them
    def centresShifted(dLon=None, dLat=None, rotate=False):
      cs = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy((-1 if rotate else 1) * df.longitude + (180 + delta if rotate else 0) + (dLon if dLon else 0), (-1 if rotate else 1) * df.latitude + (dLat if dLat else 0))).drop(columns=['longitude', 'latitude']).set_crs('EPSG:4326')
      cs['original'] = dLon is None and dLat is None
      return cs
    centres = pd.concat([centresShifted(), *[centresShifted(**kwargs) for kwargs in positions]])
    centres['id2'] = [str(i) for i in range(1, len(centres) + 1)]
    # add id2's to polygons
    polygons['id2'] = polygons.sjoin(centres, how='left', predicate='contains').id2
    # identify neighbours
    bbox = shapely.geometry.box(-180, -90, 180, 90)
    grid2GeometryBuffer = polygons.geometry.buffer(1e-5)
    polygons['neighbours'] = polygons.apply(lambda cell: set([id2 for id2 in polygons[~grid2GeometryBuffer.disjoint(cell.geometry.buffer(1e-6))].id2.tolist() if cell.id2 != id2]), axis='columns')
    polygons['keep'] = polygons.intersects(bbox)
    # merge
    centres = centres.merge(polygons, how='left', on='id2', suffixes=('', '_polygons')).drop(columns=['id_polygons'])
    id2sWithin = centres[centres.within(bbox)].id2.tolist()
    centres['keep'] = centres.keep | centres.neighbours.apply(lambda ns: False if pd.isna(ns) else any(n in id2sWithin for n in ns))
    # filter
    centres = centres[centres.keep == True]
    keepId2s = centres.id2.tolist()
    polygons = polygons[polygons.id2.isin(keepId2s)]
    # add id2 as index
    centres.index = centres.id2.rename('_id2')
    # add geometry_initial column
    centres['geometry_initial'] = centres.geometry
    # create cells
    cells = OrderedDict([(cell._id2, cell) for cell in centres.apply(lambda cell: GeoGridCell(cell), axis='columns').tolist()])
    # sort neighbours
    for cell in cells.values():
      ns = []
      neighbours = list(cell._neighbours)
      while len(ns) < len(neighbours):
        if len(ns) == 0:
          ns.append(neighbours[0])
          continue
        if ns[-1] in cells:
          nsNew = [n for n in cells[ns[-1]]._neighbours if n in neighbours and n not in ns]
          if len(nsNew) > 0:
            ns.append(nsNew[0])
            continue
        ns.append([n for n in neighbours if n not in ns][0])
      cell._neighbours = ns
    # mark cells as active if all neighours are present
    for cell in cells.values():
      cell._isActive = all([n in cells for n in cell._neighbours])
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
      for cell in self.__cells.values():
        x, y = project(*cell.xy())
        draw.ellipse((x - d2, y - d2, x + d2, y + d2), fill=(255, 0, 0) if cell._isActive else (0, 0, 255))
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

  # @staticmethod
  # def plot(centres, polygons):
  #   # usage: self.plot(centres, polygons)
  #   # crs = pyproj.CRS('EPSG:3395') # world mercator
  #   # crs = pyproj.CRS('ESRI:54009') # mollweide
  #   crs = pyproj.CRS('EPSG:4326') # WGS84
  #   # crs = pyproj.CRS('ESRI:102021') # WGS84 Stereographic South Pole
  #   centres = centres.to_crs(crs)
  #   polygons = polygons.to_crs(crs)
  #   ax = centres.plot(color=np.where(centres.keep == True, 'red', 'blue'), markersize=1)
  #   for x, y, id2, keep in zip(centres.geometry.x, centres.geometry.y, centres.id, centres.keep):
  #     plt.annotate(text=str(id2), xy=(x, y), horizontalalignment='center')
  #   polygons.boundary.plot(ax=ax)
  #   plt.axhline(y=90, color='red', linestyle='-')
  #   plt.axhline(y=-90, color='red', linestyle='-')
  #   plt.axvline(x=-180, color='red', linestyle='-')
  #   plt.axvline(x=180, color='red', linestyle='-')
  #   plt.show()
