from datetime import datetime, timezone
import json

from src.app.common import APP_NAME, APP_URL
from src.common.database import Database
from src.common.paths import projDb, srsDb

class GeoGridProjectionTIN:
  @staticmethod
  def computeTIN(geoGrid, info):
    # collect vertices and triangles
    id2ToIndex = {}
    vertices = []
    triangles = []
    for id2, cell in geoGrid.cells().items():
      id2ToIndex[id2] = len(vertices)
      vertices.append([cell._centreOriginal.x, cell._centreOriginal.y, cell.x, cell.y])
    for id2, cell in geoGrid.cells().items():
      nLast = None
      if len(cell._neighbours) != (6 if cell._isHexagon else 5):
        continue
      for n in cell._neighbours + [cell._neighbours[0]]:
        if n not in id2ToIndex:
          continue
        if nLast is not None and nLast != n:
          triangle = sorted([id2ToIndex[id2], id2ToIndex[nLast], id2ToIndex[n]])
          if triangle not in triangles:
            triangles.append(triangle)
        nLast = n
    # description
    description = json.dumps({
      'jsonSettingsIncludingTransient': geoGrid.settings().toJSON(includeTransient=True),
      'info': {**info, 'jsonSettings': None},
    })
    # result
    return {
      'file_type': 'triangulation_file',
      'format_version': '1.1',
      'name': 'Discretized Optimized Map Projection #' + info['hash'],
      'version': '1.0',
      'publication_date': datetime.now(timezone.utc).isoformat()[:-13] + 'Z',
      'license': 'Creative Commons Attribution 4.0 International',
      'description': description,
      'authority': {
        'name': f'produced by {APP_NAME}'.replace('\n', ' '),
        'url': APP_URL,
      },
      'links': [
        {
          'href': APP_URL,
          'rel': 'source',
          'type': 'text/html',
          'title': 'GitHub source',
        },
        {
          'href': info['filenameSettings'],
          'rel': 'metadata',
          'type': 'text/json',
          'title': 'settings',
        },
      ],
      'extent': {
        'type': 'bbox',
        'name': 'world',
        'parameters': {
          'bbox': [-180, -90, 180, 90],
        },
      },
      'input_crs': 'EPSG:4326',
      'output_crs': info['dompCRS'],
      'fallback_strategy': 'nearest_side',
      'transformed_components': ['horizontal'],
      'vertices_columns': ['source_x', 'source_y', 'target_x', 'target_y'],
      'triangles_columns': ['idx_vertex1', 'idx_vertex2', 'idx_vertex3'],
      'vertices': vertices,
      'triangles': triangles,
    }

  INSTALLED_PROJ = 'INSTALLED_PROJ'
  INSTALLED_QGIS = 'INSTALLED_QGIS'
  INSTALLED_FULL = 'INSTALLED_FULL'
  INSTALLED_PARTLY = 'INSTALLED_PARTLY'
  INSTALLED_NOT = 'INSTALLED_NOT'

  @staticmethod
  def isTINInstalled(appSettings, data=None, hash=None):
    hash = hash or json.loads(data['description'])['info']['hash']
    def determineStatus(tests):
      if len(tests) == 0:
        return GeoGridProjectionTIN.INSTALLED_NOT
      elif all(tests):
        return GeoGridProjectionTIN.INSTALLED_FULL
      return GeoGridProjectionTIN.INSTALLED_PARTLY
    installed = {}
    with Database(projDb(appSettings)) as db:
      projDbInstallled = [] if not db else [
        db.exists('conversion_table', {'auth_name': 'DOMP', 'code': f"{hash}-conv"}),
        db.exists('projected_crs', {'auth_name': 'DOMP', 'code': hash}),
        db.exists('usage', {'auth_name': 'DOMP', 'code': f"{hash}_USAGE"}),
        db.exists('other_transformation', {'auth_name': 'PROJ', 'code': f"WGS84_TO_DOMP-{hash}"}),
        db.exists('usage', {'auth_name': 'PROJ', 'code': f"WGS84_TO_DOMP-{hash}_USAGE"}),
      ]
      installed[GeoGridProjectionTIN.INSTALLED_PROJ] = determineStatus(projDbInstallled)
    with Database(srsDb(appSettings)) as db:
      srsDbInstallled = [] if not db else [
        db.exists('tbl_projection', {'acronym': 'domp'}),
        db.exists('tbl_srs', {'auth_name': 'DOMP', 'auth_id': hash}),
      ]
      installed[GeoGridProjectionTIN.INSTALLED_QGIS] = determineStatus(srsDbInstallled)
    return installed

  def collectTINInstalled(appSettings):
    installedHashes = set()
    with Database(projDb(appSettings)) as db:
      if db is not None:
        for code, in db.select('conversion_table', ['code'], {'auth_name': 'DOMP'}):
          if str(code).endswith('-conv'):
            installedHashes.add(code.replace('-conv', ''))
        for code, in db.select('projected_crs', ['code'], {'auth_name': 'DOMP'}):
          installedHashes.add(str(code))
        for code, in db.select('usage', ['code'], {'auth_name': 'DOMP'}):
          if str(code).startswith('WGS84_TO_DOMP-') and str(code).endswith('_USAGE'):
            installedHashes.add(code.replace('WGS84_TO_DOMP-', '').replace('_USAGE', ''))
          elif str(code).endswith('_USAGE'):
            installedHashes.add(code.replace('_USAGE', ''))
        for code, in db.select('other_transformation', ['target_crs_code'], {'target_crs_auth_name': 'DOMP'}):
          installedHashes.add(str(code))
    with Database(srsDb(appSettings)) as db:
      if db is not None:
        for code, in db.select('tbl_srs', ['auth_id'], {'auth_name': 'DOMP'}):
          installedHashes.add(str(code))
    return dict((hash, GeoGridProjectionTIN.isTINInstalled(appSettings, hash=hash)) for hash in installedHashes)

  @staticmethod
  def uninstallTIN(appSettings, data=None, hash=None):
    hash = hash or json.loads(data['description'])['info']['hash']
    with Database(projDb(appSettings)) as db:
      if db is not None:
        db.delete('conversion_table', {'auth_name': 'DOMP', 'code': f"{hash}-conv"})
        db.delete('projected_crs', {'auth_name': 'DOMP', 'code': hash})
        db.delete('usage', {'auth_name': 'DOMP', 'code': f"{hash}_USAGE"})
        db.delete('other_transformation', {'auth_name': 'PROJ', 'code': f"WGS84_TO_DOMP-{hash}"})
        db.delete('usage', {'auth_name': 'PROJ', 'code': f"WGS84_TO_DOMP-{hash}_USAGE"})
        db.commit()
    with Database(srsDb(appSettings)) as db:
      if db is not None:
        db.delete('tbl_srs', {'auth_name': 'DOMP', 'auth_id': hash})
        db.commit()

  @staticmethod
  def uninstallAllTIN(appSettings):
    with Database(projDb(appSettings)) as db:
      if db is not None:
        db.delete('conversion_table', {'auth_name': 'DOMP'})
        db.delete('projected_crs', {'auth_name': 'DOMP'})
        db.delete('usage', {'auth_name': 'DOMP'})
        db.delete('other_transformation', {'target_crs_auth_name': 'DOMP'})
        db.delete('usage', {'code': Database.like('WGS84_TO_DOMP-%')})
        db.commit()
    with Database(srsDb(appSettings)) as db:
      if db is not None:
        db.delete('tbl_projection', {'acronym': 'domp'})
        db.delete('tbl_srs', {'auth_name': 'DOMP'})
        db.commit()

  @staticmethod
  def installTIN(appSettings, filenameTIN, data):
    hash = json.loads(data['description'])['info']['hash']
    # delete potentially existing
    GeoGridProjectionTIN.uninstallTIN(appSettings, hash=hash)
    # insert new
    try:
      with Database(projDb(appSettings)) as db:
        if db is None:
          return None
        db.insert('conversion_table', {
          'auth_name': 'DOMP', 'code': f"{hash}-conv",
          'name': f"Wrong conversion for the Discretized Optimized Map Projection #{hash}",
          'description': f"Wrong conversion for the Discretized Optimized Map Projection #{hash}",
          'method_auth_name': 'EPSG', 'method_code': '1024',
          'param1_auth_name': 'EPSG', 'param1_code': '8801', 'param1_value': '0.0', 'param1_uom_auth_name': 'EPSG', 'param1_uom_code': '9102',
          'param2_auth_name': 'EPSG', 'param2_code': '8802', 'param2_value': '0.0', 'param2_uom_auth_name': 'EPSG', 'param2_uom_code': '9102',
          'param3_auth_name': 'EPSG', 'param3_code': '8806', 'param3_value': '0.0', 'param3_uom_auth_name': 'EPSG', 'param3_uom_code': '9001',
          'param4_auth_name': 'EPSG', 'param4_code': '8807', 'param4_value': '0.0', 'param4_uom_auth_name': 'EPSG', 'param4_uom_code': '9001',
          'deprecated': 0,
        })
        db.insert('projected_crs', {
          'auth_name': 'DOMP', 'code': hash, 'name': f"Discretized Optimized Map Projection #{hash}",
          'description': f"Discretized Optimized Map Projection #{hash}",
          'coordinate_system_auth_name': 'EPSG', 'coordinate_system_code': '4499',
          'geodetic_crs_auth_name': 'EPSG', 'geodetic_crs_code': '4030',
          'conversion_auth_name': 'DOMP', 'conversion_code': f"{hash}-conv",
          'deprecated': 0,
        })
        db.insert('usage', {
          'auth_name': 'DOMP', 'code': f"{hash}_USAGE",
          'object_table_name': 'projected_crs', 'object_auth_name': 'DOMP', 'object_code': hash,
          'extent_auth_name': 'EPSG', 'extent_code': '1262',
          'scope_auth_name': 'EPSG', 'scope_code': '1098',
        })
        db.insert('other_transformation', {
          'auth_name': 'PROJ', 'code': f"WGS84_TO_DOMP-{hash}", 'name': f"WGS84 to DOMP-{hash}",
          'description': f"Transformation for the Discretized Optimized Map Projection #{hash}",
          'method_auth_name': 'PROJ', 'method_code': 'PROJString', 'method_name': f"+proj=pipeline +step +proj=axisswap +order=2,1 +step +proj=tinshift +file='{filenameTIN}'",
          'source_crs_auth_name': 'EPSG', 'source_crs_code': '4326',
          'target_crs_auth_name': 'DOMP', 'target_crs_code': hash,
          'accuracy': 0.01,
          'deprecated': 0,
        })
        db.insert('usage', {
          'auth_name': 'PROJ', 'code': f"WGS84_TO_DOMP-{hash}_USAGE",
          'object_table_name': 'other_transformation', 'object_auth_name': 'PROJ', 'object_code': f"WGS84_TO_DOMP-{hash}",
          'extent_auth_name': 'EPSG', 'extent_code': '1262',
          'scope_auth_name': 'EPSG', 'scope_code': '1098',
        })
        db.commit()
      with Database(srsDb(appSettings)) as db:
        if db is not None:
          db.insert('tbl_projection', {
            'acronym': 'domp',
            'name': 'Discretized Optimized Map Projection',
          }, ignoreIfExists=True)
          db.insert('tbl_srs', {
              'description': f"Discretized Optimized Map Projection #{hash}",
              'projection_acronym': 'domp', 'ellipsoid_acronym': 'WGS84',
              'parameters': '+proj=merc +lon_0=0 +k=1 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs',
              'srid': hash,
              'auth_name': 'DOMP', 'auth_id': hash,
              'is_geo': 0,
              'deprecated': 0,
          }, ifNotExists={
              'auth_name': 'DOMP', 'auth_id': hash,
          })
          db.commit()
      return True
    except:
      return False
