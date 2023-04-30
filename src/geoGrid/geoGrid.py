import gzip
import os
import pickle
from scipy.optimize import minimize_scalar
import shapely
import shutil
from sklearn.neighbors import BallTree

from src.common.functions import minBy
from src.common.timer import timer
from src.geometry.common import Common
from src.geometry.cartesian import Cartesian
from src.geometry.dggrid import DGGRID
from src.geoGrid.geoGridCell import GeoGridCell
from src.geoGrid.geoGridProjection import GeoGridProjection
from src.geoGrid.geoGridRenderer import GeoGridRenderer
from src.geoGrid.geoGridWeight import GeoGridWeight

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
    self.__projection = None
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
    # init additional information
    for cell in cells.values():
      cell.initAdditionalInformation()
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
    ballTree = BallTree([(Common.deg2rad(cell._centreOriginal.y), Common.deg2rad(cell._centreOriginal.x)) for cell in ballTreeCells], metric='haversine')
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
      if self.__step <= 0:
        for (weight, potential) in [(GeoGridWeight(), potential)] if potential is not None else self.__settings.weightedPotentials():
          for cell in self.__cells.values():
            if cell._isActive:
              energy += weight.forCell(cell) * potential.energy(cell, [self.__cells[n] for n in cell._neighbours if n in self.__cells])
      else:
        for cell in self.__cells.values():
          if cell._isActive:
            energy += cell.energy(potential if potential else 'ALL')
      return energy

  def step(self):
    return self.__step

  def performStep(self, _onlyComputeNextForces=False):
    # reset projection
    self.__projection = None
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
    for (weight, potential) in self.__settings.weightedPotentials():
      with timer(f"compute forces: {potential.kind.lower()}", step=self.__step):
        for cell in self.__cells.values():
          if cell._isActive:
            for force in potential.forces(cell, [self.__cells[n] for n in cell._neighbours if n in self.__cells]):
              force.strength *= weight.forCell(cell)
              forces.append(force)
    # collect forces
    with timer('collect forces', step=self.__step):
      for force in forces:
        self.__cells[force.id2].addForce(force)
    # compute energies
    for (weight, potential) in self.__settings.weightedPotentials():
      with timer(f"compute energies: {potential.kind.lower()}", step=self.__step):
        for cell in self.__cells.values():
          if cell._isActive:
            cell.setEnergy(potential.kind, weight.forCell(cell) * potential.energy(cell, [self.__cells[n] for n in cell._neighbours if n in self.__cells]))

  def serializedDataForProjection(self):
    with timer('serialize data for projection', step=self.__step):
      return GeoGridProjection.serializedDataForProjection(self.__cells)

  def projection(self):
    if self.__projection is None:
      self.__projection = GeoGridProjection(self.__ballTree, self.__ballTreeCellsId1s, self.serializedDataForProjection())
    return self.__projection

  def project(self, lon, lat):
    return self.projection().project(lon, lat)

  def serializedData(self, viewSettings={}):
    with timer('serialize data for rendering', step=self.__step):
      # view settings
      viewSettings = {
        **GeoGridRenderer.viewSettingsDefault,
        **viewSettings,
      }
      # init data
      cells = dict((cell._id2, {}) for cell in self.__cells.values())
      # original polygon coords
      if viewSettings['drawOriginalPolygons']:
        for cell in self.__cells.values():
          cells[cell._id2]['polygonOriginalCoords'] = cell._polygonOriginal.exterior.coords[:-1]
      # neighbours xy
      if viewSettings['drawNeighbours']:
        for cell in self.__cells.values():
          if cell._neighbours is not None:
            cells[cell._id2]['neighboursXY'] = [self.__cells[cell2Id2].xy() for cell2Id2 in cell._neighbours if cell2Id2 in self.__cells]
      # force vectors
      if viewSettings['selectedPotential'] is not None:
        if viewSettings['selectedVisualizationMethod'] == 'SUM':
          for cell in self.__cells.values():
            cells[cell._id2]['forceVector'] = cell.forceVector(viewSettings['selectedPotential'])
        else:
          for cell in self.__cells.values():
            cells[cell._id2]['forceVectors'] = cell.forceVectors(viewSettings['selectedPotential'])
      # energy
      if viewSettings['selectedEnergy'] is not None:
        for cell in self.__cells.values():
          if cell._isActive:
            cells[cell._id2]['energy'] = cell.energy(viewSettings['selectedEnergy'])
      # centres xy and is active
      for cell in self.__cells.values():
        cells[cell._id2]['xy'] = cell.xy()
        cells[cell._id2]['isActive'] = cell._isActive
      # return
      return {
        'cells': cells,
        'path': self.__pathTmp,
        'resolution': self.__settings.resolution,
        'step': self.__step,
      }

  def render(self, viewSettings={}, **kwargs):
    serializedData = self.serializedData(viewSettings)
    return GeoGridRenderer.render(serializedData, projection=self.projection(), **kwargs)

  def data(self):
    return self.__cells
