import hashlib
import json

from src.geoGrid.geoGridWeight import GeoGridWeight
from src.interfaces.common.common import APP_FILE_FORMAT
from src.interfaces.common.projections import PROJECTION, Projection
from src.mechanics.potential.potentials import potentials

# F = - G m1 m2 / r^2
# U = F * r
# E = m1 * U
#
# konservatives Kraftfeld
# F = - nabla U(r) = - del U / del x * e_x
# U = - \int F(r) dr

class GeoGridSettings:
  def __init__(self, initialProjection=PROJECTION.unprojected, resolution=3, dampingFactor=.96, stopThresholdMaxForceStrength=.001, stopThresholdCountDeficiencies=100, stopThresholdMaxSteps=5000, limitLatForEnergy=90):
    self.initialProjection = initialProjection
    self.resolution = resolution
    self._dampingFactor = dampingFactor
    self._stopThresholdMaxForceStrength = stopThresholdMaxForceStrength
    self._stopThresholdCountDeficiencies = stopThresholdCountDeficiencies
    self._stopThresholdMaxSteps = stopThresholdMaxSteps
    self.limitLatForEnergy = limitLatForEnergy
    self._typicalDistance = None
    self._typicalArea = None
    self._almostDeficiencyRatioOfTypicalDistance = .05 # a triangle is considered almost being an deficiency, if its height is smaller than the ratio of the typical distance provided here
    self.potentials = sorted([potential(self) for potential in potentials], key=lambda potential: potential.computationalOrder)
    self._potentialsWeights = dict([(potential.kind, potential.defaultWeight or GeoGridWeight()) for potential in self.potentials])
    self._updated(initial=True)

  def toJSON(self, includeTransient=False):
    transient = {}
    if includeTransient:
      transient = {
        'step': self._step,
        'untouched': self._untouched,
        'thresholdReached': self._thresholdReached,
        'innerEnergy': self._energy[0],
        'outerEnergy': self._energy[1],
      }
    return {
      'fileFormat': APP_FILE_FORMAT,
      'fileFormatVersion': '1.0',
      'initialProjection': self.initialProjection.toJSON(),
      'resolution': self.resolution,
      'dampingFactor': self._dampingFactor,
      'stopThresholdMaxForceStrength': self._stopThresholdMaxForceStrength,
      'stopThresholdCountDeficiencies': self._stopThresholdCountDeficiencies,
      'stopThresholdMaxSteps': self._stopThresholdMaxSteps,
      'limitLatForEnergy': self.limitLatForEnergy,
      'weights': dict((potentialKind, weight.toJSON()) for (potentialKind, weight) in self._potentialsWeights.items()),
      **transient,
    }

  def hash(self, includeTransient=False):
    return self.info(includeTransient=includeTransient)['hash']

  def info(self, includeTransient=False):
    settingsJson = self.toJSON(includeTransient=includeTransient)
    hash = hashlib.sha1(json.dumps(settingsJson).encode()).hexdigest()[:7]
    return {
      'jsonSettings': settingsJson,
      'hash': hash,
      'dompSRID': 'DOMP:' + hash,
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
    self.updateInitialProjection(Projection.fromJSON(data['initialProjection']))
    self.updateResolution(data['resolution'])
    self.updateDampingFactor(data['dampingFactor'])
    self.updateStopThresholdMaxForceStrength(data['stopThresholdMaxForceStrength'])
    self.updateStopThresholdCountDeficiencies(data['stopThresholdCountDeficiencies'])
    self.updateStopThresholdMaxSteps(data['stopThresholdMaxSteps'])
    self.updateLimitLatForEnergy(data['limitLatForEnergy'])
    self.updatePotentialsWeights(dict((potentialKind, GeoGridWeight.fromJSON(weightData)) for (potentialKind, weightData) in data['weights'].items()))

  def updateInitialProjection(self, initialProjection):
    self._updated()
    self.initialProjection = initialProjection

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

  def updateStopThresholdMaxForceStrength(self, stopThresholdMaxForceStrength):
    self._updated()
    self._stopThresholdMaxForceStrength = stopThresholdMaxForceStrength
  def updateStopThresholdCountDeficiencies(self, stopThresholdCountDeficiencies):
    self._updated()
    self._stopThresholdCountDeficiencies = stopThresholdCountDeficiencies
  def updateStopThresholdMaxSteps(self, stopThresholdMaxSteps):
    self._updated()
    self._stopThresholdMaxSteps = stopThresholdMaxSteps

  def updateLimitLatForEnergy(self, limitLatForEnergy):
    self._updated()
    self.limitLatForEnergy = limitLatForEnergy

  def updateGridStats(self, gridStats):
    self._updated()
    self._typicalDistance = gridStats.typicalDistance()
    self._typicalArea = gridStats.typicalArea()

  def updatePotentialsWeights(self, weights):
    self._updated()
    self._potentialsWeights = dict(self._potentialsWeights, **weights)

  def canBeOptimized(self):
    return self.initialProjection is not None and self.initialProjection.canBeOptimized
  def cannotBeOptimized(self):
    return not self.canBeOptimized()

  def weightedPotentials(self):
    return [(self._potentialsWeights[potential.kind], potential) for potential in self.potentials if self._potentialsWeights[potential.kind] is not None]

  ## transient information

  def setUntouched(self):
    self._untouched = True

  def setThresholdReached(self):
    self._thresholdReached = True

  def updateTransient(self, energy=None, step=None):
    self._energy = energy if energy is not None else self._energy
    self._step = step if step is not None else self._step
