from src.geometry.cartesian import Cartesian, Point
from src.geometry.common import Common
from src.geometry.geo import Geo
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

  def emptyCacheAll(self):
    super().emptyCacheAll()
    self._geoBearingsCache = {}

  def energy(self, cell, neighbouringCells):
    return sum(self._quantities(cell, neighbouringCells, energy=True))
  def forces(self, cell, neighbouringCells):
    forces = []
    for i, q in enumerate(self._quantities(cell, neighbouringCells, force=True)):
      neighbouringCell = neighbouringCells[i]
      forces.append(Force(self.kind, neighbouringCell, Point(neighbouringCell.x + (neighbouringCell.y - cell.y), neighbouringCell.y - (neighbouringCell.x - cell.x)), q))
    return forces
  # def energyAndForces(self, cell, neighbouringCells):
  #   energies = 0
  #   forces = []
  #   for i, (qEnergy, qForce) in enumerate(self._quantities(cell, neighbouringCells)):
  #     energies += qEnergy
  #     neighbouringCell = neighbouringCells[i]
  #     forces.append(Force(self.kind, neighbouringCell, Point(neighbouringCell.x + (neighbouringCell.y - cell.y), neighbouringCell.y - (neighbouringCell.x - cell.x)), qForce))
  #   return energies, forces

  def _values(self, cell, neighbouringCells):
    lenNeighbours = len(cell._neighbours)
    stepBearingIdeal = self._geoBearingsForCell(cell, neighbouringCells)
    # compute bearings
    bearings = [Cartesian.bearing(cell, neighbouringCell) for neighbouringCell in neighbouringCells]
    # compute average difference
    avgDiff = 0 if self._enforceNorth else sum([Common.normalizeAngle(bearings[i] - stepBearingIdeal[i], intervalStart=-Common._pi) for i in range(0, lenNeighbours)]) / lenNeighbours
    # quantities
    return [1 / (2 * Common._pi) * Common.normalizeAngle(bearing - (stepBearingIdeal[i] + avgDiff), intervalStart=-Common._pi) for i, bearing in enumerate(bearings)]

  def _geoBearingsForCell(self, cell, neighbouringCells):
    key = cell._id2
    if key not in self._geoBearingsCache:
      # the y axis of the Cartesian coordinate system is inverted, thus the ‘-’ in the formula below
      self._geoBearingsCache[key] = [Common.normalizeAngle(-Geo.bearing(cell._centreOriginal, neighbouringCell._centreOriginal)) for neighbouringCell in neighbouringCells]
    return self._geoBearingsCache[key]
