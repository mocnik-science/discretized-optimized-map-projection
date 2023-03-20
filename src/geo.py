import math
import numpy as np

radiusEarth = 6371007.1809

def cartesianLength(x, y):
  return math.sqrt(x**2 + y**2)

def cartesianDistance(start, end):
  return cartesianLength(end.x - start.x, end.y - start.y)

def cartesianArea(cs):
  xs = np.array([c.x for c in cs])
  ys = np.array([c.y for c in cs])
  # Shoelace formula
  areaMain = np.dot(xs[:-1], ys[1:]) - np.dot(ys[:-1], xs[1:])
  areaCorrection = xs[-1] * ys[0] - ys[-1] * xs[0]
  return np.abs(areaMain + areaCorrection) / 2

def geoDistance(start, end): # in metres
  startX = np.deg2rad(start.x)
  startY = np.deg2rad(start.y)
  endX = np.deg2rad(end.x)
  endY = np.deg2rad(end.y)
  # Haversine theorem
  a = math.sin((endY - startY) / 2)**2 + math.cos(startY) * math.cos(endY) * math.sin((endX - startX) / 2)**2
  return radiusEarth * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
  # faster, but numerically less stable:
  # a = (1 - math.cos(endY - startY) + math.cos(startY) * math.cos(endY) * (1 - math.cos(endX - startX))) / 2
  # return radiusEarth * 2 * math.asin(min(1, math.sqrt(a)))

def geoBearing(start, end): # in radiant
  startX = np.deg2rad(start.x)
  startY = np.deg2rad(start.y)
  endX = np.deg2rad(end.x)
  endY = np.deg2rad(end.y)
  y = math.sin(endX - startX) * math.cos(endY)
  x = math.cos(startY) * math.sin(endY) - math.sin(startY) * math.cos(endY) * math.cos(endX - startX)
  return (math.atan2(y, x) + 2 * math.pi) % (2 * math.pi)

def geoAreaOfTriangle(triangle): # in metres
  # compute spherical excess
  e = -math.pi
  for i, j, k in [[0, 1, 2], [1, 2, 0], [2, 0, 1]]:
    d = geoBearing(triangle[i], triangle[j]) - geoBearing(triangle[i], triangle[k])
    if d < -math.pi:
      d += 2 * math.pi
    e += d
  # Girard's theorem
  return e * radiusEarth**2

# def destination(start, bearing, distance): # in radiants
#   startX = np.deg2rad(start.x)
#   startY = np.deg2rad(start.y)
#   d = distance / radiusEarth # angular distance
#   y2 = math.asin(math.sin(startY) * math.cos(d) + math.cos(startY) * math.sin(d) * math.cos(bearing))
#   x2 = startX + math.atan2(math.sin(bearing) * math.sin(d) * math.cos(startY), math.cos(d) - math.sin(startY) * math.sin(y2))
#   return shapely.Point(x2, y2)
