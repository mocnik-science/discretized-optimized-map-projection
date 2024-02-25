from src.geometry.cartesian import Cartesian, Point
from src.geoGrid.geoGridWeight import GeoGridWeight
from src.mechanics.force import Force
from src.mechanics.potential.potential import Potential

class PotentialTriangleAltitude(Potential):
  kind = 'TRIANGLE_ALTITUDE'
  computationalOrder = 1
  defaultWeight = GeoGridWeight(active=True, weightLand=1, weightOceanActive=False, weightOcean=0.3, distanceTransitionStart=100000, distanceTransitionEnd=800000)
  calibrationPossible = False
  considerForSumOfWeights = False
  maximumStrengthRatioOfTypicalDistance = .2
  __dataForCellCache = {}

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

  def emptyCacheForStep(self):
    super().emptyCacheForStep()
    self.__dataForCellCache = {}

  def energy(self, cell, neighbouringCells):
    return 0
    # cells = dict((neighbouringCell._id2, neighbouringCell) for neighbouringCell in neighbouringCells)
    # return sum(self._quantity(cell, cells[i], cells[j], onlyEnergy=True, relativeToTypicalDistance=False) for i, j in cell.getNeighbourTriangles() if i in cells and j in cells)
  def forces(self, cell, neighbouringCells):
    cells = dict((neighbouringCell._id2, neighbouringCell) for neighbouringCell in neighbouringCells)
    forces = []
    for i, j in cell.getNeighbourTriangles():
      if i not in cells or j not in cells:
        continue
      qForce = self._quantity(cell, cells[i], cells[j], onlyForce=True, relativeToTypicalDistance=False)
      if qForce == 0:
        continue
      p = self.__dataForCellCache[(cell._id2, i, j)][1]
      forces.append(Force.toDestination(self.kind, cell, p, qForce, withoutDamping=True))
      delta = Point(cell.x - p.x, cell.y - p.y)
      forces.append(Force.byDelta(self.kind, cells[i], delta, qForce / 2, withoutDamping=True))
      forces.append(Force.byDelta(self.kind, cells[j], delta, qForce / 2, withoutDamping=True))
    return forces
  def energyAndForces(self, cell, neighbouringCells):
    return 0, self.forces(cell, neighbouringCells=neighbouringCells)
    # cells = dict((neighbouringCell._id2, neighbouringCell) for neighbouringCell in neighbouringCells)
    # quantities = [(i, j, self._quantity(cell, cells[i], cells[j], relativeToTypicalDistance=False)) for i, j in cell.getNeighbourTriangles() if i in cells and j in cells]
    # energy = sum(qEnergy for _, _, (qEnergy, _) in quantities)
    # forces = []
    # for i, j, (_, qForce) in quantities:
    #   if qForce == 0:
    #     continue
    #   p = self.__dataForCellCache[(cell._id2, i, j)][1]
    #   forces.append(Force.toDestination(self.kind, cell, p, qForce / 2, withoutDamping=True))
    #   delta = Point(cell.x - p.x, cell.y - p.y)
    #   forces.append(Force.byDelta(self.kind, cells[i], delta, qForce / 2, withoutDamping=True))
    #   forces.append(Force.byDelta(self.kind, cells[j], delta, qForce / 2, withoutDamping=True))
    # return energy, forces

  def _value(self, cell, cell1, cell2):
    Cartesian.orientedAltitude(cell.point(), cell1.point(), cell2.point())
    if (cell._id2, cell1._id2, cell2._id2) not in self.__dataForCellCache:
      # p0 = cell.point()
      # p1 = cell1.point()
      # p2 = cell2.point()
      p0 = Point(*cell.applyForces(persist=False))
      p1 = Point(*cell1.applyForces(persist=False))
      p2 = Point(*cell2.applyForces(persist=False))
      minimumDistance = self._settings._almostDeficiencyRatioOfTypicalDistance * self._settings._typicalDistance
      altitude = Cartesian.orientedAltitude(p0, p1, p2) * self.calibrationFactor
      strength = max(0, -altitude + minimumDistance)
      strength = min(strength, self.maximumStrengthRatioOfTypicalDistance * self._settings._typicalDistance)
      p = Cartesian.projectToLine(p0, p1, p2) if strength != 0 else None
      p = Cartesian.pointWithDistanceToLine(p, p1, p2, distance=minimumDistance) if strength != 0 else None
      self.__dataForCellCache[(cell._id2, cell1._id2, cell2._id2)] = (strength, p)
    strength, p = self.__dataForCellCache[(cell._id2, cell1._id2, cell2._id2)]
    return strength
