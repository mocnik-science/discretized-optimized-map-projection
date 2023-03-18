from src.geo import *
from src.mechanics.force import *
from src.mechanics.potential.potential import *

class PotentialDistance(Potential):
  kind = 'DISTANCE'
  
  def energy(self, *args):
    return self._energy(*args, self._quantity)

  def force(self, *args):
    return self._force(self.kind, *args, self._quantity)

  def _energy(self, cell, neighbouringCells, computeQuantity):
    return sum(computeQuantity(cell, neighbouringCell, energy=True) for neighbouringCell in neighbouringCells)
  def _force(self, kind, cell, neighbouringCells, computeQuantity):
    return [Force(kind, neighbouringCell, cell, computeQuantity(cell, neighbouringCell, force=True)) for neighbouringCell in neighbouringCells]

  def _quantity(self, cell, neighbouringCell, **kwargs):
    geoDist = geoDistance(neighbouringCell, cell)
    cartesianDist = cartesianDistance(neighbouringCell, cell)
    # print('r =', cartesianDist / geoDist - 1)
    x = self._computeQuantity(cartesianDist / geoDist - 1, **kwargs)
    # print('f(r) =', x)
    # print(f"r = {cartesianDist / geoDist - 1:9.3f} | f(r) = {x:10.0f}")
    return x
    return self._computeQuantity(cartesianDist / geoDist - 1, **kwargs)
