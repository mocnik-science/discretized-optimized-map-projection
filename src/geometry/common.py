import math

class Common:
  _pi = math.pi
  _2pi = 2 * math.pi
  _10pi = 10 * math.pi
  _pi_2 = math.pi / 2
  _pi_4 = math.pi / 4
  _pi_8 = math.pi / 8
  _pi_180 = math.pi / 180
  _pi__2 = math.pi**2
  _sqrt2 = math.sqrt(2)
  _sqrtPi = math.sqrt(math.pi)
  _epsilon = 1e-16

  @staticmethod
  def sign(x):
    return 1 if x > 0 else -1 if x < 0 else 0

  @staticmethod
  def normalizeAngle(a, intervalStart=0): # in radiant
    return ((a + Common._10pi - intervalStart) % Common._2pi) + intervalStart

  @staticmethod
  def deg2rad(x):
    return x * Common._pi_180

  @staticmethod
  def sinc(x):
    return math.sin(x) / x

  @staticmethod
  def restrict(x, minValue=None, maxValue=None, epsilon=None):
    eps = epsilon if epsilon else 0
    x = max(minValue + eps, x)
    return min(maxValue - eps, x)
