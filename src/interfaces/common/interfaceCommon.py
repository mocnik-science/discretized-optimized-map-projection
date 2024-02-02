import json
import os
import random
import shutil

from src.common.video import renderVideo
from src.geometry.strategy import strategyForScale
from src.geoGrid.geoGridRenderer import GeoGridRenderer
from src.interfaces.common.common import APP_CAPTURE_PATH

class InterfaceCommon:
  @staticmethod
  def hash():
    return f'{random.randrange(0, 10**6):06d}'

  @staticmethod
  def isStopThresholdReached(geoGrid, geoGridSettings):
    # maxForceStrength is in units of the coordinate system in which the cells are located: radiusEarth * deg2rad(lon), radiusEarth * deg2rad(lat)
    # maxForceStrength is divided by the typical distance (which works perfectly at the equator) to normalize
    # The normalized maxForceStrength is divided by the speed (100 * (1 - dampingFactor)), in order to compensate for varying speeds
    stopThresholdReached = geoGrid.maxForceStrength() / (100 * (1 - geoGridSettings._dampingFactor)) < geoGridSettings._stopThreshold * geoGridSettings._typicalDistance
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
  def stepData(dataData, geoGridSettings, geoGrid=None, stepData=None):
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
      'resolution': str(settings['resolution']),
      'dampingFactor': str(settings['dampingFactor']),
      'stopThreshold': str(settings['stopThreshold']),
      'limitLatForEnergy': str(settings['limitLatForEnergy']),
      'weights': _jsonDumps(settings['weights']),
    }
    dataRow = f"{','.join(data.values())}\n"
    if not os.path.exists(fileNameTmp):
      os.makedirs(APP_CAPTURE_PATH, exist_ok=True)
      with open(fileNameTmp, 'w') as f:
        headerRow = f"{','.join(data.keys())}\n"
        f.write(headerRow)
        f.write(dataRow)
    elif stepData['step'] > 0:
      with open(fileNameTmp, 'a') as f:
        f.write(dataRow)

  @staticmethod
  def filename(geoGridSettings, *args, extension=None):
    return f"domp-{geoGridSettings.initialProjection.name.replace(' ', '_').replace('-', '_')}-{geoGridSettings.hash()}{'-' + '-'.join([str(arg) for arg in args]) if args else ''}{'.' + extension if extension else ''}"

  @staticmethod
  def saveData(pathFunction, dataData, geoGridSettings):
    fileNameTmp = os.path.join(APP_CAPTURE_PATH, dataData + '.csv')
    path = pathFunction('~/Downloads', InterfaceCommon.filename(geoGridSettings, dataData, extension='csv'))
    if path:
      path = os.path.expanduser(path)
      if os.path.exists(path):
        os.unlink(path)
      shutil.copy2(fileNameTmp, path)

  @staticmethod
  def saveScreenshot(pathFunction, geoGridSettings, viewSettings, geoGrid=None, serializedData=None, projection=None, stepData=None, largeSymbols=False):
    if geoGrid:
      serializedData = serializedData or geoGrid.serializedData(viewSettings)
      projection = projection or geoGrid.projection()
      stepData = stepData or InterfaceCommon.computeStepData(geoGrid, geoGridSettings)
    if serializedData is None or projection is None or stepData is None:
      raise Exception('Please provide either serializedData, projection, and stepData, or provide geogrid')
    path = pathFunction('~/Downloads', InterfaceCommon.filename(geoGridSettings, stepData['step'], InterfaceCommon.hash(), extension='png'))
    if path:
      path = os.path.expanduser(path)
      if os.path.exists(path):
        os.unlink(path)
      im = GeoGridRenderer.render(serializedData, geoGridSettings=geoGridSettings, viewSettings=viewSettings, projection=projection, size=(1920, 1080), transparency=True, largeSymbols=largeSymbols, stepData=stepData)
      im.save(path, optimize=True)

  @staticmethod
  def renderImage(geoGridSettings, viewSettings, geoGrid=None, serializedData=None, projection=None, stepData=None, size=None):
    if geoGrid:
      serializedData = serializedData or geoGrid.serializedData(viewSettings)
      projection = projection or geoGrid.projection()
      stepData = stepData or InterfaceCommon.computeStepData(geoGrid, geoGridSettings)
    if serializedData is None or projection is None: # or stepData is None:
      print(serializedData is None, projection is None, stepData is None)
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
    path = pathFunction('~/Downloads', InterfaceCommon.filename(geoGridSettings, videoData, extension='mp4'))
    if path:
      path = os.path.expanduser(path)
      if os.path.exists(path):
        os.unlink(path)
      os.replace(fileNameTmp + '.mp4', path)

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
