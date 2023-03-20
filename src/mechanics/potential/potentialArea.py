import shapely

from src.common import *
from src.geometry.cartesian import *
from src.geometry.geo import *
from src.geoGrid.geoGrid import *
from src.mechanics.force import *
from src.mechanics.potential.potential import *

# F = - G m1 m2 / r^2
# U = F * r
# E = m1 * U
#
# konservatives Kraftfeld
# F = - nabla U(r) = - del U / del x * e_x
# U = - \int F(r) dr

class PotentialArea(Potential):
  kind = 'AREA'
  calibrationPossible = True

  def energy(self, cell, neighbouringCells):
    q = self._quantity(cell, neighbouringCells, energy=True)
    return q * len(neighbouringCells)

  def force(self, cell, neighbouringCells):
    q = self._quantity(cell, neighbouringCells, force=True)
    return [Force(self.kind, neighbouringCell, cell, q) for neighbouringCell in neighbouringCells]

  def _quantity(self, cell, neighbouringCells, **kwargs):
    # hexagon:   1 + 6 * 2/6 = 3
    # pentagon:  5/6 + 5 * 2/6 = 15/6 = 2.5
    geoA = self._settings._typicalArea * (3 if cell._isHexagon else 2.5) * self.calibrationFactor
    cartesianA = Cartesian.area(neighbouringCells)
    return self._computeQuantity(cartesianA / geoA - 1, **kwargs)
