import glob
import json
import os
import random
import shutil

from src.common.video import renderVideo
from src.geoGrid.geoGridRenderer import GeoGridRenderer
from src.interfaces.common.common import APP_CAPTURE_PATH
from src.interfaces.common.file import File

class InterfaceCommon:
  @staticmethod
  def hash():
    return f'{random.randrange(0, 10**6):06d}'

  @staticmethod
  def isStopThresholdReached(geoGrid, geoGridSettings, stepData=None):
    # maxForceStrength is in units of the coordinate system in which the cells are located: radiusEarth * deg2rad(lon), radiusEarth * deg2rad(lat)
    # maxForceStrength is divided by the typical distance (which works perfectly at the equator) to normalize
    # The normalized maxForceStrength is divided by the speed (100 * (1 - dampingFactor)), in order to compensate for varying speeds
    stopThresholdReached = geoGrid.maxForceStrength() / (100 * (1 - geoGridSettings._dampingFactor)) < geoGridSettings._stopThresholdMaxForceStrength * geoGridSettings._typicalDistance
    # count deficiencies
    deficiencies, _ = geoGrid.findDeficiencies(computeAlmostDeficiencies=False)
    stopThresholdReached = stopThresholdReached or (stepData['countDeficiencies'] if stepData else len(deficiencies)) >= geoGridSettings._stopThresholdCountDeficiencies
    # max steps
    stopThresholdReached = stopThresholdReached or geoGrid.step() >= geoGridSettings._stopThresholdMaxSteps
    if stopThresholdReached:
      geoGridSettings.setThresholdReached()
    return stopThresholdReached

  @staticmethod
  def computeStepData(geoGrid, geoGridSettings):
    # compute energy
    energy, energyWeighted = geoGrid.energy(weighted=False), geoGrid.energy(weighted=True)
    energyPerPotential = {}
    for potential in geoGridSettings.potentials:
      energyPerPotential[potential.kind] = geoGrid.energy(kindOfPotential=potential.kind, weighted=False)
    energyWeightedPerPotential = {}
    for potential in geoGridSettings.potentials:
      energyWeightedPerPotential[potential.kind] = geoGrid.energy(kindOfPotential=potential.kind, weighted=True)
    # compute deficiencies
    deficiencies, almostDeficiencies = geoGrid.findDeficiencies()
    countDeficiencies, countAlmostDeficiencies = len(deficiencies), len(almostDeficiencies)
    return {
      'step': geoGrid.step(),
      'energy': energy,
      'energyWeighted': energyWeighted,
      'energyPerPotential': energyPerPotential,
      'energyWeightedPerPotential': energyWeightedPerPotential,
      'countDeficiencies': countDeficiencies,
      'countAlmostDeficiencies': countAlmostDeficiencies,
    }

  @staticmethod
  def startData():
    return InterfaceCommon.hash()

  @staticmethod
  def stepData(dataData, geoGridSettings, geoGrid=None, stepData=None, additionalData=None, appendOnlyIf=True):
    stepData = stepData or InterfaceCommon.computeStepData(geoGrid, geoGridSettings)
    if stepData is None:
      raise Exception('Please provide either stepData or geogrid')
    _jsonDumps = lambda x: '"' + json.dumps(x).replace('"', '""') + '"'
    fileNameTmp = os.path.join(APP_CAPTURE_PATH, dataData + '.csv')
    innerEnergy, outerEnergy = stepData['energy']
    innerEnergyWeighted, outerEnergyWeighted = stepData['energyWeighted']
    settings = geoGridSettings.toJSON()
    info = geoGridSettings.info()
    data = {
      'step': str(stepData['step']),
      'countDeficiencies': str(stepData['countDeficiencies']),
      'countAlmostDeficiencies': str(stepData['countDeficiencies'] + stepData['countAlmostDeficiencies']),
      'innerEnergy': f"{innerEnergy:.0f}",
      'outerEnergy': f"{outerEnergy:.0f}",
      'innerEnergyWeighted': f"{innerEnergyWeighted:.0f}",
      'outerEnergyWeighted': f"{outerEnergyWeighted:.0f}",
    }
    for (key, value), (keyWeighted, valueWeighted) in zip(stepData['energyPerPotential'].items(), stepData['energyWeightedPerPotential'].items()):
      innerEnergy, outerEnergy = value
      innerEnergyWeighted, outerEnergyWeighted = valueWeighted
      data = {
        **data,
        'innerEnergy_' + key: f"{innerEnergy:.0f}",
        'outerEnergy_' + key: f"{outerEnergy:.0f}",
        'innerEnergyWeighted_' + keyWeighted: f"{innerEnergyWeighted:.0f}",
        'outerEnergyWeighted_' + keyWeighted: f"{outerEnergyWeighted:.0f}",
      }
    data = {
      **data,
      'hash': info['hash'],
      'initialProjection': _jsonDumps(settings['initialProjection']),
      'initialProjectionName': settings['initialProjection']['name'],
      'resolution': str(settings['resolution']),
      'dampingFactor': str(settings['dampingFactor']),
      'stopThresholdMaxForceStrength': str(settings['stopThresholdMaxForceStrength']),
      'stopThresholdCountDeficiencies': str(settings['stopThresholdCountDeficiencies']),
      'stopThresholdMaxSteps': str(settings['stopThresholdMaxSteps']),
      'limitLatForEnergy': str(settings['limitLatForEnergy']),
      'weights': _jsonDumps(settings['weights']),
      **(additionalData if additionalData is not None else {}),
    }
    dataRow = f"{','.join(data.values())}\n"
    if not os.path.exists(fileNameTmp):
      os.makedirs(APP_CAPTURE_PATH, exist_ok=True)
      with open(fileNameTmp, 'w') as f:
        headerRow = f"{','.join(data.keys())}\n"
        f.write(headerRow)
        f.write(dataRow)
    elif appendOnlyIf:
      with open(fileNameTmp, 'a') as f:
        f.write(dataRow)

  @staticmethod
  def saveData(pathFunction, dataData, geoGridSettings):
    fileNameTmp = os.path.join(APP_CAPTURE_PATH, dataData + '.csv')
    File(dataData, geoGridSettings=geoGridSettings, extension='csv').apply(pathFunction).byTmpFile(fileNameTmp)

  @staticmethod
  def saveScreenshot(pathFunction, geoGridSettings, viewSettings, geoGrid=None, serializedData=None, projection=None, stepData=None, largeSymbols=False, extension='png'):
    if geoGrid:
      serializedData = serializedData or geoGrid.serializedData(viewSettings)
      projection = projection or geoGrid.projection()
      stepData = stepData or InterfaceCommon.computeStepData(geoGrid, geoGridSettings)
    if serializedData is None or projection is None or stepData is None:
      raise Exception('Please provide either serializedData, projection, and stepData, or provide geogrid')
    file = File(stepData['step'], geoGridSettings=geoGridSettings, extension=extension, addHash=InterfaceCommon.hash()).apply(pathFunction)
    if not file.isCancelled():
      file.removeExisting()
      im = GeoGridRenderer.render(serializedData, geoGridSettings=geoGridSettings, viewSettings=viewSettings, projection=projection, size=(1920, 1080), transparency=True, largeSymbols=largeSymbols, stepData=stepData)
      im.save(file.pathAndFilename(), optimize=True)

  @staticmethod
  def renderImage(geoGridSettings, viewSettings, geoGrid=None, serializedData=None, projection=None, stepData=None, size=None):
    if geoGrid:
      serializedData = serializedData or geoGrid.serializedData(viewSettings)
      projection = projection or geoGrid.projection()
      stepData = stepData or InterfaceCommon.computeStepData(geoGrid, geoGridSettings)
    if serializedData is None or projection is None:
      raise Exception('Please provide either serializedData, projection, and stepData, or provide geogrid')
    return GeoGridRenderer.render(serializedData, geoGridSettings=geoGridSettings, viewSettings=viewSettings, projection=projection, size=size if size else (1920, 1080), stepData=stepData), stepData

  @staticmethod
  def startVideo():
    return InterfaceCommon.hash()

  @staticmethod
  def stepVideo(im, videoData, stepData):
    GeoGridRenderer.save(im, hash=videoData, step=stepData['step'])

  @staticmethod
  def saveVideo(pathFunction, videoData, geoGridSettings):
    fileNameTmp = os.path.join(APP_CAPTURE_PATH, videoData)
    renderVideo(fileNameTmp, 20)
    File(videoData, geoGridSettings=geoGridSettings, extension='mp4').apply(pathFunction).byTmpFile(fileNameTmp + '.mp4', move=True)

  @staticmethod
  def collectData(pathFunction, pattern):
    lines = []
    for filename in glob.glob(os.path.expanduser(File._defaultPath) + '/' + pattern, recursive=True):
      with open(filename, 'r') as f:
        linesNew = f.readlines()
        if len(lines) == 0:
          lines = linesNew
        elif lines[0] == linesNew[0]:
          lines += linesNew[1:]
        else:
          raise Exception('Error when collecting: different header')
    with open(File(extension='csv').apply(pathFunction).pathAndFilename(), 'w') as f:
      f.writelines(lines)

  @staticmethod
  def cleanup():
    try:
      with os.scandir(APP_CAPTURE_PATH) as entries:
        for entry in entries:
          if entry.is_file():
            os.unlink(entry.path)
          else:
            shutil.rmtree(entry.path)
    except OSError:
      raise Exception('Error when cleaning up')
