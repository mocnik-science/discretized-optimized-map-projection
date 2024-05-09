import math
import os

from src.common.functions import brange
from src.common.timer import timer
from src.geometry.common import Common
from src.geometry.geo import Geo
from src.geometry.naturalEarth import NaturalEarth
from src.imageBackends.imageBackendPillow import ImageBackendPillow
from src.interfaces.common.common import APP_CAPTURE_PATH

class Graticule:
  def __new__(cls):
    if not hasattr(cls, '_Graticule__instance'):
      cls.__instance = super().__new__(cls)
      cls.__initialized = False
    return cls.__instance
  
  def __init__(self):
    if not self.__initialized:
      self.__cache = {}
      self.__initialized = True

  def coordinates(self, dDegree=20, degResolution=6):
    key = (dDegree, degResolution)
    if key in self.__cache:
      return self.__cache[key]
    dDegreeN = round(180 / dDegree)
    n = dDegreeN * math.floor(dDegree / degResolution)
    self.__cache[key] = [
      [[(x, y) for x in brange(-180, 180, partitions=2 * n)] for y in brange(-90, 90, partitions=dDegreeN)],
      [[(x, y) for y in brange(-90, 90, partitions=n)] for x in brange(-180, 180, partitions=2 * dDegreeN)],
    ]
    return self.__cache[key]

