import math
import os
from PIL import Image, ImageDraw, ImageFont

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
  def render(serializedData, geoGridSettings, viewSettings={}, size=None, maxSize=(2000, 1400), border=10, r=3, boundsExtend=1.3, projection=None, save=False):
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
    maxWidth, maxHeight = maxSize
    width, height = size or maxSize
    width = min(2 * width, maxWidth)
    height = min(2 * height, maxHeight)
    # prepare data (happens only once)
    if viewSettings['drawContinentsTolerance']:
      NaturalEarth.preparedData()
    with timer('render', step=step):
      # compute
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
      # create image
      im = Image.new('RGB', (width, height), (255, 255, 255))
      draw = ImageDraw.Draw(im)
      # render
      argsForRendering = [[draw, projectToImage], lonLatToCartesian, cells, geoGridSettings, viewSettings, r, projection]
      GeoGridRenderer.renderContinentalBorders(*argsForRendering)
      GeoGridRenderer.renderOriginalPolygons(*argsForRendering)
      GeoGridRenderer.renderNeighbours(*argsForRendering)
      GeoGridRenderer.renderForces(*argsForRendering)
      GeoGridRenderer.renderCentres(*argsForRendering)
      # save
      if save:
        GeoGridRenderer.save(im, path, resolution, step)
      # return image
      return im

  @staticmethod
  def renderContinentalBorders(d, lonLatToCartesian, cells, geoGridSettings, viewSettings, r, projection):
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
  def renderOriginalPolygons(d, lonLatToCartesian, cells, geoGridSettings, viewSettings, r, projection):
    if viewSettings['drawOriginalPolygons']:
      for cell in cells.values():
        GeoGridRenderer.__polygon(d, [lonLatToCartesian(c) for c in cell['polygonOriginalCoords']], outline=(255, 100, 100))

  @staticmethod
  def renderNeighbours(d, lonLatToCartesian, cells, geoGridSettings, viewSettings, r, projection):
    if viewSettings['drawNeighbours']:
      for cell in cells.values():
        if 'neighboursXY' in cell:
          for xy in cell['neighboursXY']:
            GeoGridRenderer.__line(d, cell['xy'], xy, fill=(220, 220, 220))

  @staticmethod
  def renderForces(d, lonLatToCartesian, cells, geoGridSettings, viewSettings, r, projection):
    if viewSettings['selectedPotential'] is not None:
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
  def renderCentres(d, lonLatToCartesian, cells, geoGridSettings, viewSettings, r, projection):
    factor = 1e-4
    if viewSettings['drawLabels']:
      font = ImageFont.truetype('Helvetica', size=12)
    for id2, cell in cells.items():
      radius = r
      if viewSettings['selectedEnergy'] is not None and cell['isActive']:
        radius *= .5 + max(0, min(10, 3 + math.log(cell['energy'] * factor)))
      if viewSettings['drawColours'] == 'ACTIVE':
        fill = (255, 140, 140) if cell['isActive'] else (140, 140, 255)
      else:
        for w, potential in geoGridSettings.weightedPotentials():
          if potential.kind == viewSettings['drawColours']:
            fill = GeoGridRenderer.__blendColour(.5 * w.forCellData(cell), colour0=(230, 230, 230), colour1=(255, 0, 0))
      GeoGridRenderer.__point(d, cell['xy'], radius, fill=fill)
      if viewSettings['drawLabels']:
        GeoGridRenderer.__text(d, cell['xy'], str(id2), font=font, fill=(0, 0, 0))

  @staticmethod
  def __point(d, p, r, **kwargs):
    draw, projectToImage = d
    x, y = projectToImage(*p)
    draw.ellipse((x - r, y - r, x + r, y + r), **kwargs)

  @staticmethod
  def __line(d, p1, p2, **kwargs):
    draw, projectToImage = d
    draw.line((*projectToImage(*p1), *projectToImage(*p2)), **kwargs)

  @staticmethod
  def __polygon(d, ps, **kwargs):
    draw, projectToImage = d
    draw.polygon([projectToImage(*p) for p in ps], **kwargs)

  @staticmethod
  def __text(d, p, text, **kwargs):
    draw, projectToImage = d
    draw.text(projectToImage(*p), text, **kwargs)

  @staticmethod
  def __blendColour(value, colour0, colour1):
    return tuple(round((1 - value) * colour0[i] + value * colour1[i]) for i in range(0, 3))

  @staticmethod
  def save(im, path, resolution, step):
    if not os.path.exists(path):
      os.mkdir(path)
    filename = os.path.join(path, 'cells-{resolution}-{step}.png'.format(resolution=resolution, step=step))
    if not os.path.exists(filename):
      im.save(filename, optimize=False, compress_level=1)
