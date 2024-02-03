import math
from pyproj import CRS, Transformer
import statistics

from src.geometry.geo import Geo
from src.geometry.common import Common

class CARDINAL_DIRECTION:
  N = 'N'
  E = 'E'
  S = 'S'
  W = 'W'
  NE = 'NE'
  NW = 'NW'
  SE = 'SE'
  SW = 'SW'
  ALL = ['N', 'E', 'S', 'W', 'NE', 'NW', 'SE', 'SW']

class CardinalDirections:
  @staticmethod
  def toCorner(direction, epsilon=1):
    if direction == CARDINAL_DIRECTION.N:
      return [0, 90 - epsilon]
    if direction == CARDINAL_DIRECTION.E:
      return [180 - epsilon, 0]
    if direction == CARDINAL_DIRECTION.S:
      return [0, -90 + epsilon]
    if direction == CARDINAL_DIRECTION.W:
      return [-180 + epsilon, 0]
    if direction == CARDINAL_DIRECTION.NE:
      return [180 - epsilon, 90 - epsilon]
    if direction == CARDINAL_DIRECTION.NW:
      return [-180 + epsilon, 90 - epsilon]
    if direction == CARDINAL_DIRECTION.SE:
      return [180 - epsilon, -90 + epsilon]
    if direction == CARDINAL_DIRECTION.SW:
      return [-180 + epsilon, -90 + epsilon]
    return direction

def strategyForScale(corners=CARDINAL_DIRECTION.ALL, horizontal=True, vertical=True, diagonalUp=False, diagonalDown=False, degreeHorizontal=360, degreeVertical=180, degreeDiagonalUp=360, degreeDiagonalDown=360, epsilon=5):
  def _strategyForScale(projection):
    transform = projection.transform if projection.transform is not None else Transformer.from_crs(CRS('EPSG:4326'), CRS(projection.srid), always_xy=True).transform
    maxX = max(abs(transform(*CardinalDirections.toCorner(corner, epsilon=epsilon))[0]) for corner in corners)
    maxY = max(abs(transform(*CardinalDirections.toCorner(corner, epsilon=epsilon))[1]) for corner in corners)
    scales = []
    def appendScale(degree_2, value):
      scales.append(Geo.radiusEarth * Common.deg2rad(degree_2) / (degree_2 / (degree_2 - epsilon) * value))
    if horizontal:
      appendScale(degreeHorizontal / 2, maxX)
    if vertical:
      appendScale(degreeVertical / 2, maxY)
    if diagonalUp:
      appendScale(degreeDiagonalUp / 2, math.sqrt(maxX**2 + maxY**2))
    if diagonalDown:
      appendScale(degreeDiagonalDown / 2, math.sqrt(maxX**2 + maxY**2))
    return statistics.mean(scales)
  return _strategyForScale
