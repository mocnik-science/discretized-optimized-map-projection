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
  def __init__(self, resolution=4):
    self.resolution = resolution
    self._dampingFactor = .99
    self._typicalDistance = None
    self._typicalArea = None
    self._forceFactor = None
    self.potentials = [PotentialArea(self), PotentialDistance(self), PotentialShape(self)]

  def updateGridStats(self, gridStats):
    self._typicalDistance = gridStats.typicalDistance()
    self._typicalArea = gridStats.typicalArea()
    self._forceFactor = (1 - self._dampingFactor) * self._typicalDistance
