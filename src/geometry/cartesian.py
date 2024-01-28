import math

from src.geometry.common import Common

class Point:
  def __init__(self, x, y):
    self.x = x
    self.y = y

  def xy(self):
    return self.x, self.y

  def __eq__(self, other):
    return self.x == other.x and self.y == other.y

  def __str__(self):
    return f'Point(x = {self.x:.1f}, y = {self.y:.1f})'

class Cartesian:
  @staticmethod
  def length(x, y):
    return math.sqrt(x * x + y * y)

  @staticmethod
  def distance(start, end):
    return Cartesian.length(end.x - start.x, end.y - start.y)

  @staticmethod
  def orientedArea(*cs):
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
  def orientation(a, b, c):
    area = Cartesian.orientedArea(a, b, c)
    return area > 0 if area != 0 else None

  # altitude of a in the triangle a, b, c
  @staticmethod
  def orientedAltitude(a, b, c):
    return 2 * Cartesian.orientedArea(a, b, c) / Cartesian.distance(b, c)

  @staticmethod
  def bearing(start, end): # in radiant, positively oriented, north is 0
    return (math.atan2(end.y - start.y, end.x - start.x) + 1.5 * Common._pi) % Common._2pi

  # linear interpolation between the points a and b, such that the resulting x is a if k vanishes, and b if k is 1
  @staticmethod
  def interpolatePoints(a, b, k):
    return Point(a.x + k * (b.x - a.x), a.y + k * (b.y - a.y))

  # project point x to the line through a and b
  @staticmethod
  def projectToLine(x, a, b):
    ba = (b.x - a.x, b.y - a.y)
    lengthBa_2 = ba[0]**2 + ba[1]**2
    if lengthBa_2 == 0:
      return a
    k = ((x.x - a.x) * ba[0] + (x.y - a.y) * ba[1]) / lengthBa_2
    return Cartesian.interpolatePoints(a, b, k)

  # compute a point x with a given distance (by default 1) to the line through a and b, such that x is projected to p and such that the triangle (x, a, b) has positive oriented area for positive area
  @staticmethod
  def pointWithDistanceToLine(p, a, b, distance=1):
    if a.x == b.x and a.y == b.y:
      return p
    x = Point(p.x - (b.y - a.y), p.y + (b.x - a.x))
    return Cartesian.interpolatePoints(p, x, distance / Cartesian.distance(p, x))
