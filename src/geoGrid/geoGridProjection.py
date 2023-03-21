import numpy as np

from src.common.functions import *
from src.geometry.common import *
from src.geometry.cartesian import *
from src.geometry.geo import *
from src.geoGrid.geoGridCell import *
from src.geoGrid.geoGridRenderer import *

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
    dist, ind = self.__ballTree.query([np.deg2rad([lat, lon])], k=3)
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