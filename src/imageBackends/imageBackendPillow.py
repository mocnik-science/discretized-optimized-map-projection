from PIL import Image, ImageDraw, ImageFont

from src.imageBackends.imageBackend import ImageBackend

class ImageBackendPillow(ImageBackend):
  def __init__(self, width, height, projectToImage, transparentBackground=True):
    super().__init__(projectToImage)
    self.__im = Image.new('RGBA', (width, height)) if transparentBackground else Image.new('RGB', (width, height), (255, 255, 255))
    self.__draw = ImageDraw.Draw(self.__im)

  @staticmethod
  def getImageFont(name, size=12):
    return ImageFont.truetype(name, size=size)

  def group_(self, name, elements):
    [*elements]

  def point_(self, p, r, imageCoordinates=False, fill=(0, 0, 0)):
    x, y = self._project(p, imageCoordinates=imageCoordinates)
    return self.__draw.ellipse((x - r, y - r, x + r, y + r), fill=fill)

  def line_(self, p1, p2, imageCoordinates=False, stroke=(0, 0, 0), width=1):
    return self.__draw.line([self._project(p1, imageCoordinates=imageCoordinates), self._project(p2, imageCoordinates=imageCoordinates)], fill=stroke, width=width)

  def polygon_(self, ps, imageCoordinates=False, stroke=None, fill=None, width=1):
    return self.__draw.polygon([self._project(p, imageCoordinates=imageCoordinates) for p in ps], fill=fill, outline=stroke, width=width)

  def text_(self, p, text, imageCoordinates=False, font=None, fill=(0, 0, 0), anchor='mm', align='left'):
    return self.__draw.text(self._project(p, imageCoordinates=imageCoordinates), text, font=font, fill=fill, anchor=anchor, align=align)

  def save(self, pathAndFilename):
    kwargs = {
      'optimize': True,
    } if pathAndFilename.endswith('.png') else {}
    self.__im.save(pathAndFilename, **kwargs)

  def im(self):
    return self.__im
