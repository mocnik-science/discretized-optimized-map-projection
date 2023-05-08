import os

def guessProjQGIS():
  qgisApp = '/Applications/QGIS.app'
  if os.path.exists(qgisApp):
    return qgisApp
  return ''

def projDb(appSettings):
  if 'filenameProjQGIS' not in appSettings:
    return None
  filenameProjDb = os.path.join(appSettings['filenameProjQGIS'], 'Contents', 'Resources', 'proj', 'proj.db')
  if appSettings['filenameProjQGIS'].endswith('.app') and os.path.exists(filenameProjDb):
    return filenameProjDb
  if appSettings['filenameProjQGIS'] == 'proj.db' or appSettings['filenameProjQGIS'].endswith('/proj.db'):
    return appSettings['filenameProjQGIS']
  return None

def srsDb(appSettings):
  if 'filenameProjQGIS' not in appSettings:
    return None
  filenameSrsDb = os.path.join(appSettings['filenameProjQGIS'], 'Contents', 'Resources', 'resources', 'srs.db')
  if appSettings['filenameProjQGIS'].endswith('.app') and os.path.exists(filenameSrsDb):
    return filenameSrsDb
  return None
