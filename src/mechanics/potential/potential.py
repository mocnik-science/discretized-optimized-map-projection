from src.common.functions import sign
from src.geometry.common import Common
from src.geometry.geo import Geo

class Potential:
  kind = None
  computationalOrder = 0
  defaultWeight = None
  calibrationPossible = False
  __exponent = 1
  __geoBearingsCache = {}
  __geoDistanceCache = {}

  def __init__(self, settings):
    self._settings = settings
    self.calibrationFactor = 1
    self.emptyCacheAll()

  def emptyCacheAll(self):
    self.emptyCacheDampingFactor()
    self.emptyCacheForStep()
    self.__geoBearingsCache = {}
    self.__geoDistanceCache = {}

  def emptyCacheDampingFactor(self):
    self.__D = None

  def emptyCacheForStep(self):
    pass

  def setCalibrationFactor(self, k):
    self.calibrationFactor = k

  def _geoBearingsForCell(self, cell, neighbouringCells):
    key = cell._id2
    if key not in self.__geoBearingsCache:
      # the y axis of the Cartesian coordinate system is inverted, thus the ‘-’ in the formula below
      self.__geoBearingsCache[key] = [Common.normalizeAngle(-Geo.bearing(cell._centreOriginal, neighbouringCell._centreOriginal)) for neighbouringCell in neighbouringCells]
    return self.__geoBearingsCache[key]

  def _geoDistanceForCells(self, cell1, cell2):
    key = (cell1._id2, cell2._id2)
    if key not in self.__geoDistanceCache:
      self.__geoDistanceCache[key] = Geo.distance(cell1._centreOriginal, cell2._centreOriginal)
    return self.__geoDistanceCache[key]

  def energy(self, cell, neighbouringCells):
    raise Exception('Needs to be implemented by inheriting class')
  def forces(self, cell, neighbouringCells):
    raise Exception('Needs to be implemented by inheriting class')
  # def energyAndForces(self, cell, neighbouringCells):
  #   raise Exception('Needs to be implemented by inheriting class')

  def _value(self, cell, *args):
    raise Exception('Needs to be implemented by inheriting class')
  def _values(self, cell, *args):
    raise Exception('Needs to be implemented by inheriting class')

  def _quantity(self, *args, **kwargs):
    return self.__quantity(self._value(*args), **kwargs)
  def _quantities(self, *args, **kwargs):
    return [self.__quantity(r, **kwargs) for r in self._values(*args)]
  def __quantity(self, r, energy=False, force=False, relativeToTypicalDistance=True):
    # D – spring constant
    #     chosen such that the force at r = 1/2 is -delta/2 (where delta is the typical distance)
    if self.__D is None:
      self.__D = (self._settings._typicalDistance if relativeToTypicalDistance else 1) * 2**(self.__exponent - 1)
    if energy:
      return self.__D / (self.__exponent + 1) * abs(r)**(self.__exponent + 1)
    elif force:
      return self.__D * abs(r)**self.__exponent * sign(r)
    else:
      k = self.__D * abs(r)**self.__exponent
      energy = k / (self.__exponent + 1) * abs(r)
      force = k * sign(r)
      return energy, force

    # # D – spring constant
    # #     chosen such that the force at r = R is -r (where r is the multiple of the typical distance)
    # #     R = D * exponent * R**(exponent - 1)
    # #     => D = R**(2 - exponent) / exponent
    # if self.__D is None:
    #   R = .5
    #   self.__D = R**(2 - self.__exponent) / self.__exponent * (1 - self._settings._dampingFactor) * self._settings._typicalDistance
    # if energy:
    #   return self.__D * abs(r)**self.__exponent
    # elif force:
    #   return -self.__D * self.__exponent * abs(r)**(self.__exponent - 1) * sign(r)
    # else:
    #   energy = self.__D * abs(r)**self.__exponent
    #   force = -energy * self.__exponent / r
    #   return energy, force

    # # gravitational potential of a hogomeneous solid sphere
    # # m, r – mass and radius of the ‘outer’ point mass
    # # M, R – mass and radius of the big solid sphere mass
    # # gamma – gravitation constant
    # #         chosen such that the force at r = R is r (where r is the multiple of the typical distance)
    # #         R = gamma * m * M / R**2
    # #         => gamma = R**3 / (m * M)
    # m = 1
    # M = 1
    # R = .5
    # gamma = R**3 / (m * M) * (1 - self._settings._dampingFactor) * self._settings._typicalDistance
    # sgn = sign(r)
    # r = abs(r)
    # if energy:
    #   if r < R:
    #     return gamma * m * M / (2 * R) * (r**2 / R**2 - 3)
    #   else:
    #     return -gamma * m * M / r
    # if force:
    #   if r < R:
    #     return gamma * m * M / R * (r**3 / R**2 + 3 / 2) * sgn
    #   else:
    #     return -gamma * m * M / r**2 * sgn
    # # if energy:
    # #   return -1 / r**exponent * (1 - self._settings._dampingFactor) * self._settings._typicalDistance
    # # if force:
    # #   return -exponent / r**(exponent + 1) * (1 - self._settings._dampingFactor) * self._settings._typicalDistance
