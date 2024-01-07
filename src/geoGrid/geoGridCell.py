import shapely

from src.geometry.common import Common
from src.geometry.cartesian import Cartesian, Point
from src.geometry.geo import Geo, radiusEarth
from src.geometry.naturalEarth import NaturalEarth

def translatePoint(p, dLon):
  if dLon is None:
    return p
  return shapely.Point(p.x + dLon, p.y)

def translatePolygon(p, dLon):
  if dLon is None:
    return p
  return shapely.Polygon([(x + dLon, y) for (x, y) in p.exterior.coords])

class GeoGridCell:
  def __init__(self, id2, dggridCell, dLon=None):
    self._id1 = dggridCell.id
    self._id2 = id2
    self._forcesNext = []
    self._xForcesNext = None
    self._yForcesNext = None
    self._isActive = False
    self._selfAndAllNeighboursAreActive = False
    self._isHexagon = dggridCell.isHexagon()
    self._neighbours = dggridCell.neighbours
    self._neighboursOriginal = dggridCell.neighbours
    self._centreOriginal = translatePoint(dggridCell.centre, dLon)
    self._polygonOriginal = translatePolygon(dggridCell.polygon, dLon)
    self.x = radiusEarth * Common.deg2rad(self._centreOriginal.x)
    self.y = radiusEarth * Common.deg2rad(self._centreOriginal.y)
    self._neighboursBearings2 = None
    self._energy = {}
    self.__dggridCell = dggridCell

  def initNeighbours(self, neighbours):
    if any(abs(neighbour._centreOriginal.x - self._centreOriginal.x) > 270 for neighbour in neighbours):
      self._neighbours = None
      self._neighboursBearings2 = None
      return
    self._neighbours = [neighbour._id2 for neighbour in neighbours]
    neighboursBearings = [Geo.bearing(self._centreOriginal, neighbour._centreOriginal) for neighbour in neighbours]
    neighboursBearings2 = []
    i = 0
    for b0, b1 in zip(neighboursBearings, neighboursBearings[1:] + [neighboursBearings[0]]):
      if b0 >= b1:
        neighboursBearings2.append((i, b0, b1))
      else:
        neighboursBearings2.append((i, b0, 0))
        neighboursBearings2.append((i, Common._2pi, b1))
      i += 1
    self._neighboursBearings2 = neighboursBearings2

  def initAdditionalInformation(self):
    self._distanceToLand = NaturalEarth.distanceToLand(self.__dggridCell.centre)
    del self.__dggridCell

  def initTransformer(self, transformer):
    self.x, self.y = transformer.transform(self._centreOriginal.x, self._centreOriginal.y)

  def xy(self):
    return self.x, self.y

  def point(self):
    return Point(self.x, self.y)

  def setEnergy(self, kindOfPotential, energy):
    self._energy[kindOfPotential] = energy

  def energy(self, kindOfPotential):
    if kindOfPotential is None:
      return None
    elif kindOfPotential == 'ALL':
      return sum(self._energy.values())
    elif kindOfPotential in self._energy:
      return self._energy[kindOfPotential]
    raise Exception('The energy has not yet been computed')

  def addForce(self, force):
    # compute effect of the force
    dX = force.x - force.xTo
    dY = force.y - force.yTo
    if dX == 0 and dY == 0:
      raise Exception('The differences dX and dY should never both vanish')
    l = Cartesian.length(dX, dY)
    k = force.strength / l
    # update the force
    force.xForce += k * dX
    force.yForce += k * dY
    # add the force
    self._forcesNext.append(force)

  def applyForce(self):
    # sum up the force
    xForcesNext, yForcesNext = self.computeForcesNext()
    # apply the force
    self.x += xForcesNext
    self.y += yForcesNext

  def resetForcesNext(self):
    # reset next forces
    self._forcesNext = []
    self._xForcesNext = None
    self._yForcesNext = None

  def computeForcesNext(self):
    if self._xForcesNext is None or self._yForcesNext is None:
      self._xForcesNext = 0
      self._yForcesNext = 0
      for force in self._forcesNext:
        self._xForcesNext += force.xForce
        self._yForcesNext += force.yForce
    return self._xForcesNext, self._yForcesNext

  def forceVector(self, potential, k=30):
    if potential == 'ALL':
      xForcesNext, yForcesNext = self.computeForcesNext()
      return (self.x, self.y), (self.x + k * xForcesNext, self.y + k * yForcesNext)
    xForce = 0
    yForce = 0
    for force in self._forcesNext:
      if force.kind == potential:
        xForce += force.xForce
        yForce += force.yForce
    return (self.x, self.y), (self.x + k * xForce, self.y + k * yForce)

  def forceVectors(self, potential, k=30):
    collectedForces = []
    collectedForcesById = {}
    for force in self._forcesNext:
      if potential == 'ALL' or force.kind == potential:
        if force.id2To is None:
          collectedForces.append([self.x + k * force.xForce, self.y + k * force.yForce])
        else:
          if force.id2To not in collectedForcesById:
            collectedForcesById[force.id2To] = [0, 0]
          collectedForcesById[force.id2To][0] += force.xForce
          collectedForcesById[force.id2To][1] += force.yForce
    return (self.x, self.y), collectedForces + [(self.x + k * force[0], self.y + k * force[1]) for force in collectedForcesById.values()]

  # def neighboursWithEnclosingBearing(self, cells, point):
  #   return GeoGridCell.neighboursWithEnclosingBearingStatic(self.getNeighboursWithEnclosingBearingStaticData())

  def getNeighboursWithEnclosingBearingStaticData(self):
    return {
      'point': self.point(),
      'neighboursBearings2': self._neighboursBearings2,
      'centreOriginal': self._centreOriginal,
      'neighbours': self._neighbours,
    }

  @staticmethod
  def neighboursWithEnclosingBearingStatic(cellData, cells, point):
    if cellData['neighboursBearings2'] is None:
      return None
    bearing = Geo.bearing(cellData['centreOriginal'], point)
    for i, b0, b1 in cellData['neighboursBearings2']:
      if b0 > bearing and bearing >= b1:
        return [cells[cellData['neighbours'][j]] for j in [i, (i + 1) % len(cellData['neighbours'])]]
    raise Exception('This should never happen – some bearing should have been found')

  def __str__(self):
    return f"{self._id1:>4} | {self._id2:>5} | {self.x:11.1f} | {self.y:11.1f} | {'active' if self._isActive else 'inactive':>8} | {'hexagon' if self._isHexagon else 'pentagon':>8} | {', '.join([str(x) for x in self._neighbours]) if self._neighbours else '':<70} | {self._centreOriginal.x:9.4f} | {self._centreOriginal.y:9.4f}"
