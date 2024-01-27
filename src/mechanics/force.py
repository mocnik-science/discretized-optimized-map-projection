from src.geoGrid.geoGridCell import GeoGridCell
from src.geometry.cartesian import Cartesian

class Force:
  def __init__(self, kind, cellFrom, cellTo, strength):
    self.kind = kind
    self.id2From = cellFrom._id2
    self.id2To = cellTo._id2 if isinstance(cellTo, GeoGridCell) else None
    self.strength = strength

  # force in the direction of cellFrom -> cellTo
  @staticmethod
  def toCell(kind, cellFrom, cellTo, strength):
    force = Force(kind, cellFrom, cellTo, strength)
    force.__initRelativeCoordinates(cellTo.x - cellFrom.x, cellTo.y - cellFrom.y)
    return force

  # force in the direction of cellFrom -> destination
  @staticmethod
  def toDestination(kind, cellFrom, destination, strength):
    force = Force(kind, cellFrom, None, strength)
    force.__initRelativeCoordinates(destination.x - cellFrom.x, destination.y - cellFrom.y)
    return force

  # force in the direction of cellFrom -> cellFrom + delta
  @staticmethod
  def byDelta(kind, cellFrom, delta, strength):
    force = Force(kind, cellFrom, None, strength)
    force.__initRelativeCoordinates(delta.x, delta.y)
    return force

  def __initRelativeCoordinates(self, dX, dY):
    # compute effect of the force
    if dX == 0 and dY == 0:
      self.x = 0
      self.y = 0
    else:
      k = self.strength / Cartesian.length(dX, dY)
      # compute the force
      self.x = k * dX
      self.y = k * dY

  def scaleStrength(self, factor):
    self.x *= factor
    self.y *= factor
