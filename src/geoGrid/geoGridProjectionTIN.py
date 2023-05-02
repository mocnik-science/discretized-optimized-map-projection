from datetime import datetime, timezone
import json

from src.app.common import APP_NAME, APP_URL

class GeoGridProjectionTIN:
  @staticmethod
  def computeTIN(geoGrid):
    return {
      'file_type': 'triangulation_file',
      'format_version': '1.0',
      'name': 'Individual Discretized Optimized Map Projection',
      'version': '1.0',
      'publication_date': datetime.now(timezone.utc).isoformat()[:-13] + 'Z',
      'license': 'Creative Commons Attribution 4.0 International',
      'description': json.dumps(geoGrid.settings().toJSON(includeTransient=True)),
      'authority': {
        'name': f'produced by {APP_NAME}',
        'url': APP_URL,
      },
      'links': [
        {
          'href': APP_URL,
          'rel': 'source',
          'type': 'text/html',
          'title': 'GitHub source',
        },
      ],
      'fallback_strategy': 'nearest_side',
      'extent': {
        'type': 'bbox',
        'name': 'world',
        'parameters': [-180, -90, 180, 90],
      },
      'input_crs': 'EPSG:4326',
      'output_crs': 'Individual Discretized Optimized Map Projection',
      'transformed_components': 'horizontal',
      'vertices_columns': ['source_x', 'source_y', 'target_x', 'target_y'],
      'triangles_columns': ['idx_vertex1', 'idx_vertex2', 'idx_vertex3'],
      'triangles': [],
      'vertices': [],
    }
