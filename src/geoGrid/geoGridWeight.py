import math

from src.geometry.common import Common

class GeoGridWeight:
  def __init__(self, active=True, weightLand=1, weightOceanActive=False, weightOcean=1, distanceTransitionStart=100000, distanceTransitionEnd=800000):
    self.__active = active
    self.__weightLand = weightLand
    self.__weightOceanActive = weightOceanActive
    self.__weightOcean = weightOcean
    self.__distanceTransitionStart = distanceTransitionStart
    self.__distanceTransitionEnd = distanceTransitionEnd

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
    if not self.__weightOceanActive or self.__weightLand == self.__weightOcean:
      return self.__weightLand
    return self._easeInOutSine(cellData['distanceToLand'], xStart=self.__distanceTransitionStart, xEnd=self.__distanceTransitionEnd, yStart=self.__weightLand, yEnd=self.__weightOcean)

  @staticmethod
  def _easeInOutSine(x, xStart=0, xEnd=1, yStart=0, yEnd=1):
    if x <= xStart:
      return yStart
    if x >= xEnd:
      return yEnd
    x = (x - xStart) / (xEnd - xStart)
    y = - (math.cos(Common._pi * x) - 1) / 2
    return yStart + y * (yEnd - yStart)
