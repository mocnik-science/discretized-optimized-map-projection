from src.geometry.cartesian import Cartesian, Point
from src.geometry.common import Common
from src.geoGrid.geoGridWeight import GeoGridWeight
from src.mechanics.force import Force
from src.mechanics.potential.potential import Potential

class PotentialShape(Potential):
  kind = 'SHAPE'
  defaultWeight = GeoGridWeight(active=True, weightLand=.7, weightOceanActive=True, weightOcean=.3, distanceTransitionStart=100000, distanceTransitionEnd=800000)
  calibrationPossible = False
  averaged = True

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
    quantities = self._quantities(cell, neighbouringCells, onlyForce=True) / len(quantities)
    qAveraged = sum(quantities) if self.averaged else None
    for i, q in enumerate(quantities):
      neighbouringCell = neighbouringCells[i]
      forces.append(Force.toDestination(self.kind, neighbouringCell, Point(neighbouringCell.x + (neighbouringCell.y - cell.y), neighbouringCell.y - (neighbouringCell.x - cell.x)), qAveraged if self.averaged else q))
    return forces
  def energyAndForces(self, cell, neighbouringCells):
    energy, forces = 0, []
    if not cell._isActive:
      return energy, forces
    quantities = self._quantities(cell, neighbouringCells)
    qForceAveraged = sum([qForce for (_, qForce) in quantities]) / len(quantities) if self.averaged else None
    for i, (qEnergy, qForce) in enumerate(quantities):
      energy += qEnergy
      neighbouringCell = neighbouringCells[i]
      forces.append(Force.toCell(self.kind, neighbouringCell, Point(neighbouringCell.x + (neighbouringCell.y - cell.y), neighbouringCell.y - (neighbouringCell.x - cell.x)), qForceAveraged if self.averaged else qForce))
    return energy, forces

  def _values(self, cell, neighbouringCells):
    lenNeighbours = len(cell._neighbours)
    bearingIdeal = self._geoBearingsForCell(cell, neighbouringCells)
    # compute bearings
    bearings = [Cartesian.bearing(cell.point(), neighbouringCell.point()) for neighbouringCell in neighbouringCells]
    # compute average difference
    avgDiff = 0 if self._enforceNorth else sum([Common.normalizeAngle(bearings[i] - bearingIdeal[i], intervalStart=-Common._pi) for i in range(0, lenNeighbours)]) / lenNeighbours
    # quantities
    return [6 / Common._pi * abs(Common.normalizeAngle(bearing - (bearingIdeal[i] + avgDiff), intervalStart=-Common._pi)) for i, bearing in enumerate(bearings)]
