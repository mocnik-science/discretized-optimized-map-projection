
# from src.common.console import Console
from src.geometry.cartesian import Cartesian
from src.geoGrid.geoGridWeight import GeoGridWeight
from src.mechanics.force import Force
from src.mechanics.potential.potential import Potential

# F = - G m1 m2 / r^2
# U = F * r
# E = m1 * U
#
# konservatives Kraftfeld
# F = - nabla U(r) = - del U / del x * e_x
# U = - \int F(r) dr

class PotentialArea(Potential):
  kind = 'AREA'
  defaultWeight = GeoGridWeight(active=True, weightLand=1, weightOceanActive=True, weightOcean=0.3, distanceTransitionStart=100000, distanceTransitionEnd=800000)
  calibrationPossible = False

  def energy(self, cell, neighbouringCells):
    if not cell._isActive:
      return 0
    return self._quantity(cell, neighbouringCells, onlyEnergy=True) * len(neighbouringCells)
  def forces(self, cell, neighbouringCells):
    if not cell._isActive:
      return []
    q = self._quantity(cell, neighbouringCells, onlyForce=True)
    return [Force.toCell(self.kind, neighbouringCell, cell, q) for neighbouringCell in neighbouringCells]
  def energyAndForces(self, cell, neighbouringCells):
    if not cell._isActive:
      return 0, []
    qEnergy, qForce = self._quantity(cell, neighbouringCells)
    return qEnergy * len(neighbouringCells), [Force.toCell(self.kind, neighbouringCell, cell, qForce) for neighbouringCell in neighbouringCells]

  def _value(self, cell, neighbouringCells):
    # cell area and partly area of the neighbouring cells
    # hexagon:   1 + 6 * 2/6 = 3
    # pentagon:  5/6 + 5 * 2/6 = 15/6 = 2.5
    cartesianA = Cartesian.orientedArea(*(neighbouringCell.point() for neighbouringCell in neighbouringCells)) * self.calibrationFactor**2
    if cartesianA < 0:
    #   geoA = (3 if cell._isHexagon else 2.5) * self._settings._typicalArea
    #   Console.print(cell._id2, cartesianA, cartesianA / geoA)
      return 0
    geoA = (3 if cell._isHexagon else 2.5) * self._settings._typicalArea
    return cartesianA / geoA - 1
