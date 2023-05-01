from src.common.functions import sign

class Potential:
  kind = None
  calibrationPossible = False
  __exponent = 2

  def __init__(self, settings):
    self._settings = settings
    self.calibrationFactor = 1
    self.__D = None
    self.emptyCache()

  def emptyCache(self):
    pass

  def setCalibrationFactor(self, k):
    self.calibrationFactor = k

  def energy(self, cell, neighbouringCells):
    raise Exception('Needs to be implemented by inheriting class')
  def forces(self, cell, neighbouringCells):
    raise Exception('Needs to be implemented by inheriting class')
  # def energyAndForces(self, cell, neighbouringCells):
  #   raise Exception('Needs to be implemented by inheriting class')

  def _value(self, cell, neighbouringCells):
    raise Exception('Needs to be implemented by inheriting class')
  def _values(self, cell, neighbouringCells):
    raise Exception('Needs to be implemented by inheriting class')

  def _quantity(self, *args, **kwargs):
    return self.__quantity(self._value(*args), **kwargs)
  def _quantities(self, *args, **kwargs):
    return [self.__quantity(r, **kwargs) for r in self._values(*args)]
  def __quantity(self, r, energy=False, force=False):
    # D – spring constant
    #     chosen such that the force at r = R is -r (where r is the multiple of the typical distance)
    #     R = D * exponent * R**(exponent - 1)
    #     => D = R**(2 - exponent) / exponent
    if self.__D is None:
      R = .5
      self.__D = R**(2 - self.__exponent) / self.__exponent * self._settings._forceFactor
    if energy:
      return self.__D * abs(r)**self.__exponent
    elif force:
      return -self.__D * self.__exponent * abs(r)**(self.__exponent - 1) * sign(r)
    else:
      energy = self.__D * abs(r)**self.__exponent
      force = -energy * self.__exponent / r
      return energy, force




    # gravitational potential of a hogomeneous solid sphere
    # m, r – mass and radius of the ‘outer’ point mass
    # M, R – mass and radius of the big solid sphere mass
    # gamma – gravitation constant
    #         chosen such that the force at r = R is r (where r is the multiple of the typical distance)
    #         R = gamma * m * M / R**2
    #         => gamma = R**3 / (m * M)
    m = 1
    M = 1
    R = .5
    gamma = R**3 / (m * M) * self._settings._forceFactor
    sgn = sign(r)
    r = abs(r)
    if energy:
      if r < R:
        return gamma * m * M / (2 * R) * (r**2 / R**2 - 3)
      else:
        return -gamma * m * M / r
    if force:
      if r < R:
        return gamma * m * M / R * (r**3 / R**2 + 3 / 2) * sgn
      else:
        return -gamma * m * M / r**2 * sgn
    # if energy:
    #   return -1 / r**exponent * self._forceFactor
    # if force:
    #   return -exponent / r**(exponent + 1) * self._forceFactor
