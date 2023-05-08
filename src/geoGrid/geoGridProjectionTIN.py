from datetime import datetime, timezone
import json
import sqlite3
import traceback

from src.app.common import APP_NAME, APP_URL
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

  @staticmethod
  def installTIN(appSettings, filenameTIN, data):
    info = json.loads(data['description'])['info']
    filenameProjDb = projDb(appSettings)
    try:
      if not filenameProjDb:
        return None
      else:
        connection = sqlite3.connect(filenameProjDb)
        cursor = connection.cursor()
        cursor.execute(f'''
          INSERT INTO conversion_table (
            auth_name, code, name,
            description,
            method_auth_name, method_code,
            param1_auth_name, param1_code, param1_value, param1_uom_auth_name, param1_uom_code,
            param2_auth_name, param2_code, param2_value, param2_uom_auth_name, param2_uom_code,
            param3_auth_name, param3_code, param3_value, param3_uom_auth_name, param3_uom_code,
            param4_auth_name, param4_code, param4_value, param4_uom_auth_name, param4_uom_code,
            deprecated
          ) VALUES (
            'DOMP', '{info['hash']}-conv', 'Wrong conversion for the Discretized Optimized Map Projection #{info['hash']}',
            'Wrong conversion for the Discretized Optimized Map Projection #{info['hash']}',
            'EPSG', '1024',
            'EPSG', '8801', '0.0', 'EPSG', '9102',
            'EPSG', '8802', '0.0', 'EPSG', '9102',
            'EPSG', '8806', '0.0', 'EPSG', '9001',
            'EPSG', '8807', '0.0', 'EPSG', '9001',
            0
          );
        ''')
        cursor.execute(f'''
          INSERT INTO projected_crs (
            auth_name, code, name,
            description,
            coordinate_system_auth_name, coordinate_system_code,
            geodetic_crs_auth_name, geodetic_crs_code,
            conversion_auth_name, conversion_code,
            deprecated
          ) VALUES (
            'DOMP', '{info['hash']}', 'Discretized Optimized Map Projection #{info['hash']}',
            'Discretized Optimized Map Projection #{info['hash']}',
            'EPSG', '4499',
            'EPSG', '4030',
            'DOMP', '{info['hash']}-conv',
            0
          );
        ''')
        cursor.execute(f'''
          INSERT INTO usage (
            auth_name, code,
            object_table_name, object_auth_name, object_code,
            extent_auth_name, extent_code,
            scope_auth_name, scope_code
          ) VALUES (
            'DOMP', '{info['hash']}_USAGE',
            'projected_crs', 'DOMP', '{info['hash']}',
            'EPSG', '1262',
            'EPSG', '1098'
          );
        ''')
        cursor.execute(f'''
          INSERT INTO other_transformation (
            auth_name, code, name,
            description,
            method_auth_name, method_code, method_name,
            source_crs_auth_name, source_crs_code,
            target_crs_auth_name, target_crs_code,
            accuracy,
            deprecated
          ) VALUES (
            'PROJ', 'WGS84_TO_DOMP-{info['hash']}', 'WGS84 to DOMP-{info['hash']}',
            'Transformation for the Discretized Optimized Map Projection #{info['hash']}',
            'PROJ', 'PROJString', '+proj=pipeline +step +proj=axisswap +order=2,1 +step +proj=tinshift +file="{filenameTIN}"',
            'EPSG', '4326',
            'DOMP', '{info['hash']}',
            0.01,
            0
          );
        ''')
        cursor.execute(f'''
          INSERT INTO usage (
            auth_name, code,
            object_table_name, object_auth_name, object_code,
            extent_auth_name, extent_code,
            scope_auth_name, scope_code
          ) VALUES (
            'PROJ', 'WGS84_TO_DOMP-{info['hash']}_USAGE',
            'other_transformation', 'PROJ', 'WGS84_TO_DOMP-{info['hash']}',
            'EPSG', '1262',
            'EPSG', '1098'
          );
        ''')
        connection.commit()
      filenameSrsDb = srsDb(appSettings)
      if filenameSrsDb:
        connection = sqlite3.connect(filenameSrsDb)
        cursor = connection.cursor()
        cursor.execute(f'''
          INSERT INTO tbl_projection (
            acronym, name
          ) VALUES (
            'domp', 'Discretized Optimized Map Projection'
          );
        ''')
        cursor.execute(f'''
          INSERT INTO tbl_srs (
            description,
            projection_acronym, ellipsoid_acronym,
            parameters,
            srid,
            auth_name, auth_id,
            is_geo,
            deprecated
          ) VALUES (
            'Discretized Optimized Map Projection #{info['hash']}',
            'domp', 'WGS84',
            '+proj=merc +lon_0=0 +k=1 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs',
            '{info['hash']}',
            'DOMP', '{info['hash']}',
            0,
            0
          );
        ''')
        connection.commit()
        connection.close()
    except:
      traceback.print_exc()
      return False
    return True