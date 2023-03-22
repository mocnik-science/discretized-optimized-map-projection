import math

class Common:
  _pi = math.pi
  _2pi = 2 * math.pi
  _10pi = 10 * math.pi
  _pi_2 = math.pi / 2
  _pi_180 = math.pi / 180

  @staticmethod
  def normalizeAngle(a, intervalStart=0): # in radiant
    return ((a + Common._10pi - intervalStart) % Common._2pi) + intervalStart

  @staticmethod
  def deg2rad(x):
    return x * Common._pi_180
