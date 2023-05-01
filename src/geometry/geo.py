import math
import shapely

from src.geometry.cartesian import Point
from src.geometry.common import Common

radiusEarth = 6371007.1809
radiusEarth2 = radiusEarth * radiusEarth

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
  def areaOfTriangle(triangle): # in square metres
    # compute spherical excess
    e = -Common._pi
    for i, j, k in [[0, 1, 2], [1, 2, 0], [2, 0, 1]]:
      e += Common.normalizeAngle(Geo.bearing(triangle[i], triangle[j]) - Geo.bearing(triangle[i], triangle[k]), intervalStart=-Common._pi)
      # d = Geo.bearing(triangle[i], triangle[j]) - Geo.bearing(triangle[i], triangle[k])
      # if d < -Common._pi:
      #   d += Common._2pi
      # e += d
    # Girard's theorem
    return e * radiusEarth2

  @staticmethod
  def areaOfPolygon(polygon): # in square metres
    # close the polygon
    points = [Point(*cs) for cs in polygon.exterior.coords]
    if points[0] != points[-1]:
      points += [points[0]]
    # extend the polygon by repeating the first and last point
    points = [points[-2]] + points
    # compute the number of points
    lenPoints = len(points) - 2 # reduced by the two repeated points
    # compute the spherical excess
    e = (lenPoints - 2) * -Common._pi
    for i in range(1, lenPoints + 1):
      e += Common.normalizeAngle(Geo.bearing(points[i], points[i - 1]) - Geo.bearing(points[i], points[i + 1]))
    # generalized Girard's theorem
    return e * radiusEarth2

  # @staticmethod
  # def destination(start, bearing, distance): # in radiants
  #   startX = Common.deg2rad(start.x)
  #   startY = Common.deg2rad(start.y)
  #   d = distance / radiusEarth # angular distance
  #   y2 = math.asin(math.sin(startY) * math.cos(d) + math.cos(startY) * math.sin(d) * math.cos(bearing))
  #   x2 = startX + math.atan2(math.sin(bearing) * math.sin(d) * math.cos(startY), math.cos(d) - math.sin(startY) * math.sin(y2))
  #   return Point(x2, y2)

  @staticmethod
  def contained(p, geometry):
    for g in geometry if isinstance(geometry, list) else [geometry]:
      if g.contains(p):
        return True
    return False

  @staticmethod
  # segmentation length in km
  def segmentize(geometry, segmentation=10000):
    maxSegmentInDegree = segmentation * 360 / (Common._pi * 2 * radiusEarth)
    return [shapely.segmentize(g, max_segment_length=maxSegmentInDegree) for g in (geometry if isinstance(geometry, list) else [geometry])]

  class PreparedForDistanceTo:
    def __init__(self, geometry, segmentation=10000):
      # the area is compared in the degree coordinate system, not in real area on the Earth's surface; this is only an approximation but improves running times sufficiently well
      geometry = sorted(geometry, key=lambda g: shapely.area(g)) if isinstance(geometry, list) else [geometry]
      self.__geometries = {
        1: Geo.segmentize(geometry, segmentation=segmentation),
        10: Geo.segmentize(geometry, segmentation=10 * segmentation),
      }
    def geometry(self, k):
      return self.__geometries[k]

  @staticmethod
  def distanceTo(p, geometry, segmentation=10000):
    # check whether the point is contained in the geometry
    if Geo.contained(p, geometry.geometry(1) if isinstance(geometry, Geo.PreparedForDistanceTo) else geometry):
      return 0
    # prepare the data
    gs = Geo.PreparedForDistanceTo(geometry, segmentation=segmentation) if not isinstance(geometry, Geo.PreparedForDistanceTo) else geometry
    # compute relevant distances
    dist = None
    pss = []
    segmentationMultiplier = 10
    segmentationDiff = segmentationMultiplier * segmentation / 2
    for g in gs.geometry(segmentationMultiplier):
      skip = 0
      pss.append([])
      for p2 in g.exterior.coords[:-1]:
        if skip > 0:
          skip -= 1
          pss[-1].append((p2, None))
          continue
        dist2 = Geo.distance(p, Point(*p2))
        pss[-1].append((p2, dist2))
        if dist is not None and dist2 > dist + segmentationDiff:
          skip = math.floor(max(0, (dist2 - dist - segmentationDiff) / 10 / segmentation))
        dist = min(dist, dist2) if dist is not None else dist2
    # compute relevant line segments
    lineSegments = []
    for ps in pss:
      currentLineSegment = None
      for i, (p2, d) in enumerate(ps):
        if d is not None and d <= dist + segmentationDiff:
          if currentLineSegment is None:
            currentLineSegment = [ps[(i - 1 + len(ps)) % len(ps)]]
          currentLineSegment.append((p2, d))
        elif currentLineSegment is not None:
          lineSegments.append([*currentLineSegment, ps[(i + 1) % len(ps)]])
          currentLineSegment = None
    # add points to line segments
    pointss = []
    for lineSegment in lineSegments:
      pointss.append([])
      for i, (p2, d) in enumerate(lineSegment):
        pointss[-1].append((p2, d))
        if i < len(lineSegment) - 1:
          p3, _ = lineSegment[i + 1]
          for k in [j / segmentationMultiplier for j in range(1, segmentationMultiplier)]:
            p23 = ((1 - k) * p2[0] + k * p3[0], (1 - k) * p2[1] + k * p3[1])
            pointss[-1].append((p23, None))
    # find nearest point on line segments
    for points in pointss:
      skip = 0
      for p2, d in points:
        if d is None and skip > 0:
          skip -= 1
          continue
        dist2 = d if d is not None else Geo.distance(p, Point(*p2))
        if dist2 > dist:
          skip = math.floor((dist2 - dist) / segmentation)
        else:
          dist = dist2
    return dist
