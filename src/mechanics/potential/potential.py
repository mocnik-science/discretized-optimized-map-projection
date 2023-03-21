from src.common.functions import *

class Potential:
  kind = None
  calibrationPossible = False

  def __init__(self, settings):
    self._settings = settings
    self.calibrationFactor = 1

  def setCalibrationFactor(self, k):
    self.calibrationFactor = k

  def energy(self, cell, neighbouringCells):
    raise Exception('Needs to be implemented by inheriting class')

  def force(self, cell, neighbouringCells):
    raise Exception('Needs to be implemented by inheriting class')

  def _computeQuantity(self, r, energy=False, force=False, exponent=1):
    R = .5
    # D – spring constant
    #     chosen such that the force at r = R is -r (where r is the multiple of the typical distance)
    #     R = D * exponent * R**(exponent - 1)
    #     => D = R**(2 - exponent) / exponent
    sgn = sign(r)
    r = abs(r)
    D = R**(2 - exponent) / exponent * self._settings._forceFactor
    if energy:
      return D * r**exponent
    if force:
      return -D * exponent * r**(exponent - 1) * sgn
    raise Exception('Provide either energy or force')





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
