import math

class Common:
  __pi180 = math.pi / 180
  __2pi = 2 * math.pi

  @staticmethod
  def normalizeAngle(a, intervalStart=0): # in radiant
    return ((a + Common.__2pi - intervalStart) % Common.__2pi) + intervalStart

  @staticmethod
  def deg2rad(x):
    return x * Common.__pi180
