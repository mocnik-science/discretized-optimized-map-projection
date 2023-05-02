from src.app.common import APP_FILE_FORMAT
from src.geoGrid.geoGridWeight import GeoGridWeight
from src.mechanics.potential.potentialArea import PotentialArea
from src.mechanics.potential.potentialDistance import PotentialDistance
from src.mechanics.potential.potentialShape import PotentialShape

# F = - G m1 m2 / r^2
# U = F * r
# E = m1 * U
#
# konservatives Kraftfeld
# F = - nabla U(r) = - del U / del x * e_x
# U = - \int F(r) dr

class GeoGridSettings:
  def __init__(self, resolution=3, dampingFactor=.99, stopThreshold=.001):
    self.resolution = resolution
    self._dampingFactor = dampingFactor
    self._stopThreshold = stopThreshold
    self._typicalDistance = None
    self._typicalArea = None
    self._forceFactor = None
    self.potentials = [PotentialArea(self), PotentialDistance(self), PotentialShape(self)]
    self._potentialsWeights = dict([(potential.kind, GeoGridWeight()) for potential in self.potentials])

  def toJSON(self):
    return {
      'fileFormat': APP_FILE_FORMAT,
      'fileFormatVersion': '1.0',
      'resolution': self.resolution,
      'dampingFactor': self._dampingFactor,
      'stopThreshold': self._stopThreshold,
      'weights': dict((potentialKind, weight.toJSON()) for (potentialKind, weight) in self._potentialsWeights.items()),
    }

  def updateFromJSON(self, data):
    if data['fileFormat'] != APP_FILE_FORMAT or data['fileFormatVersion'] != '1.0':
      raise Exception('Wrong fileformat')
    self.updateResolution(data['resolution'])
    self.updateDampingFactor(data['dampingFactor'])
    self.updateStopThreshold(data['stopThreshold'])
    self.updatePotentialsWeights(dict((potentialKind, GeoGridWeight.fromJSON(weightData)) for (potentialKind, weightData) in data['weights'].items()))

  def updateResolution(self, resolution):
    if self.resolution == resolution:
      return
    self.resolution = resolution
    for potential in self.potentials:
      potential.emptyCacheAll()

  def updateDampingFactor(self, dampingFactor):
    self._dampingFactor = dampingFactor
    self._forceFactor = (1 - self._dampingFactor) * self._typicalDistance
    for potential in self.potentials:
      potential.emptyCacheDampingFactor()

  def updateStopThreshold(self, stopThreshold):
    self._stopThreshold = stopThreshold

  def updateGridStats(self, gridStats):
    self._typicalDistance = gridStats.typicalDistance()
    self._typicalArea = gridStats.typicalArea()
    self._forceFactor = (1 - self._dampingFactor) * self._typicalDistance

  def weightedPotentials(self, allWeights=False):
    return [(self._potentialsWeights[potential.kind], potential) for potential in self.potentials if self._potentialsWeights[potential.kind] is not None and (allWeights or not self._potentialsWeights[potential.kind].isVanishing())]

  def updatePotentialsWeights(self, weights):
    self._potentialsWeights = dict(self._potentialsWeights, **weights)
