from src.geometry.cartesian import Cartesian, Point
from src.geometry.common import Common
from src.geoGrid.geoGridWeight import GeoGridWeight
from src.mechanics.force import Force
from src.mechanics.potential.potential import Potential

class PotentialShape(Potential):
  kind = 'SHAPE'
  defaultWeight = GeoGridWeight(active=True, weightLand=.7, weightOceanActive=True, weightOcean=0.3, distanceTransitionStart=100000, distanceTransitionEnd=800000)
  calibrationPossible = False

  def __init__(self, *args, enforceNorth=False, **kwargs):
    super().__init__(*args, **kwargs)
    self._enforceNorth = enforceNorth

  def energy(self, cell, neighbouringCells):
    if not cell._isActive:
      return 0
    return sum(self._quantities(cell, neighbouringCells, onlyEnergy=True))
  def forces(self, cell, neighbouringCells):
    if not cell._isActive:
      return []
    forces = []
    for i, q in enumerate(self._quantities(cell, neighbouringCells, onlyForce=True)):
      neighbouringCell = neighbouringCells[i]
      forces.append(Force.toDestination(self.kind, neighbouringCell, Point(neighbouringCell.x + (neighbouringCell.y - cell.y), neighbouringCell.y - (neighbouringCell.x - cell.x)), q))
    return forces
  def energyAndForces(self, cell, neighbouringCells):
    energy, forces = 0, []
    if not cell._isActive:
      return energy, forces
    for i, (qEnergy, qForce) in enumerate(self._quantities(cell, neighbouringCells)):
      energy += qEnergy
      neighbouringCell = neighbouringCells[i]
      forces.append(Force.toCell(self.kind, neighbouringCell, Point(neighbouringCell.x + (neighbouringCell.y - cell.y), neighbouringCell.y - (neighbouringCell.x - cell.x)), qForce))
    return energy, forces

  def _values(self, cell, neighbouringCells):
    lenNeighbours = len(cell._neighbours)
    bearingIdeal = self._geoBearingsForCell(cell, neighbouringCells)
    # compute bearings
    bearings = [Cartesian.bearing(cell.point(), neighbouringCell.point()) for neighbouringCell in neighbouringCells]
    # compute average difference
    avgDiff = 0 if self._enforceNorth else sum([Common.normalizeAngle(bearings[i] - bearingIdeal[i], intervalStart=-Common._pi) for i in range(0, lenNeighbours)]) / lenNeighbours
    # quantities
    return [12 / (2 * Common._pi) * abs(Common.normalizeAngle(bearing - (bearingIdeal[i] + avgDiff), intervalStart=-Common._pi)) for i, bearing in enumerate(bearings)]
