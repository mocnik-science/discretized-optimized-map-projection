import math

from src.geo import *

class GeoGridCell:
  def __init__(self, d):
    self._id1 = d.id
    self._id2 = d.id2
    self.x = d.geometry.x * math.pi / 180 * radiusEarth
    self.y = d.geometry.y * math.pi / 180 * radiusEarth
    self._xInitial = self.x
    self._yInitial = self.y
    self._forcesNext = []
    self._xForcesNext = None
    self._yForcesNext = None
    self._isActive = False
    self._isHexagon = len(d.geometry_polygons.exterior.coords) - 1 == 5
    self._neighbours = d.neighbours
    self._geometryCentre = d.geometry
    self._geometryPolygon = d.geometry_polygons

  def xy(self):
    return self.x, self.y

  def point(self):
    return shapely.Point(self.x, self.y)

  def setCalibrationFactor(self, k):
    self.x = k * self._xInitial
    self.y = k * self._yInitial

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
    return f"{self._id1:>4} | {self._id2:>5} | {self.x:11.1f} | {self.y:11.1f} | {'active' if self._isActive else 'inactive':>8} | {'hexagon' if self._isHexagon else 'pentagon':>8} | {', '.join(self._neighbours):>70} | {self._geometryCentre.x:9.4f} | {self._geometryCentre.y:9.4f}"
