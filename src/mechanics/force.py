from src.geoGrid.geoGridCell import GeoGridCell
from src.geometry.cartesian import Cartesian

class Force:
  def __init__(self, kind, cell, cellTo, strength):
    self.kind = kind
    self.id2 = cell._id2
    self.id2To = cellTo._id2 if isinstance(cellTo, GeoGridCell) else None
    self.strength = strength

  # force applies to cell, in the direction of cellTo -> cell
  @classmethod
  def toCell(cls, kind, cell, cellTo, strength):
    force = Force(kind, cell, cellTo, strength)
    # compute effect of the force
    dX = cell.x - cellTo.x
    dY = cell.y - cellTo.y
    if dX == 0 and dY == 0:
      raise Exception('The differences dX and dY should never both vanish')
    k = force.strength / Cartesian.length(dX, dY)
    # compute the force
    force.x = k * dX
    force.y = k * dY
    # return
    return force

  def scaleStrength(self, factor):
    self.x *= factor
    self.y *= factor
