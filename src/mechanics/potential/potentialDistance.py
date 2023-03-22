from src.geometry.cartesian import *
from src.geometry.geo import *
from src.mechanics.force import *
from src.mechanics.potential.potential import *

class PotentialDistance(Potential):
  kind = 'DISTANCE'
  calibrationPossible = False
  
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self._geoDistanceCache = {}

  def energy(self, cell, neighbouringCells):
    return sum(self._quantity(cell, neighbouringCell, energy=True) for neighbouringCell in neighbouringCells)
  def force(self, cell, neighbouringCells):
    return [Force(self.kind, neighbouringCell, cell, self._quantity(cell, neighbouringCell, force=True)) for neighbouringCell in neighbouringCells]

  def _value(self, cell, neighbouringCell):
    geoD = self._geoDistanceForCells(neighbouringCell, cell) * self.calibrationFactor
    cartesianD = Cartesian.distance(neighbouringCell, cell)
    return cartesianD / geoD - 1

  def _geoDistanceForCells(self, cell1, cell2):
    key = (cell1._id2, cell2._id2)
    if key not in self._geoDistanceCache:
      self._geoDistanceCache[key] = Geo.distance(cell1._centreOriginal, cell2._centreOriginal)
    return self._geoDistanceCache[key]
