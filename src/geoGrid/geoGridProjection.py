from src.common.functions import minBy
from src.geometry.common import Common
from src.geometry.cartesian import Cartesian, Point
from src.geometry.geo import Geo
from src.geoGrid.geoGridCell import GeoGridCell

class GeoGridProjection:
  def __init__(self, ballTree, ballTreeCellsId1s, cellsData):
    self.__ballTree = ballTree
    self.__ballTreeCellsId1s = ballTreeCellsId1s
    self.__cellsData = cellsData

  @staticmethod
  def serializedDataForProjection(cells):
    return dict((k, cell.getNeighboursWithEnclosingBearingStaticData()) for k, cell in cells.items())

  def updateSerializedDataForProjection(self, serializedDataForProjection):
    self.__cellsData = serializedDataForProjection

  def project(self, lon, lat):
    pointLonLat = Point(lon, lat)
    dist, ind = self.__ballTree.query([[Common.deg2rad(lat), Common.deg2rad(lon)]], k=3)
    nearestCellData = None
    cornerCellsData = None
    for id2s in [self.__ballTreeCellsId1s[i] for i in ind[0]]:
      nearestCellData = minBy([self.__cellsData[id2] for id2 in id2s], by=lambda cellData: Cartesian.distance(pointLonLat, cellData['centreOriginal']))
      cornerCellsData = GeoGridCell.neighboursWithEnclosingBearingStatic(nearestCellData, self.__cellsData, pointLonLat)
      if cornerCellsData is not None:
        break
    if nearestCellData is None or cornerCellsData is None:
      raise Exception('No nearest cell found')
    cornerCellsData = [nearestCellData, *cornerCellsData]
    if cornerCellsData[0]['centreOriginal'].x == lon and cornerCellsData[0]['centreOriginal'].y == lat:
      return cornerCellsData[0]['point'].x, cornerCellsData[0]['point'].y
    cs = GeoGridProjection.__toBarycentricCoordinatesSpherical([cellData['centreOriginal'] for cellData in cornerCellsData], pointLonLat)
    return GeoGridProjection.__fromBarycentricCoordinates([cellData['point'] for cellData in cornerCellsData], cs)

  @staticmethod
  def __toBarycentricCoordinatesSpherical(triangle, point):
    coordinates = [Geo.areaOfTriangle([p if i != n else point for i, p in enumerate(triangle)]) for n in range(0, 3)]
    s = sum(coordinates)
    return [c / s for c in coordinates]

  @staticmethod
  def __fromBarycentricCoordinates(triangle, coordinates):
    return sum([coordinates[i] * triangle[i].x for i in range(0, 3)]), sum([coordinates[i] * triangle[i].y for i in range(0, 3)])
