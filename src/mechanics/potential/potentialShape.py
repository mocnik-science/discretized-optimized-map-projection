import shapely

from src.geometry.cartesian import *
from src.geometry.common import *
from src.geometry.geo import *
from src.mechanics.force import *
from src.mechanics.potential.potential import *

class PotentialShape(Potential):
  kind = 'SHAPE'
  calibrationPossible = False
  
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

  def energy(self, cell, neighbouringCells):
    return sum(self._quantity(cell, neighbouringCells, energy=True))

  def force(self, cell, neighbouringCells):
    forces = []
    for i, q in enumerate(self._quantity(cell, neighbouringCells, force=True)):
      neighbouringCell = neighbouringCells[i]
      forces.append(Force(self.kind, neighbouringCell, shapely.Point(neighbouringCell.x + (neighbouringCell.y - cell.y), neighbouringCell.y - (neighbouringCell.x - cell.x)), q))
    return forces

  def _quantity(self, cell, neighbouringCells, **kwargs):
    lenNeighbours = len(cell._neighbours)
    stepBearingIdeal = 2 * math.pi / lenNeighbours
    # compute bearings
    bearings = [Cartesian.bearing(cell, neighbouringCell) for neighbouringCell in neighbouringCells]
    # compute average difference
    avgDiff = sum([Common.normalizeAngle(bearings[i] - i * stepBearingIdeal, intervalStart=-math.pi) for i in range(0, lenNeighbours)]) / lenNeighbours
    # quantities
    return [self._computeQuantity(Common.normalizeAngle(bearing - (i * stepBearingIdeal + avgDiff), intervalStart=-math.pi), **kwargs) for i, bearing in enumerate(bearings)]
