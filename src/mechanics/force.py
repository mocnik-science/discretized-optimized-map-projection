from src.geoGrid.geoGridCell import GeoGridCell
from src.geometry.cartesian import Cartesian

class Force:
  def __init__(self, kind, cellFrom, cellTo, strength, withoutDamping=False):
    self.kind = kind
    self.id2From = cellFrom._id2
    self.id2To = cellTo._id2 if isinstance(cellTo, GeoGridCell) else None
    self.strength = strength
    self.withoutDamping = withoutDamping

  # force in the direction of cellFrom -> cellTo
  @staticmethod
  def toCell(kind, cellFrom, cellTo, strength, **kwargs):
    force = Force(kind, cellFrom, cellTo, strength, **kwargs)
    force.__initRelativeCoordinates(cellTo.x - cellFrom.x, cellTo.y - cellFrom.y)
    return force

  # force in the direction of cellFrom -> destination
  @staticmethod
  def toDestination(kind, cellFrom, destination, strength, **kwargs):
    force = Force(kind, cellFrom, None, strength, **kwargs)
    force.__initRelativeCoordinates(destination.x - cellFrom.x, destination.y - cellFrom.y)
    return force

  # force in the direction of cellFrom -> cellFrom + delta
  @staticmethod
  def byDelta(kind, cellFrom, delta, strength, **kwargs):
    force = Force(kind, cellFrom, None, strength, **kwargs)
    force.__initRelativeCoordinates(delta.x, delta.y)
    return force

  def __initRelativeCoordinates(self, dX, dY):
    # compute effect of the force
    if (dX == 0 and dY == 0) or self.strength == 0:
      self.x, self.y = 0, 0
    else:
      k = self.strength / Cartesian.length(dX, dY)
      # compute the force
      self.x, self.y = k * dX, k * dY

  def scaleStrength(self, factor):
    self.x *= factor
    self.y *= factor
