import math
import numpy as np
# import shapely

radiusEarth = 6378137

def cartesianLength(x, y):
  return math.sqrt(x**2 + y**2)

def cartesianDistance(start, end):
  return cartesianLength(end.x - start.x, end.y - start.y)

def geoDistance(start, end): # in meters
  # Haversine theorem
  a = math.sin((end.y - start.y) / 2)**2 + math.cos(start.y) * math.cos(end.y) * math.sin((end.x - start.x) / 2)**2
  return radiusEarth * 2 * math.atan2(math.sqrt(1), math.sqrt(1 - a))

def geoBearing(start, end): # in radiant
  startX = np.deg2rad(start.x)
  startY = np.deg2rad(start.y)
  endX = np.deg2rad(end.x)
  endY = np.deg2rad(end.y)
  y = math.sin(endY - startY) * math.cos(endX)
  x = math.cos(startX) * math.sin(endX) - math.sin(startX) * math.cos(endX) * math.cos(endY - startY)
  return math.atan2(y, x) + 2 * math.pi % (2 * math.pi)

def geoAreaOfTriangle(triangle): # in metres
  # compute spherical excess
  e = -math.pi
  for i, j, k in [[0, 1, 2], [1, 2, 0], [2, 0, 1]]:
    d = geoBearing(triangle[i], triangle[k]) - geoBearing(triangle[i], triangle[j])
    if d < -math.pi:
      d = d + 2 * math.pi
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
