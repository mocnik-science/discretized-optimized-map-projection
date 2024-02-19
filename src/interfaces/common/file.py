import os
import shutil

class File:
  _defaultPath = '~/Downloads'

  def __init__(self, geoGridSettings, *parts, extension=None, path=None, addHash=None):
    self._initialProjectionName = geoGridSettings.initialProjection.name.replace(' ', '_').replace('-', '_')
    self._hash = geoGridSettings.hash()
    self._parts = [str(part) for part in parts] if parts else []
    self._extension = extension
    self._paths = [path or File._defaultPath]
    self._addHash = addHash
    self._finalPathAndFilename = None
    self._finalPath = None
    self._finalFilename = None
    self._cancelled = False

  def isCancelled(self):
    return self._cancelled

  def update(self, path=None, addPath=None, addPaths=None, filename=None, addPart=None, addParts=None):
    if path is not None:
      self._finalPath = path
    if addPaths is not None:
      self._paths += addPaths
    if addPath is not None:
      self._paths += [addPath]
    if filename is not None:
      self._finalFilename = filename
    if addParts is not None:
      self._parts += addParts
    if addPart is not None:
      self._parts += [addPart]
    return self

  def byDialog(self, dialog, resultOk, *args, **kwargs):
    d = dialog(*args, **kwargs, defaultDir=self.path(), defaultFile=self.filename())
    if d.ShowModal() != resultOk:
      self._cancelled = True
    else:
      self._finalPathAndFilename = d.GetPath()
    return self

  def filename(self):
    if self._finalPathAndFilename is not None:
      return None
    return self._finalFilename or f"domp-{self._initialProjectionName}-{self._hash}{'-' + '-'.join(self._parts) if self._parts else ''}{'-' + self._addHash if self._addHash else ''}{'.' + self._extension if self._extension else ''}"
  def path(self):
    return os.path.expanduser(self._finalPath or os.path.join(*self._paths))
  def pathAndFilename(self):
    if self._finalPathAndFilename is not None:
      return self._finalPathAndFilename
    return os.path.join(self.path(), self.filename())
  
  def apply(self, f):
    s = f(self)
    if s is None:
      self._cancelled = True
      s = self
    os.makedirs(s.path(), exist_ok=True)
    return s

  def removeExisting(self):
    if self._cancelled:
      return
    pathAndFilename = self.pathAndFilename()
    if os.path.exists(pathAndFilename):
      os.unlink(pathAndFilename)
    return pathAndFilename
  def byTmpFile(self, fileNameTmp, move=True):
    if self._cancelled:
      return
    method = os.replace if move else shutil.copy2
    method(fileNameTmp, self.removeExisting())
