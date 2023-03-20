import math
import numpy as np

class Cartesian:
  @staticmethod
  def length(x, y):
    return math.sqrt(x**2 + y**2)

  @staticmethod
  def distance(start, end):
    return Cartesian.length(end.x - start.x, end.y - start.y)

  @staticmethod
  def area(cs):
    xs = np.array([c.x for c in cs])
    ys = np.array([c.y for c in cs])
    # Shoelace formula
    areaMain = np.dot(xs[:-1], ys[1:]) - np.dot(ys[:-1], xs[1:])
    areaCorrection = xs[-1] * ys[0] - ys[-1] * xs[0]
    return np.abs(areaMain + areaCorrection) / 2

  @staticmethod
  def bearing(start, end): # in radiant, positively oriented, north is 0
    return (math.atan2(end.y - start.y, end.x - start.x) + 1.5 * math.pi) % (2 * math.pi)
