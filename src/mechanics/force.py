from src.geoGrid.geoGridCell import GeoGridCell
from src.geometry.cartesian import Cartesian

class Force:
  def __init__(self, kind, cell, cellTo, strength):
    self.kind = kind
    self.id2 = cell._id2
    self.id2To = cellTo._id2 if isinstance(cellTo, GeoGridCell) else None
    self.strength = strength

  # force in the direction of cellTo -> cell
  @classmethod
  def toCell(cls, kind, cell, cellTo, strength):
    force = Force(kind, cell, cellTo, strength)
    force.__initToDestination(cell, cell.x - cellTo.x, cell.y - cellTo.y)
    return force

  # force in the direction of destination -> cell
  @classmethod
  def toDestination(cls, kind, cell, destination, strength):
    force = Force(kind, cell, None, strength)
    force.__initToDestination(cell, cell.x - destination.x, cell.y - destination.y)
    return force

  # force on cell, in the direction of delta
  @classmethod
  def byDelta(cls, kind, cell, delta, strength):
    force = Force(kind, cell, None, strength)
    force.__initToDestination(cell, delta.x, delta.y)
    return force

  def __initToDestination(self, cell, dX, dY):
    # compute effect of the force
    if dX == 0 and dY == 0:
      raise Exception('The differences dX and dY should never both vanish')
    k = self.strength / Cartesian.length(dX, dY)
    # compute the force
    self.x = k * dX
    self.y = k * dY

  def scaleStrength(self, factor):
    self.x *= factor
    self.y *= factor
