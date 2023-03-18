import shapely

from src.common import *
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

  def energy(self, cell, neighbouringCells):
    q = self._quantity(cell, neighbouringCells, energy=True)
    return q * len(neighbouringCells)
    # return sum(q for neighbouringCell in neighbouringCells)
    # return self._energy(*args, self._quantity)

  def force(self, cell, neighbouringCells):
    q = self._quantity(cell, neighbouringCells, force=True)
    return [Force(self.kind, neighbouringCell, cell, q) for neighbouringCell in neighbouringCells]
    # return self._force(*args, self._quantity)

  def _quantity(self, cell, neighbouringCells, **kwargs):
  #   # force = computeArea(neighbouringCells) - optimalArea
  #   # print(shapely.Polygon([neighbouringCell.xy() for neighbouringCell in neighbouringCells]).area)

  #   # print('area', shapely.Polygon([neighbouringCell.xy() for neighbouringCell in neighbouringCells]).area)
  #   # print('area typical', self._settings._typicalArea)

    # hexagon:   1 + 6 * 2/6 = 3
    # pentagon:  5/6 + 5 * 2/6 = 15/6 = 2.5
    geoArea = self._settings._typicalArea * (3 if cell._isHexagon else 2.5)
    cartesianArea = shapely.Polygon([neighbouringCell.xy() for neighbouringCell in neighbouringCells]).area
    x = self._computeQuantity(cartesianArea / geoArea - 1, **kwargs)
    # print(f"a = {cartesianArea / geoArea - 1:9.3f} | f(r) = {x:10.0f}")
    return x
    return self._computeQuantity(cartesianArea / geoArea - 1, **kwargs)
