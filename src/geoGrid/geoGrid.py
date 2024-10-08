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
from src.geometry.cartesian import Cartesian, Point
from src.geometry.dggrid import DGGRID
from src.geoGrid.geoGridCell import GeoGridCell
from src.geoGrid.geoGridProjection import GeoGridProjection
from src.geoGrid.geoGridProjectionTIN import GeoGridProjectionTIN
from src.geoGrid.geoGridRenderer import GeoGridRenderer

class GeoGrid:
  def __init__(self, settings, callbackStatus=lambda status, energy, calibration=None: None):
    # save settings
    self.__settings = settings
    self.__callbackStatus = callbackStatus
    # init
    self.__gridStats = None
    self.__cells = None
    self.__pathTmp = '_tmp'
    self.__step = 0
    self.__ballTree = None
    self.__ballTreeCellsId1s = None
    self.__projection = None
    # reset potentials
    for potential in self.__settings.potentials:
      potential.emptyCacheAll()
    # load data
    filename = 'cells-{resolution}.pickle.gzip'.format(resolution=self.__settings.resolution)
    if os.path.exists(filename):
      self.__callbackStatus('loading cells and indices from proxy file ...', None)
      with timer('load data from proxy file'):
        with gzip.open(filename, 'rb') as f:
          data = pickle.load(f)
    else:
      self.__callbackStatus('creating cells and indices, and save them to proxy file ...', None)
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
    # init the settings
    self.__settings.initWithGridStats(self.__gridStats)
    self.__settings.initWithGeoGrid(self)
    # project to initial crs
    if self.__settings.initialProjection and self.__settings.initialProjection.transform is not None:
      with timer('apply initial CRS'):
        for cell in self.__cells.values():
          cell.initTransform(self.__settings.initialProjection.transform, scale=self.__settings.initialProjection.scale)
    # calibrate
    if self.__settings.canBeOptimized() is None:
      with timer('calibrate'):
        self.calibrate()
    # compute next forces and energies
    self.computeEnergiesAndForces()

  def settings(self):
    return self.__settings

  def cells(self):
    return self.__cells

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
        polesById1[cell._id1] = cell, cell._centreOriginal.y > 0
    # identify neighbours in cartesian space
    for id2 in cells:
      cells[id2].initNeighbours([polesById1[n][0] if n in polesById1 else minBy(cellsById1[n], by=lambda cellNeighbour: Cartesian.distance(cells[id2]._centreOriginal, cellNeighbour._centreOriginal)) for n in cells[id2]._neighbours])
    # identify cells to keep
    bbox = shapely.geometry.box(-180, -90 - 1e-10, 180, 90 + 1e-10)
    shapely.prepare(bbox)
    keepId2s = []
    for cell in cells.values():
      if bbox.contains(cell._centreOriginal) and cell._neighbours is not None:
        cell._isActive = True
        keepId2s.append(cell._id2)
        keepId2s += cell._neighbours
    for cell in cells.values():
      if cell._isActive and all([cells[neighbour]._isActive for neighbour in cell._neighbours]):
        cell._selfAndAllNeighboursAreActive = True
    # remove cells not to keep
    removeId2s = [id2 for id2 in cells if id2 not in keepId2s]
    for id2 in removeId2s:
      del cells[id2]
    # init poles
    for cell, isNorth in polesById1.values():
      cell.initPole(isNorth, cells)
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

  def calibrate(self):
    energy = 0
    for (weight, potential) in self.__settings.weightedPotentials():
      if weight.isVanishing():
        continue
      if potential.calibrationPossible:
        self.__callbackStatus(f"calibrating {potential.kind.lower()} ...", None)
        def computeEnergy(k):
          potential.setCalibrationFactor(abs(k))
          _, outerEnergy = self.energy(kindOfPotential=potential.kind, weighted=True, calibration=True)
          return outerEnergy
        result = minimize_scalar(computeEnergy, method='brent', bracket=[.5, 1.5])
        potential.setCalibrationFactor(abs(result.x))
        energy += result.fun
      else:
        _, outerEnergy = self.energy(kindOfPotential=potential.kind, weighted=True, calibration=True)
        energy += outerEnergy
    statusPotentials = []
    for (weight, potential) in self.__settings.weightedPotentials():
      if weight.isVanishing():
        continue
      if potential.calibrationPossible:
        statusPotentials.append(f"k_{potential.kind.lower()} = {potential.calibrationFactor:.2f}")
    if len(statusPotentials) > 0:
      self.__callbackStatus(None, energy, calibration=f"calibrated: {', '.join(statusPotentials)}")

  def energy(self, kindOfPotential=None, weighted=False, calibration=False):
    with timer('compute energy', log=kindOfPotential is None, step=self.__step):
      innerEnergy = 0
      outerEnergy = 0
      if self.__step <= 0 or calibration:
        for (weight, potential) in self.__settings.weightedPotentials():
          if kindOfPotential is not None and potential.kind != kindOfPotential:
            continue
          if weight.isVanishing():
            continue
          for cell in self.__cells.values():
            if cell._isActive and cell.within(lat=self.__settings.limitLatForEnergy):
              energy = (weight.forCell(cell) if weighted else 1) * potential.energy(cell, [self.__cells[n] for n in cell._neighbours if n in self.__cells])
              if cell._selfAndAllNeighboursAreActive:
                innerEnergy += energy
              outerEnergy += energy
      else:
        for cell in self.__cells.values():
          if cell._isActive and cell.within(lat=self.__settings.limitLatForEnergy):
            energy = cell.energy(kindOfPotential if kindOfPotential else 'ALL', weighted=weighted)
            if cell._selfAndAllNeighboursAreActive:
              innerEnergy += energy
            outerEnergy += energy
      return innerEnergy, outerEnergy

  def maxForceStrength(self):
    with timer('compute maximum force strength', step=self.__step):
      forceStrength = 0
      for cell in self.__cells.values():
        if cell._isActive:
          forceStrength = max(forceStrength, Cartesian.length(*cell.computeForcesNext()))
    return forceStrength

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
          cell.applyForces()
    # reset potentials
    for potential in self.__settings.potentials:
      potential.emptyCacheForStep()
    # find deficiencies and correct them
    # self.correctDeficiencies()
    # calibrate
    self.calibrate()
    # compute next forces and energies
    self.computeEnergiesAndForces()

  def findDeficiencies(self, computeAlmostDeficiencies=True):
    deficiencies, almostDeficiencies = [], []
    with timer(f"find deficiencies", step=self.__step):
      for cell in self.__cells.values():
        if not cell._isActive:
          continue
        for i, j in cell.getNeighbourTriangles():
          area = Cartesian.orientedArea(cell, self.__cells[i], self.__cells[j])
          # deficiency: orientation swapped or area vanishes
          if area <= 0:
            deficiencies.append((cell, self.__cells[i], self.__cells[j]))
          # almost a deficiency: altitude of the triangle is shorter than 5 per cent of the typical distance
          elif computeAlmostDeficiencies and area / Cartesian.distance(self.__cells[i], self.__cells[j]) <= self.__settings._almostDeficiencyRatioOfTypicalDistance * self.__settings._typicalDistance:
            almostDeficiencies.append((cell, self.__cells[i], self.__cells[j]))
    return deficiencies, almostDeficiencies if computeAlmostDeficiencies else None

  def correctDeficiencies(self):
    deficiencies, almostDeficiencies = self.findDeficiencies()
    with timer(f"correct deficiencies", step=self.__step):
      def _correctDeficiencies(ds, almostAltitude):
        coordinatesForCell = {}
        for cell0, cell1, cell2 in ds:
          x, y = cell0.xy()
          xForce, yForce = cell0.computeForcesNext()
          xBefore, yBefore = x - xForce, y - yForce
          altitude = Cartesian.orientedAltitude(cell0, cell1, cell2)
          altitudeBefore = Cartesian.orientedAltitude(Point(xBefore, yBefore), cell1, cell2)
          factor = max(0, min(1, (altitudeBefore - almostAltitude) / (altitudeBefore - altitude)))
          saveFactor = True
          if cell0._id2 in coordinatesForCell:
            factorOld, _ = coordinatesForCell[cell0._id2]
            saveFactor = factorOld < factor
          if saveFactor:
            coordinatesForCell[cell0._id2] = factor, (xBefore + factor * xForce, yBefore + factor * yForce)
        for id2, (_, coordinates) in coordinatesForCell.items():
          self.__cells[id2].x, self.__cells[id2].y = coordinates
      # _correctDeficiencies(deficiencies, 0)
      _correctDeficiencies(deficiencies + almostDeficiencies, self.__settings._almostDeficiencyRatioOfTypicalDistance * self.__settings._typicalDistance)

  def computeEnergiesAndForces(self):
    # reset forces
    for cell in self.__cells.values():
      cell.resetForcesNext()
    # compute energies and forces
    for (weight, potential) in self.__settings.weightedPotentials():
      with timer(f"compute energies and forces: {potential.kind.lower()}", step=self.__step):
        for cell in self.__cells.values():
          # only continue if weight is not vanishing
          if weight.isVanishing():
            cell.setEnergy(potential.kind, 0)
            cell.setEnergyWeight(potential.kind, 0)
            continue
          # weight
          w = weight.forCell(cell)
          # compute
          energy, forces = potential.energyAndForces(cell, [self.__cells[n] for n in cell._neighbours if n in self.__cells])
          # handle energies
          cell.setEnergy(potential.kind, energy)
          cell.setEnergyWeight(potential.kind, w)
          # handle forces
          for force in forces:
            force.scaleStrength(w if force.withoutDamping else (1 - self.__settings._dampingFactor) * w)
            self.__cells[force.id2From].addForce(force)

  def serializedDataForProjection(self):
    with timer('serialize data for projection', step=self.__step):
      return GeoGridProjection.serializedDataForProjection(self.__cells)

  def projection(self):
    if self.__projection is None:
      self.__projection = GeoGridProjection(self.__ballTree, self.__ballTreeCellsId1s, self.serializedDataForProjection())
    return self.__projection

  def project(self, lon, lat):
    return self.projection().project(lon, lat)

  def exportProjectionTIN(self, info):
    return GeoGridProjectionTIN.computeTIN(self, info)

  def serializedData(self, viewSettings={}):
    with timer('serialize data for rendering', step=self.__step):
      # view settings
      viewSettings = {
        **GeoGridRenderer.viewSettingsDefault,
        **viewSettings,
      }
      # init data
      cells = dict((cell._id2, {}) for cell in self.__cells.values())
      # initial polygon coords
      if viewSettings['drawInitialPolygons']:
        for cell in self.__cells.values():
          cells[cell._id2]['polygonInitialCoords'] = cell._polygonOriginal.exterior.coords[:-1]
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
            cells[cell._id2]['energy'] = cell.energy(viewSettings['selectedEnergy'], weighted=True)
      # centres xy and is active
      for cell in self.__cells.values():
        cells[cell._id2]['xy'] = cell.xy()
        cells[cell._id2]['isActive'] = cell._isActive
        cells[cell._id2]['distanceToLand'] = cell._distanceToLand
      # return
      return {
        'cells': cells,
        'path': self.__pathTmp,
        'resolution': self.__settings.resolution,
        'step': self.__step,
      }
