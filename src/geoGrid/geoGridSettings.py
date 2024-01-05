import hashlib
import json

from src.app.common import APP_FILE_FORMAT
from src.geoGrid.geoGridWeight import GeoGridWeight
from src.mechanics.potential.potentials import potentials

# F = - G m1 m2 / r^2
# U = F * r
# E = m1 * U
#
# konservatives Kraftfeld
# F = - nabla U(r) = - del U / del x * e_x
# U = - \int F(r) dr

class GeoGridSettings:
  def __init__(self, resolution=3, dampingFactor=.98, stopThreshold=.001):
    self.resolution = resolution
    self._dampingFactor = dampingFactor
    self._stopThreshold = stopThreshold
    self._typicalDistance = None
    self._typicalArea = None
    self.potentials = [potential(self) for potential in potentials]
    self._potentialsWeights = dict([(potential.kind, potential.defaultWeight or GeoGridWeight()) for potential in self.potentials])
    self._updated(initial=True)

  def toJSON(self, includeTransient=False):
    transient = {}
    if includeTransient:
      transient = {
        'step': self._step,
        'untouched': self._untouched,
        'thresholdReached': self._thresholdReached,
        'energy': self._energy,
      }
    return {
      'fileFormat': APP_FILE_FORMAT,
      'fileFormatVersion': '1.0',
      'resolution': self.resolution,
      'dampingFactor': self._dampingFactor,
      'stopThreshold': self._stopThreshold,
      'weights': dict((potentialKind, weight.toJSON()) for (potentialKind, weight) in self._potentialsWeights.items()),
      **transient,
    }

  def info(self, includeTransient=False):
    settingsJson = self.toJSON(includeTransient=includeTransient)
    hash = hashlib.sha1(json.dumps(settingsJson).encode()).hexdigest()[:7]
    return {
      'jsonSettings': settingsJson,
      'hash': hash,
      'dompCRS': 'DOMP:' + hash,
      'filenameSettings': 'domp-' + hash + '-projection.domp',
      'filenameTIN': 'domp-' + hash + '-tin.json',
    }

  def _updated(self, initial=False):
    ## transient information
    if initial:
      self._untouched = True
      self._thresholdReached = False
      self._energy = None
      self._step = None
    elif self._step is not None:
      self._untouched = False
      self._thresholdReached = False
      self._energy = None
      self._step = None

  def updateFromJSON(self, data):
    self._updated()
    if data['fileFormat'] != APP_FILE_FORMAT or data['fileFormatVersion'] != '1.0':
      raise Exception('Wrong fileformat')
    self.updateResolution(data['resolution'])
    self.updateDampingFactor(data['dampingFactor'])
    self.updateStopThreshold(data['stopThreshold'])
    self.updatePotentialsWeights(dict((potentialKind, GeoGridWeight.fromJSON(weightData)) for (potentialKind, weightData) in data['weights'].items()))

  def updateResolution(self, resolution):
    self._updated()
    if self.resolution == resolution:
      return
    self.resolution = resolution
    for potential in self.potentials:
      potential.emptyCacheAll()

  def updateDampingFactor(self, dampingFactor):
    self._updated()
    self._dampingFactor = dampingFactor
    for potential in self.potentials:
      potential.emptyCacheDampingFactor()

  def updateStopThreshold(self, stopThreshold):
    self._updated()
    self._stopThreshold = stopThreshold

  def updateGridStats(self, gridStats):
    self._updated()
    self._typicalDistance = gridStats.typicalDistance()
    self._typicalArea = gridStats.typicalArea()

  def updatePotentialsWeights(self, weights):
    self._updated()
    self._potentialsWeights = dict(self._potentialsWeights, **weights)

  def weightedPotentials(self, allWeights=False):
    return [(self._potentialsWeights[potential.kind], potential) for potential in self.potentials if self._potentialsWeights[potential.kind] is not None and (allWeights or not self._potentialsWeights[potential.kind].isVanishing())]

  ## transient information

  def setUntouched(self):
    self._untouched = True

  def setThresholdReached(self):
    self._thresholdReached = True

  def updateTransient(self, energy=None, step=None):
    self._energy = energy if energy is not None else self._energy
    self._step = step if step is not None else self._step
