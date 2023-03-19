import math
import shapely

from src.geo import *

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
    self._kInitial = math.pi / 180 * radiusEarth
    self._forcesNext = []
    self._xForcesNext = None
    self._yForcesNext = None
    self._isActive = False
    self._isHexagon = dggridCell.isHexagon()
    self._neighbours = dggridCell.neighbours
    self._neighboursOriginal = dggridCell.neighbours
    self._centreOriginal = translatePoint(dggridCell.centre, dLon)
    self._polygonOriginal = translatePolygon(dggridCell.polygon, dLon)
    self.setCalibrationFactor(1)

  def xy(self):
    return self.x, self.y

  def point(self):
    return shapely.Point(self.x, self.y)

  def setCalibrationFactor(self, k):
    self._k = self._kInitial * k
    self.x = self._k * self._centreOriginal.x
    self.y = self._k * self._centreOriginal.y

  def addForce(self, force):
    # compute effect of the force
    dX = force.xTo - force.x
    dY = force.yTo - force.y
    if dX == 0 and dY == 0:
      raise Exception('The differences dX and dY should never both vanish')
    l = cartesianLength(dX, dY)
    k = force.strength / l
    # update the force
    force.xForce += k * dX
    force.yForce += k * dY
    # add the force
    self._forcesNext.append(force)

  def applyForce(self):
    # sum up the force
    xForcesNext, yForcesNext = self._computeForcesNext()
    # apply the force
    self.x += xForcesNext
    self.y += yForcesNext
    # reset next forces
    self._forcesNext = []
    self._xForcesNext = None
    self._yForcesNext = None

  def _computeForcesNext(self):
    if self._xForcesNext is None or self._yForcesNext is None:
      self._xForcesNext = 0
      self._yForcesNext = 0
      for force in self._forcesNext:
        self._xForcesNext += force.xForce
        self._yForcesNext += force.yForce
    return self._xForcesNext, self._yForcesNext

  def forceVector(self, potential, k=6):
    if potential == 'ALL':
      xForcesNext, yForcesNext = self._computeForcesNext()
      return (self.x, self.y), (self.x + k * xForcesNext, self.y + k * yForcesNext)
    xForce = 0
    yForce = 0
    for force in self._forcesNext:
      if force.kind == potential:
        xForce += force.xForce
        yForce += force.yForce
    return (self.x, self.y), (self.x + k * xForce, self.y + k * yForce)

  def forceVectors(self, potential, k=6):
    k *= 2
    forces = {}
    for force in self._forcesNext:
      if potential == 'ALL' or force.kind == potential:
        if force.id2To not in forces:
          forces[force.id2To] = [0, 0]
        forces[force.id2To][0] += force.xForce
        forces[force.id2To][1] += force.yForce
    return (self.x, self.y), [(self.x + k * force[0], self.y + k * force[1]) for force in forces.values()]

  def __str__(self):
    return f"{self._id1:>4} | {self._id2:>5} | {self.x:11.1f} | {self.y:11.1f} | {'active' if self._isActive else 'inactive':>8} | {'hexagon' if self._isHexagon else 'pentagon':>8} | {', '.join([str(x) for x in self._neighbours]) if self._neighbours else '':<70} | {self._centreOriginal.x:9.4f} | {self._centreOriginal.y:9.4f}"
