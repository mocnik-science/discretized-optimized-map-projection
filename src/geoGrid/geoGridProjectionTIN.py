from datetime import datetime, timezone
import json

from src.app.common import APP_NAME, APP_URL

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
    # settings
    settingsJson = json.dumps(geoGrid.settings().toJSON(includeTransient=True))
    # result
    return {
      'file_type': 'triangulation_file',
      'format_version': '1.1',
      'name': 'Discretized Optimized Map Projection #' + info['hash'],
      'version': '1.0',
      'publication_date': datetime.now(timezone.utc).isoformat()[:-13] + 'Z',
      'license': 'Creative Commons Attribution 4.0 International',
      'description': settingsJson,
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
  def installTIN(info, data):
    pass
