import os
import requests
import shapefile
from zipfile import ZipFile

from src.timer import timer

class NaturalEarth:
  urlNaturalEarthData = 'http://naciscdn.org/naturalearth/110m/physical/ne_110m_land.zip'
  pathNaturalEarthData = '.naturalEarthData'
  fileZipNaturalEarthData = os.path.join(pathNaturalEarthData, 'ne_110m_land.zip')
  fileSubpathNaturalEarthData = os.path.join(pathNaturalEarthData, 'ne_110m_land')
  fileShpNaturalEarthData = os.path.join(fileSubpathNaturalEarthData, 'ne_110m_land.shp')
  _shpData = None
  _prepData = None

  def __new__(cls):
    if not hasattr(cls, '_instance'):
      cls._instance = super(NaturalEarth, cls).__new__(cls)
      cls._instance.__initialized = False
    return cls._instance

  def __init__(self):
    if self.__initialized:
      return
    self.__initialized = True

  def _ensureNaturalEarthData(self):
    if not os.path.exists(self.pathNaturalEarthData):
      os.mkdir(self.pathNaturalEarthData)
    if not os.path.exists(self.fileSubpathNaturalEarthData):
      os.mkdir(self.fileSubpathNaturalEarthData)
    if os.path.exists(self.fileShpNaturalEarthData):
      return self.fileShpNaturalEarthData
    with open(self.fileZipNaturalEarthData, 'wb') as file:
      with requests.get(self.urlNaturalEarthData) as request:
        file.write(request.content)
    with open(self.fileZipNaturalEarthData, 'rb') as file:
      zipFile = ZipFile(file)
      zipFile.extractall(path=self.fileSubpathNaturalEarthData)
    if not os.path.exists(self.fileShpNaturalEarthData):
      raise Exception('Could not download Natural Earth Data')
    return self.fileShpNaturalEarthData

  def _data(self):
    if self._shpData is None:
      with timer('load natural earth data'):
        self._shpData = shapefile.Reader(NaturalEarth()._ensureNaturalEarthData())
    return self._shpData

  def _preparedData(self):
    if self._prepData is None:
      data = NaturalEarth.data()
      with timer('prepare natural earth data'):
        self._prepData = []
        for g in data.shapes():
          if g.shapeType == shapefile.POLYGON:
            kStart = None
            for i, partStart in enumerate(g.parts):
              if i > 0:
                self._prepData.append(g.points[kStart:partStart])
              kStart = partStart
            self._prepData.append(g.points[kStart:])
    return self._prepData

  @staticmethod
  def data():
    return NaturalEarth()._data()

  @staticmethod
  def preparedData():
    return NaturalEarth()._preparedData()
