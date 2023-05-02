import math

from src.geometry.common import Common

class GeoGridWeight:
  def __init__(self, active=True, weightLand=1, weightOceanActive=False, weightOcean=0.25, distanceTransitionStart=100000, distanceTransitionEnd=800000):
    self.__active = active
    self.__weightLand = weightLand
    self.__weightOceanActive = weightOceanActive
    self.__weightOcean = weightOcean
    self.__distanceTransitionStart = distanceTransitionStart
    self.__distanceTransitionEnd = distanceTransitionEnd
    self.__cache = {}

  def toJSON(self):
    return {
      'active': self.__active,
      'weightLand': self.__weightLand,
      'weightOceanActive': self.__weightOceanActive,
      'weightOcean': self.__weightOcean,
      'distanceTransitionStart': self.__distanceTransitionStart,
      'distanceTransitionEnd': self.__distanceTransitionEnd,
    }

  @staticmethod
  def fromJSON(data):
    return GeoGridWeight(**data)

  def isActive(self):
    return self.__active
  def weightLand(self):
    return self.__weightLand
  def isWeightOceanActive(self):
    return self.__weightOceanActive
  def weightOcean(self):
    return self.__weightOcean
  def distanceTransitionStart(self):
    return self.__distanceTransitionStart
  def distanceTransitionEnd(self):
    return self.__distanceTransitionEnd

  def isVanishing(self):
    return not self.isActive() or (self.__weightLand == 0 and (not self.__weightOceanActive or self.__weightOcean == 0))

  def forCell(self, cell):
    return self.forCellData({
      'distanceToLand': cell._distanceToLand,
    })
  def forCellData(self, cellData):
    if not self.isActive():
      return 0
    if cellData['distanceToLand'] in self.__cache:
      return self.__cache[cellData['distanceToLand']]
    weight = None
    if not self.__weightOceanActive or self.__weightLand == self.__weightOcean:
      weight = self.__weightLand
    else:
      weight = self._easeInOutSine(cellData['distanceToLand'], xStart=self.__distanceTransitionStart, xEnd=self.__distanceTransitionEnd, yStart=self.__weightLand, yEnd=self.__weightOcean)
    self.__cache[cellData['distanceToLand']] = weight
    return weight

  @staticmethod
  def _easeInOutSine(x, xStart=0, xEnd=1, yStart=0, yEnd=1):
    if x <= xStart:
      return yStart
    if x >= xEnd:
      return yEnd
    x = (x - xStart) / (xEnd - xStart)
    y = - (math.cos(Common._pi * x) - 1) / 2
    return yStart + y * (yEnd - yStart)
