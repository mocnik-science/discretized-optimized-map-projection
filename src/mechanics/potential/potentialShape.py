from src.geometry.cartesian import Cartesian
from src.geometry.common import Common
from src.mechanics.force import Force
from src.mechanics.potential.potential import Potential

class PotentialShape(Potential):
  kind = 'SHAPE'
  calibrationPossible = False
  
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

  def energy(self, cell, neighbouringCells):
    return sum(self._quantities(cell, neighbouringCells, energy=True))
  def force(self, cell, neighbouringCells):
    forces = []
    for i, q in enumerate(self._quantities(cell, neighbouringCells, force=True)):
      neighbouringCell = neighbouringCells[i]
      forces.append(Force(self.kind, neighbouringCell, Point(neighbouringCell.x + (neighbouringCell.y - cell.y), neighbouringCell.y - (neighbouringCell.x - cell.x)), q))
    return forces
  def energyAndForce(self, cell, neighbouringCells):
    energies = 0
    forces = []
    for i, (qEnergy, qForce) in enumerate(self._quantities(cell, neighbouringCells)):
      energies += qEnergy
      neighbouringCell = neighbouringCells[i]
      forces.append(Force(self.kind, neighbouringCell, Point(neighbouringCell.x + (neighbouringCell.y - cell.y), neighbouringCell.y - (neighbouringCell.x - cell.x)), qForce))
    return energies, forces

  def _values(self, cell, neighbouringCells):
    lenNeighbours = len(cell._neighbours)
    stepBearingIdeal = 2 * math.pi / lenNeighbours
    # compute bearings
    bearings = [Cartesian.bearing(cell, neighbouringCell) for neighbouringCell in neighbouringCells]
    # compute average difference
    avgDiff = sum([Common.normalizeAngle(bearings[i] - i * stepBearingIdeal, intervalStart=-math.pi) for i in range(0, lenNeighbours)]) / lenNeighbours
    # quantities
    return [Common.normalizeAngle(bearing - (i * stepBearingIdeal + avgDiff), intervalStart=-math.pi) for i, bearing in enumerate(bearings)]
