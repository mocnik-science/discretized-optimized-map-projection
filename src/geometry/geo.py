import math

from src.geometry.common import Common

radiusEarth = 6371007.1809

class Geo:
  @staticmethod
  def distance(start, end): # in metres
    startX = Common.deg2rad(start.x)
    startY = Common.deg2rad(start.y)
    endX = Common.deg2rad(end.x)
    endY = Common.deg2rad(end.y)
    # Haversine theorem
    a = math.sin((endY - startY) / 2)**2 + math.cos(startY) * math.cos(endY) * math.sin((endX - startX) / 2)**2
    return radiusEarth * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    # faster, but numerically less stable:
    # a = (1 - math.cos(endY - startY) + math.cos(startY) * math.cos(endY) * (1 - math.cos(endX - startX))) / 2
    # return radiusEarth * 2 * math.asin(min(1, math.sqrt(a)))

  @staticmethod
  def bearing(start, end): # in radiant, negatively oriented, north is 0
    startX = Common.deg2rad(start.x)
    startY = Common.deg2rad(start.y)
    endX = Common.deg2rad(end.x)
    endY = Common.deg2rad(end.y)
    y = math.sin(endX - startX) * math.cos(endY)
    x = math.cos(startY) * math.sin(endY) - math.sin(startY) * math.cos(endY) * math.cos(endX - startX)
    return Common.normalizeAngle(math.atan2(y, x))

  @staticmethod
  def areaOfTriangle(triangle): # in metres
    # compute spherical excess
    e = -Common._pi
    for i, j, k in [[0, 1, 2], [1, 2, 0], [2, 0, 1]]:
      e += Common.normalizeAngle(Geo.bearing(triangle[i], triangle[j]) - Geo.bearing(triangle[i], triangle[k]), intervalStart=-Common._pi)
      # d = Geo.bearing(triangle[i], triangle[j]) - Geo.bearing(triangle[i], triangle[k])
      # if d < -Common._pi:
      #   d += Common._2pi
      # e += d
    # Girard's theorem
    return e * radiusEarth * radiusEarth

  # @staticmethod
  # def destination(start, bearing, distance): # in radiants
  #   startX = Common.deg2rad(start.x)
  #   startY = Common.deg2rad(start.y)
  #   d = distance / radiusEarth # angular distance
  #   y2 = math.asin(math.sin(startY) * math.cos(d) + math.cos(startY) * math.sin(d) * math.cos(bearing))
  #   x2 = startX + math.atan2(math.sin(bearing) * math.sin(d) * math.cos(startY), math.cos(d) - math.sin(startY) * math.sin(y2))
  #   return Point(x2, y2)
