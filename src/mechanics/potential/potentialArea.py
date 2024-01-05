import math

from src.common.functions import sign
from src.geometry.cartesian import Cartesian
from src.geoGrid.geoGridWeight import GeoGridWeight
from src.mechanics.force import Force
from src.mechanics.potential.potential import Potential

# F = - G m1 m2 / r^2
# U = F * r
# E = m1 * U
#
# konservatives Kraftfeld
# F = - nabla U(r) = - del U / del x * e_x
# U = - \int F(r) dr

class PotentialArea(Potential):
  kind = 'AREA'
  defaultWeight = GeoGridWeight(active=True, weightLand=1, weightOceanActive=True, weightOcean=0.3, distanceTransitionStart=100000, distanceTransitionEnd=800000)
  calibrationPossible = False

  def energy(self, cell, neighbouringCells):
    return self._quantity(cell, neighbouringCells, energy=True) * len(neighbouringCells)
  def forces(self, cell, neighbouringCells):
    q = self._quantity(cell, neighbouringCells, force=True)
    return [Force(self.kind, neighbouringCell, cell, q) for neighbouringCell in neighbouringCells]
  # def energyAndForces(self, cell, neighbouringCells):
  #   qEnergy, qForce = self._quantity(cell, neighbouringCells)
  #   return qEnergy * len(neighbouringCells),  [Force(self.kind, neighbouringCell, cell, qForce) for neighbouringCell in neighbouringCells]

  def _value(self, cell, neighbouringCells):
    # cell area and partly area of the neighbouring cells
    # hexagon:   1 + 6 * 2/6 = 3
    # pentagon:  5/6 + 5 * 2/6 = 15/6 = 2.5
    geoA = (3 if cell._isHexagon else 2.5) * self._settings._typicalArea * self.calibrationFactor
    cartesianA = Cartesian.area(neighbouringCells)
    sqrtGeoA = math.sqrt(geoA)
    return (math.sqrt(cartesianA) - sqrtGeoA) / sqrtGeoA
