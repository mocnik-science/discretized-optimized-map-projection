import os
import requests
import shapefile
import shapely
from zipfile import ZipFile

from src.common.timer import timer

class NaturalEarth:
  urlNaturalEarthData = 'http://naciscdn.org/naturalearth/110m/physical/ne_110m_land.zip'
  pathNaturalEarthData = '.naturalEarthData'
  fileZipNaturalEarthData = os.path.join(pathNaturalEarthData, 'ne_110m_land.zip')
  fileSubpathNaturalEarthData = os.path.join(pathNaturalEarthData, 'ne_110m_land')
  fileShpNaturalEarthData = os.path.join(fileSubpathNaturalEarthData, 'ne_110m_land.shp')
  _shpData = None
  _prepData = {}

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

  @staticmethod
  def __simplify(exteriors, interiors, tolerance):
    exteriors = [shapely.simplify(shapely.Polygon(cs), tolerance) for cs in exteriors]
    if tolerance <= 2:
      exteriors = [cs.exterior.coords for cs in sorted(exteriors, key=lambda cs: cs.area)[-20:]]
      interiors = [shapely.simplify(shapely.Polygon(cs), tolerance).exterior.coords for cs in interiors]
      return exteriors, interiors
    return [cs.exterior.coords for cs in sorted(exteriors, key=lambda cs: cs.area)[-4:]], []

  def _preparedData(self, simplifyTolerance='full'):
    if 'full' not in self._prepData:
      data = NaturalEarth.data()
      with timer('prepare natural earth data'):
        exteriors = []
        interiors = []
        for g in data.shapes():
          if g.shapeType == shapefile.POLYGON:
            kStart = None
            geometries = []
            for i, partStart in enumerate(g.parts):
              if i > 0:
                geometries.append(g.points[kStart:partStart])
              kStart = partStart
            geometries.append(g.points[kStart:])
            exteriors.append(geometries[0])
            interiors += geometries[1:]
        self._prepData['full'] = [exteriors, interiors]
    if simplifyTolerance != 'full' and simplifyTolerance not in self._prepData:
        self._prepData[simplifyTolerance] = self.__simplify(*self._prepData['full'], simplifyTolerance)
        # self._prepData[simplifyTolerance] = [[self.__simplify(cs, simplifyTolerance) for cs in css] for css in self._prepData['full']]
    return self._prepData['full' if simplifyTolerance == 'full' else simplifyTolerance]

  @staticmethod
  def data():
    return NaturalEarth()._data()

  @staticmethod
  def preparedData(*args, **kwargs):
    return NaturalEarth()._preparedData(*args, **kwargs)
