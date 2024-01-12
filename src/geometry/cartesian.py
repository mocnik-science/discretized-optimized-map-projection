import math

from src.geometry.common import Common

class Point:
  def __init__(self, x, y):
    self.x = x
    self.y = y

  def __eq__(self, other):
    return self.x == other.x and self.y == other.y

class Cartesian:
  @staticmethod
  def length(x, y):
    return math.sqrt(x * x + y * y)

  @staticmethod
  def distance(start, end):
    return Cartesian.length(end.x - start.x, end.y - start.y)

  @staticmethod
  def area(cs):
    # faster than the shoelace formula
    n = len(cs)
    return sum(c.x * (cs[i + 1 if i < n - 1 else 0].y - cs[i - 1 if i > 0 else n - 1].y) for i, c in enumerate(cs)) / 2

  # @staticmethod
  # def areaShoelace(cs):
  #   xs = np.array([c.x for c in cs])
  #   ys = np.array([c.y for c in cs])
  #   # Shoelace formula
  #   areaMain = np.dot(xs[:-1], ys[1:]) - np.dot(ys[:-1], xs[1:])
  #   areaCorrection = xs[-1] * ys[0] - ys[-1] * xs[0]
  #   return (areaMain + areaCorrection) / 2

  @staticmethod
  def bearing(start, end): # in radiant, positively oriented, north is 0
    return (math.atan2(end.y - start.y, end.x - start.x) + 1.5 * Common._pi) % Common._2pi

  @staticmethod
  def orientedArea(a, b, c):
    return (a.x * b.y - b.x * a.y + b.x * c.y - c.x * b.y + c.x * a.y - a.x * c.y) / 2

  @staticmethod
  def orientation(a, b, c):
    area = Cartesian.orientedArea(a, b, c)
    return area > 0 if area != 0 else None

  @staticmethod
  def orientedAltitude(a, b, c):
    return Cartesian.orientedArea(a, b, c) / Cartesian.distance(b, c)
