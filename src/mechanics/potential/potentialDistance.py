from src.geometry.cartesian import Cartesian
from src.geoGrid.geoGridWeight import GeoGridWeight
from src.mechanics.force import Force
from src.mechanics.potential.potential import Potential

class PotentialDistance(Potential):
  kind = 'DISTANCE'
  defaultWeight = GeoGridWeight(active=True, weightLand=1, weightOceanActive=True, weightOcean=0.3, distanceTransitionStart=100000, distanceTransitionEnd=800000)
  calibrationPossible = False

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

  def energy(self, cell, neighbouringCells):
    return sum(self._quantity(cell, neighbouringCell, onlyEnergy=True) for neighbouringCell in neighbouringCells)
  def forces(self, cell, neighbouringCells):
    return [Force.toCell(self.kind, neighbouringCell, cell, self._quantity(cell, neighbouringCell, onlyForce=True)) for neighbouringCell in neighbouringCells]
  def energyAndForces(self, cell, neighbouringCells):
    energy, forces = 0, []
    for neighbouringCell in neighbouringCells:
      qEnergy, qForce = self._quantity(cell, neighbouringCell)
      energy += qEnergy
      forces.append(Force.toCell(self.kind, neighbouringCell, cell, qForce))
    return energy, forces

  def _value(self, cell, neighbouringCell):
    cartesianD = Cartesian.distance(neighbouringCell.point(), cell.point()) * self.calibrationFactor
    geoD = self._geoDistanceForCells(neighbouringCell, cell)
    return cartesianD / geoD - 1
