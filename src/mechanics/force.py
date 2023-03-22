from src.geoGrid.geoGridCell import GeoGridCell

# force applies to cell, in the direction of cellTo -> cell
class Force:
  def __init__(self, kind, cell, cellTo, strength):
    self.kind = kind
    self.id2 = cell._id2
    self.x = cell.x
    self.y = cell.y
    self.id2To = cellTo._id2 if isinstance(cellTo, GeoGridCell) else None
    self.xTo = cellTo.x
    self.yTo = cellTo.y
    self.strength = strength
    self.xForce = 0
    self.yForce = 0
