from src.geometry.cartesian import *
from src.geometry.geo import *
from src.mechanics.force import *
from src.mechanics.potential.potential import *

class PotentialDistance(Potential):
  kind = 'DISTANCE'
  calibrationPossible = True
  
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self._geoDistanceCache = {}

  def energy(self, *args):
    return self._energy(*args, self._quantity)

  def force(self, *args):
    return self._force(self.kind, *args, self._quantity)

  def _energy(self, cell, neighbouringCells, computeQuantity):
    return sum(computeQuantity(cell, neighbouringCell, energy=True) for neighbouringCell in neighbouringCells)
  def _force(self, kind, cell, neighbouringCells, computeQuantity):
    return [Force(kind, neighbouringCell, cell, computeQuantity(cell, neighbouringCell, force=True)) for neighbouringCell in neighbouringCells]

  def _quantity(self, cell, neighbouringCell, **kwargs):
    geoD = self._geoDistanceForCells(neighbouringCell, cell) * self.calibrationFactor
    cartesianD = Cartesian.distance(neighbouringCell, cell)
    return self._computeQuantity(cartesianD / geoD - 1, **kwargs)

  def _geoDistanceForCells(self, cell1, cell2):
    key = (cell1._id2, cell2._id2)
    if key not in self._geoDistanceCache:
      self._geoDistanceCache[key] = Geo.distance(cell1._centreOriginal, cell2._centreOriginal)
    return self._geoDistanceCache[key]