class GeoGridRenderer:
  viewSettingsDefault = {
    'selectedPotential': 'ALL',
    'selectedVisualizationMethod': 'SUM',
    'selectedEnergy': None,
    'drawNeighbours': False,
    'drawLabels': False,
    'drawInitialPolygons': False,
    'drawContinentsTolerance': 3,
    'drawGraticule': False,
    'drawGraticuleDDegree': 20,
    'drawGraticuleDegResolution': 6,
    'showNthStep': 5,
  }

  @staticmethod
  def render(serializedData, geoGridSettings, viewSettings={}, size=None, maxSide=2000, border=10, transparency=False, largeSymbols=False, r=3, boundsExtend=1.3, projection=None, save=False, stepData=None, backend=ImageBackendPillow):
    # handle serialized data
    cells = serializedData['cells']
    path = serializedData['path']
    resolution = serializedData['resolution']
    step = serializedData['step']
    # view settings
    viewSettings = {
      **GeoGridRenderer.viewSettingsDefault,
      **viewSettings,
    }
    # prepare size
    width, height = size or (maxSide, maxSide)
    if width > maxSide or height > maxSide:
      width = int(2 * maxSide * width / max(width, height))
      height = int(2 * maxSide * height / max(width, height))
    width *= 2
    height *= 2
    # prepare data (happens only once)
    if viewSettings['drawContinentsTolerance']:
      NaturalEarth.preparedData()
    with timer('render', step=step):
      # compute
      widthOverall = width
      heightOverall = height
      width -= 2 * border
      height -= 2 * border
      xMin = -Common._pi * Geo.radiusEarth * boundsExtend
      xMax = -xMin
      yMin = -Common._pi_2 * Geo.radiusEarth * boundsExtend
      yMax = -yMin
      w = min(width, (xMax - xMin) / (yMax - yMin) * height)
      h = min(height, (yMax - yMin) / (xMax - xMin) * width)
      dx2 = border + (width - w) / 2
      dy2 = border + (height - h) / 2
      s = w / (xMax - xMin)
      projectToImage = lambda x, y: (dx2 + s * (x - xMin), dy2 + s * (-y - yMin))
      k = Common._pi_180 * Geo.radiusEarth
      lonLatToCartesian = lambda cs: tuple(k * c for c in cs)
      viewSettings = {
        **viewSettings,
        'widthOverall': widthOverall,
        'heightOverall': heightOverall,
      }
      # create image
      image = backend(widthOverall, heightOverall, projectToImage, transparentBackground=transparency)
      # render
      argsForRendering = [image, lonLatToCartesian, cells, geoGridSettings, viewSettings, 5 if largeSymbols else 1, (4 if largeSymbols else 1) * r, projection, stepData]
      GeoGridRenderer.renderContinents(*argsForRendering)
      GeoGridRenderer.renderGraticule(*argsForRendering)
      GeoGridRenderer.renderInitialPolygons(*argsForRendering)
      GeoGridRenderer.renderNeighbours(*argsForRendering)
      GeoGridRenderer.renderForces(*argsForRendering)
      GeoGridRenderer.renderCentres(*argsForRendering)
      GeoGridRenderer.renderStepData(*argsForRendering)
      # save
      if save:
        GeoGridRenderer.save(image, path, resolution, step)
      # return image
      return image

  @staticmethod
  def renderContinents(image, lonLatToCartesian, cells, geoGridSettings, viewSettings, w, r, projection, stepData):
    if projection is None:
      return
    if viewSettings['drawContinentsTolerance']:
      csExteriors, csInteriors = NaturalEarth.preparedData(viewSettings['drawContinentsTolerance'])
      image.group('land-outer', (image.polygon_([projection.project(*c) for c in cs], fill=(230, 230, 230)) for cs in csExteriors))
      # image.group('land-outer-stroke', (image.polygon_([projection.project(*c) for c in cs], stroke=(0, 255, 0)) for cs in csExteriors))
      image.group('land-inner', (image.polygon_([projection.project(*c) for c in cs], fill=(255, 255, 255)) for cs in csInteriors))

  @staticmethod
  def renderGraticule(image, lonLatToCartesian, cells, geoGridSettings, viewSettings, w, r, projection, stepData):
    if projection is None:
      return
    if viewSettings['drawGraticule']:
      image.group('graticule', (image.line_([projection.project(*c) for c in gc], stroke=(200, 200, 200), width=2) for gcs in Graticule().coordinates(dDegree=viewSettings['drawGraticuleDDegree'], degResolution=viewSettings['drawGraticuleDegResolution']) for gc in gcs))

  @staticmethod
  def renderInitialPolygons(image, lonLatToCartesian, cells, geoGridSettings, viewSettings, w, r, projection, stepData):
    if viewSettings['drawInitialPolygons'] and geoGridSettings.canBeOptimized():
      image.group('initial-cells', (image.polygon_([lonLatToCartesian(c) for c in cell['polygonInitialCoords']], stroke=(255, 100, 100), width=w) for cell in cells.values()))

  @staticmethod
  def renderNeighbours(image, lonLatToCartesian, cells, geoGridSettings, viewSettings, w, r, projection, stepData):
    if viewSettings['drawNeighbours'] and geoGridSettings.canBeOptimized():
      neighbours = []
      for cell in cells.values():
        if 'neighboursXY' in cell:
          for xy in cell['neighboursXY']:
            neighbours.append(image.line_(cell['xy'], xy, stroke=(220, 220, 220), width=w))
      image.group('neighbours', neighbours)

  @staticmethod
  def renderForces(image, lonLatToCartesian, cells, geoGridSettings, viewSettings, w, r, projection, stepData):
    if viewSettings['selectedPotential'] is not None and geoGridSettings.canBeOptimized():
      forces = []
      if viewSettings['selectedVisualizationMethod'] == 'SUM':
        for cell in cells.values():
          p1, p2 = cell['forceVector']
          forces.append(image.line_(p1, p2, stroke=(150, 150, 150), width=w))
      else:
        for cell in cells.values():
          p1, p2s = cell['forceVectors']
          for p2 in p2s:
            forces.append(image.line_(p1, p2, stroke=(150, 150, 150), width=w))
      image.group('forces', forces)

  @staticmethod
  def renderCentres(image, lonLatToCartesian, cells, geoGridSettings, viewSettings, w, r, projection, stepData):
    factor = 1e-4
    if viewSettings['drawLabels']:
      font = image.getImageFont('Helvetica', size=14)
    centres = []
    labels = []
    for id2, cell in cells.items():
      if geoGridSettings.cannotBeOptimized() and not cell['isActive']:
        continue
      radius = r
      fill = None
      if viewSettings['selectedEnergy'] is not None and cell['isActive']:
        radius *= .5 + max(0, min(10, 3 + math.log((cell['energy'] + 1e-10) * factor)))
        fill = (255, 140, 140)
      if viewSettings['drawCentres'] is not None:
        fill = None
        if viewSettings['drawCentres'] == 'ACTIVE':
          fill = (255, 140, 140) if cell['isActive'] else (140, 140, 255)
        else:
          for weight, potential in geoGridSettings.weightedPotentials():
            if not weight.isVanishing() and potential.kind == viewSettings['drawCentres']:
              fill = GeoGridRenderer.__blendColour(.5 * weight.forCellData(cell), colour0=(230, 230, 230), colour1=(255, 0, 0))
      if fill is not None:
        centres.append(image.point_(cell['xy'], radius, fill=fill))
      if viewSettings['drawLabels']:
        labels.append(image.text_(tuple(map(sum, zip(cell['xy'], lonLatToCartesian((.6, -.3))))), str(id2), font=font, fill=(0, 0, 0), anchor='mm' if viewSettings['drawCentres'] is None else 'la', align='center' if viewSettings['drawCentres'] is None else 'left'))
    if len(centres):
      image.group('centres', centres)
    if len(labels):
      image.group('labels', labels)

  @staticmethod
  def renderStepData(image, lonLatToCartesian, cells, geoGridSettings, viewSettings, w, r, projection, stepData):
    if viewSettings['captureVideo'] and stepData:
      texts = []
      font = image.getImageFont('Helvetica', size=40)
      texts.append(image.text_((30, viewSettings['heightOverall'] - 20), f"Step {stepData['step']}", imageCoordinates=True, font=font, fill=(0, 0, 0), anchor='ls', align='left'))
      innerEnergy, outerEnergy = stepData['energy']
      texts.append(image.text_((viewSettings['widthOverall'] - 30, viewSettings['heightOverall'] - 20), f"energy = {innerEnergy:.2e} ({outerEnergy:.2e})", imageCoordinates=True, font=font, fill=(0, 0, 0), anchor='rs', align='right'))
      image.group('stepData', texts)

  @staticmethod
  def __blendColour(value, colour0, colour1):
    return tuple(round((1 - value) * colour0[i] + value * colour1[i]) for i in range(0, 3))

  @staticmethod
  def save(image, hash, step):
    path = os.path.join(APP_CAPTURE_PATH, hash)
    pathAndFilename = os.path.join(path, f"frame-{step:08d}.png")
    os.makedirs(path, exist_ok=True)
    if not os.path.exists(pathAndFilename):
      image.save(pathAndFilename)
