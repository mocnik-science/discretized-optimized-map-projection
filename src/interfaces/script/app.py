import os
import py
import sys

from src.common.console import Console
from src.geoGrid.geoGrid import GeoGrid
from src.geoGrid.geoGridSettings import GeoGridSettings
from src.geoGrid.geoGridWeight import GeoGridWeight
from src.interfaces.common.common import APP_NAME, APP_COPYRIGHT, APP_FILES_PATH
from src.interfaces.common.interfaceCommon import InterfaceCommon
from src.interfaces.common.projections import PROJECTION, Projection
from src.mechanics.potential.potentials import potentials

Print = Console.print

class POTENTIAL:
  pass

for potential in potentials:
  setattr(POTENTIAL, potential.kind, potential.kind)

# TODO show projections installed
# TODO save and install projection for QGIS
# TODO save projection for QGIS
# TODO load and save simulation settings

class DOMP:
  def __init__(self):
    # self.__appSettings = shelve.Shelf({})
    self.__geoGridSettings = GeoGridSettings()
    self.__viewSettings = {
      'captureVideo': False,
    }
    # init paths
    os.makedirs(APP_FILES_PATH, exist_ok=True)
    # variables
    self.__dataDataDict = {}
    self.__videoDatas = []
    # settings
    self.viewForces(all=True)
    self.viewEnergy()
    self.viewNeighbours()
    self.viewLabels()
    self.viewCentres(active=True)
    self.viewOriginalPolygons()
    self.viewContinents()
    # about
    self.about()
    # load the default projection
    self.loadProjection()

  def __callbackStatus(self, status, energy=None, calibration=None):
    Console.print(f"{'':<10} |", status, energy or '', calibration or '')
  
  ###### ABOUT

  def about(self):
    Console.print(APP_NAME)
    Console.print(APP_COPYRIGHT)
    Console.print()

  ###### VIEW SETTINGS

  def viewForces(self, all=False, potential=None, sum=True):
    self.__viewSettings['selectedPotential'] = 'ALL' if all else potential if potential else None
    self.__viewSettings['selectedVisualizationMethod'] = 'SUM' if sum else 'INDIVIDUALLY'
  def viewEnergy(self, all=False, potential=None):
    self.__viewSettings['selectedEnergy'] = 'ALL' if all else potential if potential else None
  def viewNeighbours(self, show=False):
    self.__viewSettings['drawNeighbours'] = show
  def viewLabels(self, show=False):
    self.__viewSettings['drawLabels'] = show
  def viewCentres(self, active=False, weightsForPotential=None):
    self.__viewSettings['drawCentres'] = 'ACTIVE' if active else weightsForPotential if weightsForPotential else None
  def viewOriginalPolygons(self, show=False):
    self.__viewSettings['drawOriginalPolygons'] = show
  def viewContinents(self, showStronglySimplified=False, showSimplified=False, show=False, showWithTolerance=None):
    self.__viewSettings['drawContinentsTolerance'] = 3 if showStronglySimplified else 1 if showSimplified else 'full' if show else showWithTolerance if showWithTolerance is not None else False

  ###### GEO GRID SETTINGS

  def settings(self, includeTransient=False):
    return self.__geoGridSettings.toJSON(includeTransient=includeTransient)

  def resolution(self, resolution=None):
    if resolution is not None:
      self.__geoGridSettings.updateResolution(resolution)
      self.__resetGeoGrid()
    return self.__geoGridSettings.resolution

  def dampingFactor(self, dampingFactor=None):
    if dampingFactor is not None:
      self.__geoGridSettings.updateDampingFactor(dampingFactor)
    return self.__geoGridSettings.dampingFactor
  def speed(self, speed=None):
    if speed is not None:
      self.__geoGridSettings.updateDampingFactor(1 - speed / 100)
    return 100 * (1 - self.__geoGridSettings._dampingFactor)

  def stopThreshold(self, maxForceStrength=None, countDeficiencies=None):
    if maxForceStrength is not None:
      self.__geoGridSettings.updateStopThresholdMaxForceStrength(maxForceStrength / 100)
    if countDeficiencies is not None:
      self.__geoGridSettings.updateStopThresholdCountDeficiencies(countDeficiencies)
    return 100 * self.__geoGridSettings._stopThresholdMaxForceStrength, self.__geoGridSettings._stopThresholdCountDeficiencies, 

  def limitLatForEnergy(self, limitLatForEnergy=None):
    if limitLatForEnergy is not None:
      self.__geoGridSettings.updateLimitLatForEnergy(limitLatForEnergy)
      self.__geoGrid.computeEnergiesAndForces()
    return self.__geoGridSettings.limitLatForEnergy

  def weights(self, potentialKind=None, active=None, weightLand=None, weightOceanActive=None, weightOcean=None, distanceTransitionStart=None, distanceTransitionEnd=None):
    if not potentialKind:
      if any(x is not None for x in [active, weightLand, weightOceanActive, weightOcean, distanceTransitionStart, distanceTransitionEnd]):
        raise Exception('Values can only be updated if the kind of the potential to update is provided')
      return '_'
    if not potentialKind in self.__geoGridSettings._potentialsWeights:
      raise Exception('Invalid kind of the potential')
    weight = self.__geoGridSettings._potentialsWeights[potentialKind]
    weightJSON = weight.toJSON()
    modified = False
    if active is not None:
      modified = True
      weightJSON['active'] = active
    if weightLand is not None:
      modified = True
      weightJSON['weightLand'] = weightLand
    if weightOceanActive is not None:
      modified = True
      weightJSON['weightOceanActive'] = weightOceanActive
    if weightOcean is not None:
      modified = True
      weightJSON['weightOcean'] = weightOcean
    if distanceTransitionStart is not None:
      modified = True
      weightJSON['distanceTransitionStart'] = distanceTransitionStart * 1000
    if distanceTransitionEnd is not None:
      modified = True
      weightJSON['distanceTransitionEnd'] = distanceTransitionEnd * 1000
    if modified:
      weight = GeoGridWeight(**weightJSON)
      self.__geoGridSettings.updatePotentialsWeights({potentialKind: weight})
      self.__geoGrid.computeEnergiesAndForces()
    weightJSON = weight.toJSON()
    weightJSON['distanceTransitionStart'] /= 1000
    weightJSON['distanceTransitionEnd'] /= 1000
    return weightJSON

  ###### LOADING PROJECTIONS

  def loadProjection(self, projection=PROJECTION.unprojected, name=None, srid=None, **kwargs):
    if srid is not None and name is not None:
      projection = Projection(name=name, srid=srid, **kwargs)
    elif srid is not None or name is not None:
      raise Exception('Provide both a name and an SRID')
    self.__geoGridSettings.initialProjection = projection
    self.__resetGeoGrid()
    self.__stepActions()

  def __resetGeoGrid(self):
    self.__geoGrid = GeoGrid(self.__geoGridSettings, callbackStatus=self.__callbackStatus)

  ###### RUN

  def __stepActions(self):
    self.__stepActionsData(self.__dataDataDict)
    self.__stepActionsVideo(self.__videoDatas)
  def __stepActionsData(self, dataDataDict={}):
    for dataData, dd in dataDataDict.items():
      InterfaceCommon.stepData(dataData, self.__geoGridSettings, geoGrid=self.__geoGrid, additionalData=dd['additionalData'] if dd is not None and 'additionalData' in dd else {})
  def __stepActionsVideo(self, videoDatas=None, videoData=None):
    if videoData and not videoDatas:
      videoDatas = [videoData]
    if len(videoDatas) == 0:
      return
    self.__viewSettings['captureVideo'] = True
    im, stepData = InterfaceCommon.renderImage(self.__geoGridSettings, self.__viewSettings, geoGrid=self.__geoGrid)
    self.__viewSettings['captureVideo'] = False
    for videoData in videoDatas:
      InterfaceCommon.stepVideo(im, videoData, stepData)

  def step(self):
    self.steps(n=1)
  def steps(self, n=None):
    def _step():
      self.__geoGrid.performStep()
      self.__stepActions()
    if n is None:
      while True:
        _step()
        if InterfaceCommon.isStopThresholdReached(self.__geoGrid, self.__geoGridSettings):
          break
    else:
      for _ in range(0, n):
        _step()

  ###### DATA

  def energy(self, inner=True, weighted=True):
    return self.__geoGrid.energy(weighted=weighted)[0 if inner else 1]
  def energyPerPotential(self, inner=True, weighted=True):
    return dict((potential.kind, self.__geoGrid.energy(kindOfPotential=potential.kind, weighted=weighted)[0 if inner else 1]) for potential in self.__geoGridSettings.potentials)

  def deficiencies(self):
    return self.__geoGrid.findDeficiencies()[0]
  def almostDeficiencies(self):
    return self.__geoGrid.findDeficiencies()[1]

  ###### SAVING DATA, SCREENSHOTS, AND VIDEOS

  @staticmethod
  def __fileFunction(**kwargs):
    return lambda file: file.update(**kwargs)

  def data(self, dataData=None, additionalData=None, **kwargs):
    self.saveData(self.startData(dataData=dataData, additionalData=additionalData), **kwargs)

  def appendData(self, dataData=None, additionalData=None, **kwargs):
    self.stopData(self.startData(dataData=dataData, additionalData=additionalData), **kwargs)

  def startData(self, dataData=None, additionalData=None, preventInitialSnapshot=False, preventSnapshots=False):
    dataData = dataData or InterfaceCommon.startData()
    if not preventSnapshots:
      self.__dataDataDict[dataData] = {'additionalData': additionalData}
    if not (preventSnapshots or preventInitialSnapshot):
      self.__stepActionsData(dataDataDict={dataData: self.__dataDataDict[dataData]})
    return dataData

  def stopData(self, dataData):
    if dataData in self.__dataDataDict:
      del self.__dataDataDict[dataData]

  def saveData(self, dataData, **kwargs):
    self.stopData(dataData)
    InterfaceCommon.saveData(DOMP.__fileFunction(**kwargs), dataData, self.__geoGridSettings)

  def screenshot(self, largeSymbols=False, **kwargs):
    InterfaceCommon.saveScreenshot(DOMP.__fileFunction(**kwargs), self.__geoGridSettings, self.__viewSettings, geoGrid=self.__geoGrid, largeSymbols=largeSymbols)

  def startVideo(self):
    videoData = InterfaceCommon.startVideo()
    self.__videoDatas.append(videoData)
    self.__stepActionsVideo(videoData=videoData)
    return videoData

  def saveVideo(self, videoData, **kwargs):
    self.__videoDatas = [vd for vd in self.__videoDatas if vd != videoData]
    InterfaceCommon.saveVideo(DOMP.__fileFunction(**kwargs), videoData, self.__geoGridSettings)

  ###### WITH

  def __trace(self, frame, event, arg):
    if event != 'line':
      return
    lineNumber = frame.f_lineno
    Console.status(f'\nline {lineNumber + 1:>5} |', self.__codeFulltext[lineNumber - 1].strip())

  def __enter__(self):
    sys.settrace(lambda *args, **kwargs: None)
    frame = sys._getframe(1)
    self.__codeFulltext = py.code.Frame(sys._getframe(1)).code.fullsource
    frame.f_trace = self.__trace
    return self

  def __exit__(self, exc_type, exc_value, traceback):
    self.__callbackStatus('cleanup')
    InterfaceCommon.cleanup()
    Console.clearStatus()
