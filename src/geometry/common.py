import math

class Common:
  @staticmethod
  def normalizeAngle(a, intervalStart=0): # in radiant
    return ((a + 2 * math.pi - intervalStart) % (2 * math.pi)) + intervalStart
