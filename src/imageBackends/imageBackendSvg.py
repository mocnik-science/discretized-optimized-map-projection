import drawsvg as svg

from src.common.functions import flatten
from src.imageBackends.imageBackend import ImageBackend

class ImageFontSvg:
  def __init__(self, name, size=12):
    self.name = name
    self.size = size

class ImageBackendSvg(ImageBackend):
  def __init__(self, width, height, projectToImage, transparentBackground=True):
    super().__init__(projectToImage)
    self.__svg = svg.Drawing(width, height)

  @staticmethod
  def getImageFont(name, size=12):
    return ImageFontSvg(name, size=size)

  @staticmethod
  def __rgb(rgb):
    if rgb == None:
      return 'none'
    if len(rgb) != 3:
      raise Exception('rgb value must be a tuple of length 3')
    return f'rgb({rgb[0]:.0f}, {rgb[1]:.0f}, {rgb[2]:.0f})'

  def _manifest(self, x):
    return self.__svg.append(x)

  def group_(self, name, elements):
    g = svg.Group(id=name)
    for element in elements:
      g.append(element)
    return g

  def point_(self, p, r, imageCoordinates=False, fill=(0, 0, 0)):
    return svg.Circle(*self._project(p, imageCoordinates=imageCoordinates), r, fill=self.__rgb(fill))

  def line_(self, *ps, imageCoordinates=False, stroke=(0, 0, 0), width=1):
    return svg.Line(*flatten([self._project(p, imageCoordinates=imageCoordinates) for p in ps]), stroke=self.__rgb(stroke), stroke_width=width)

  def polygon_(self, ps, imageCoordinates=False, stroke=None, fill=None, width=1):
    return svg.Lines(*flatten([self._project(p, imageCoordinates=imageCoordinates) for p in ps]), fill=self.__rgb(fill), stroke=self.__rgb(stroke), stroke_width=width)

  def text_(self, p, text, imageCoordinates=False, font=None, fill=(0, 0, 0), anchor='mm', align='left'):
    if len(anchor) != 2:
      anchor = 'mm'
    textAnchor = {
      'l': 'start',
      'm': 'middle',
      'r': 'end',
    }[anchor[0]]
    dominantBaseline = {
      'b': 'auto',
      'm': 'middle',
      't': 'hanging',
    }
    x, y = self._project(p, imageCoordinates=imageCoordinates)
    return svg.Text(text, font.size if font else 12, x=x, y=y, fill=self.__rgb(fill), text_anchor=textAnchor, dominant_baseline=dominantBaseline)

  def save(self, pathAndFilename):
    self.__svg.save_svg(pathAndFilename)
