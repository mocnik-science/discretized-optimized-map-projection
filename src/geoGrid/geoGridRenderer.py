import math
import os
from PIL import Image, ImageDraw, ImageFont

from src.app.common import APP_CAPTURE_PATH
from src.common.timer import timer
from src.geometry.common import Common
from src.geometry.geo import radiusEarth
from src.geometry.naturalEarth import NaturalEarth

class GeoGridRenderer:
  viewSettingsDefault = {
    'selectedPotential': 'ALL',
    'selectedVisualizationMethod': 'SUM',
    'selectedEnergy': None,
    'drawNeighbours': False,
    'drawLabels': False,
    'drawOriginalPolygons': False,
    'drawContinentsTolerance': 3,
    'showNthStep': 5,
  }

  @staticmethod
  def render(serializedData, geoGridSettings, viewSettings={}, size=None, maxSide=2000, border=10, r=3, boundsExtend=1.3, projection=None, save=False, stepData=None):
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
      xMin = -Common._pi * radiusEarth * boundsExtend
      xMax = -xMin
      yMin = -Common._pi_2 * radiusEarth * boundsExtend
      yMax = -yMin
      w = min(width, (xMax - xMin) / (yMax - yMin) * height)
      h = min(height, (yMax - yMin) / (xMax - xMin) * width)
      dx2 = border + (width - w) / 2
      dy2 = border + (height - h) / 2
      s = w / (xMax - xMin)
      projectToImage = lambda x, y: (dx2 + s * (x - xMin), dy2 + s * (-y - yMin))
      k = Common._pi_180 * radiusEarth
      lonLatToCartesian = lambda cs: (k * c for c in cs)
      viewSettings = {
        **viewSettings,
        'widthOverall': widthOverall,
        'heightOverall': heightOverall,
      }
      # create image
      im = Image.new('RGB', (widthOverall, heightOverall), (255, 255, 255))
      draw = ImageDraw.Draw(im)
      # render
      argsForRendering = [[draw, projectToImage], lonLatToCartesian, cells, geoGridSettings, viewSettings, r, projection, stepData]
      GeoGridRenderer.renderContinentalBorders(*argsForRendering)
      GeoGridRenderer.renderOriginalPolygons(*argsForRendering)
      GeoGridRenderer.renderNeighbours(*argsForRendering)
      GeoGridRenderer.renderForces(*argsForRendering)
      GeoGridRenderer.renderCentres(*argsForRendering)
      GeoGridRenderer.renderStepData(*argsForRendering)
      # save
      if save:
        GeoGridRenderer.save(im, path, resolution, step)
      # return image
      return im

  @staticmethod
  def renderContinentalBorders(d, lonLatToCartesian, cells, geoGridSettings, viewSettings, r, projection, stepData):
    if projection is None:
      return
    if viewSettings['drawContinentsTolerance']:
      csExteriors, csInteriors = NaturalEarth.preparedData(viewSettings['drawContinentsTolerance'])
      for cs in csExteriors:
        GeoGridRenderer.__polygon(d, [projection.project(*c) for c in cs], fill=(230, 230, 230))
        # GeoGridRenderer.__polygon(d, [*lonLatToCartesian(c) for c in cs], outline=(0, 255, 0))
      for cs in csInteriors:
        GeoGridRenderer.__polygon(d, [projection.project(*c) for c in cs], fill=(255, 255, 255))

  @staticmethod
  def renderOriginalPolygons(d, lonLatToCartesian, cells, geoGridSettings, viewSettings, r, projection, stepData):
    if viewSettings['drawOriginalPolygons'] and geoGridSettings.hasNoInitialCRS():
      for cell in cells.values():
        GeoGridRenderer.__polygon(d, [lonLatToCartesian(c) for c in cell['polygonOriginalCoords']], outline=(255, 100, 100))

  @staticmethod
  def renderNeighbours(d, lonLatToCartesian, cells, geoGridSettings, viewSettings, r, projection, stepData):
    if viewSettings['drawNeighbours'] and geoGridSettings.hasNoInitialCRS():
      for cell in cells.values():
        if 'neighboursXY' in cell:
          for xy in cell['neighboursXY']:
            GeoGridRenderer.__line(d, cell['xy'], xy, fill=(220, 220, 220))

  @staticmethod
  def renderForces(d, lonLatToCartesian, cells, geoGridSettings, viewSettings, r, projection, stepData):
    if viewSettings['selectedPotential'] is not None and geoGridSettings.hasNoInitialCRS():
      if viewSettings['selectedVisualizationMethod'] == 'SUM':
        for cell in cells.values():
          p1, p2 = cell['forceVector']
          GeoGridRenderer.__line(d, p1, p2, fill=(150, 150, 150))
      else:
        for cell in cells.values():
          p1, p2s = cell['forceVectors']
          for p2 in p2s:
            GeoGridRenderer.__line(d, p1, p2, fill=(150, 150, 150))

  @staticmethod
  def renderCentres(d, lonLatToCartesian, cells, geoGridSettings, viewSettings, r, projection, stepData):
    factor = 1e-4
    if viewSettings['drawLabels']:
      font = ImageFont.truetype('Helvetica', size=14)
    for id2, cell in cells.items():
      if geoGridSettings.hasInitialCRS() and not cell['isActive']:
        continue
      radius = r
      if viewSettings['selectedEnergy'] is not None and cell['isActive']:
        radius *= .5 + max(0, min(10, 3 + math.log((cell['energy'] + 1e-10) * factor)))
      if viewSettings['drawCentres'] is not None:
        fill = None
        if viewSettings['drawCentres'] == 'ACTIVE':
          fill = (255, 140, 140) if cell['isActive'] else (140, 140, 255)
        else:
          for weight, potential in geoGridSettings.weightedPotentials():
            if not weight.isVanishing() and potential.kind == viewSettings['drawCentres']:
              fill = GeoGridRenderer.__blendColour(.5 * weight.forCellData(cell), colour0=(230, 230, 230), colour1=(255, 0, 0))
        if fill is not None:
          GeoGridRenderer.__point(d, cell['xy'], radius, fill=fill)
      if viewSettings['drawLabels']:
        GeoGridRenderer.__text(d, tuple(map(sum, zip(cell['xy'], lonLatToCartesian((.6, -.3))))), str(id2), font=font, fill=(0, 0, 0), anchor='mm' if viewSettings['drawCentres'] is None else 'la', align='center' if viewSettings['drawCentres'] is None else 'left')

  @staticmethod
  def renderStepData(d, lonLatToCartesian, cells, geoGridSettings, viewSettings, r, projection, stepData):
    if viewSettings['captureVideo'] and stepData:
      font = ImageFont.truetype('Helvetica', size=40)
      GeoGridRenderer.__text(d, (30, viewSettings['heightOverall'] - 20), f"Step {stepData['step']}", imageCoordinates=True, font=font, fill=(0, 0, 0), anchor='ls', align='left')
      innerEnergy, outerEnergy = stepData['energy']
      GeoGridRenderer.__text(d, (viewSettings['widthOverall'] - 30, viewSettings['heightOverall'] - 20), f"energy = {innerEnergy:.2e} ({outerEnergy:.2e})", imageCoordinates=True, font=font, fill=(0, 0, 0), anchor='rs', align='right')

  @staticmethod
  def __point(d, p, r, imageCoordinates=False, **kwargs):
    draw, projectToImage = d
    x, y = p if imageCoordinates else projectToImage(*p)
    draw.ellipse((x - r, y - r, x + r, y + r), **kwargs)

  @staticmethod
  def __line(d, p1, p2, imageCoordinates=False, **kwargs):
    draw, projectToImage = d
    draw.line((*(p1 if imageCoordinates else projectToImage(*p1)), *(p2 if imageCoordinates else projectToImage(*p2))), **kwargs)

  @staticmethod
  def __polygon(d, ps, imageCoordinates=False, **kwargs):
    draw, projectToImage = d
    draw.polygon([p if imageCoordinates else projectToImage(*p) for p in ps], **kwargs)

  @staticmethod
  def __text(d, p, text, imageCoordinates=False, **kwargs):
    draw, projectToImage = d
    draw.text(p if imageCoordinates else projectToImage(*p), text, **kwargs)

  @staticmethod
  def __blendColour(value, colour0, colour1):
    return tuple(round((1 - value) * colour0[i] + value * colour1[i]) for i in range(0, 3))

  @staticmethod
  def save(im, hash, step):
    path = os.path.join(APP_CAPTURE_PATH, hash)
    pathAndFilename = os.path.join(path, f"frame-{step:08d}.png")
    os.makedirs(path, exist_ok=True)
    if not os.path.exists(pathAndFilename):
      im.save(pathAndFilename, optimize=False, compress_level=1)
