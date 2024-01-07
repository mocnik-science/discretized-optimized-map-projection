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
    return sum(self._quantity(cell, neighbouringCell, energy=True) for neighbouringCell in neighbouringCells)
  def forces(self, cell, neighbouringCells):
    return [Force(self.kind, neighbouringCell, cell, self._quantity(cell, neighbouringCell, force=True)) for neighbouringCell in neighbouringCells]
  # def energyAndForces(self, cell, neighbouringCells):
  #   energies = 0
  #   forces = []
  #   for neighbouringCell in neighbouringCells:
  #     qEnergy, qForce = self._quantity(cell, neighbouringCell)
  #     energies += qEnergy
  #     forces.append(Force(self.kind, neighbouringCell, cell, qForce))
  #   return energies, forces

  def _value(self, cell, neighbouringCell):
    cartesianD = Cartesian.distance(neighbouringCell, cell) * self.calibrationFactor
    geoD = self._geoDistanceForCells(neighbouringCell, cell)
    return cartesianD / geoD - 1
