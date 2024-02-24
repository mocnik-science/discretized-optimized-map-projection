class ImageBackend:
  def __init__(self, projectToImage):
    self.__projectToImage = projectToImage

  def _project(self, p, imageCoordinates=False):
    return p if imageCoordinates else self.__projectToImage(*p)

  def _manifest(self, x):
    return x

  @staticmethod
  def getImageFont(name, size=12):
    raise Exception('Not implemented')

  def group(self, *args, **kwargs):
    self._manifest(self.group_(*args, **kwargs))
  def group_(self, name, elements):
    raise Exception('Not implemented')

  def point(self, *args, **kwargs):
    self._manifest(self.point_(*args, **kwargs))
  def point_(self, p, r, imageCoordinates=False, fill=(0, 0, 0)):
    raise Exception('Not implemented')

  def line(self, *args, **kwargs):
    self._manifest(self.line_(*args, **kwargs))
  def line_(self, p1, p2, imageCoordinates=False, stroke=(0, 0, 0), width=1):
    raise Exception('Not implemented')

  def polygon(self, *args, **kwargs):
    self._manifest(self.polygon_(*args, **kwargs))
  def polygon_(self, ps, imageCoordinates=False, stroke=None, fill=None, width=1):
    raise Exception('Not implemented')

  def text(self, *args, **kwargs):
    self._manifest(self.text_(*args, **kwargs))
  def text_(self, p, text, imageCoordinates=False, font=None, fill=None, anchor='mm', align='left'):
    raise Exception('Not implemented')

  def save(self, pathAndFilename):
    raise Exception('Not implemented')

  def im(self):
    raise Exception('Not implemented')
