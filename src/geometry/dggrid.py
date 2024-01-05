import os
import shapely
import subprocess

class DGGRIDCell:
  def __init__(self, id):
    self.id = id
    self.centre = None
    self.polygon = None
    self.neighbours = None
    self._isHexagon = None

  def isHexagon(self):
    if self._isHexagon is not None:
      return self._isHexagon
    if self.polygon:
      self._isHexagon = len(self.polygon.exterior.coords) - 1 == 6
    return self._isHexagon

class DGGRIDStats:
  def __init__(self, earthRadius, statsForResolution):
    self.earthRadius = earthRadius
    self.__statsForResolution = statsForResolution

  def __getStatsForResolution(self, resolution=None):
    if resolution is None:
      resolution = max(self.__statsForResolution.keys())
    if resolution not in self.__statsForResolution:
      raise Exception('Stats for this resolution do not exist')
    return self.__statsForResolution[resolution]

  def numberOfCells(self, **kargs):
    return self.__getStatsForResolution(**kargs)['numberOfCells']
  def typicalArea(self, **kargs): # m^2
    return self.__getStatsForResolution(**kargs)['typicalArea'] * 1e6
  def typicalDistance(self, **kargs): # m
    return self.__getStatsForResolution(**kargs)['typicalDistance'] * 1e3

class DGGRID:
  def __init__(self, executable='DGGRID/build/src/apps/dggrid/dggrid', tmpWorkingDir='.dggrid', removeTmpWorkingDirAfterUse=True):
    self.__executable = executable
    self.__tmpWorkingDir = tmpWorkingDir
    self.__removeTmpWorkingDirAfterUse = removeTmpWorkingDirAfterUse

  def __run(self, parameters):
    metaFile = 'info.meta'
    if not os.path.exists(self.__tmpWorkingDir):
      os.mkdir(self.__tmpWorkingDir)
    with open(os.path.join(self.__tmpWorkingDir, metaFile), 'wt') as f:
      f.writelines([f"{k:<36}{v}\n" for k, v in parameters.items()])
    output = subprocess.check_output([os.path.abspath(self.__executable), metaFile], cwd=self.__tmpWorkingDir)
    return output.decode('utf-8')

  def __cleanup(self):
    if self.__removeTmpWorkingDirAfterUse:
      for filename in os.listdir(self.__tmpWorkingDir):
        os.remove(os.path.join(self.__tmpWorkingDir, filename))
      os.rmdir(self.__tmpWorkingDir)

  def __parameters(self, operation, dggs='ISEA3H', aperture=4, topology='HEXAGON', proj='ISEA', resolution=9, azimuth0=0, lon0=11.25, lat0=58.28252559, centresFilename=None, polygonsFilename=None, neighboursFilename=None):
    parameters = {
      'dggrid_operation': operation,
      'dggs_aperture': aperture,
      'dggs_proj': proj,
      'dggs_res_spec': resolution,
      'dggs_topology': topology,
      'dggs_type': dggs,
      'dggs_vert0_azimuth': azimuth0,
      'dggs_vert0_lon': lon0,
      'dggs_vert0_lat': lat0,
      'longitude_wrap_mode': 'UNWRAP_EAST',
      'proj_datum': 'WGS84_AUTHALIC_SPHERE',
    }
    if centresFilename is not None:
      parameters = {
        **parameters,
        'point_output_file_name': centresFilename,
        'point_output_type': 'AIGEN',
      }
    if polygonsFilename is not None:
      parameters = {
        **parameters,
        'cell_output_file_name': polygonsFilename,
        'cell_output_type': 'AIGEN',
      }
    if neighboursFilename is not None:
      parameters = {
        **parameters,
        'neighbor_output_file_name': neighboursFilename,
        'neighbor_output_type': 'TEXT',
      }
    return parameters

  def stats(self, **kwargs):
    ## run
    parameters = self.__parameters('OUTPUT_STATS', **kwargs)
    output = self.__run(parameters)
    ## cleanup
    self.__cleanup()
    ## parse output
    earthRadius = None
    statsForResolution = {}
    labelEarthRadius = 'Earth Radius:'
    statsActive = False
    for line in output.split('\n'):
      if line.startswith(labelEarthRadius):
        earthRadius = float(line.removeprefix(labelEarthRadius).strip().replace(',', ''))
      if len(line.strip()) == 0:
        statsActive = False
      if statsActive:
        xs = [x.replace(',', '') for x in line.split(' ') if len(x) > 0]
        statsForResolution[int(xs[0])] = {
          'numberOfCells': int(xs[1]),
          'typicalArea': float(xs[2]),
          'typicalDistance': float(xs[3]),
        }
      if line.startswith('Res'):
        if [x for x in line.split(' ') if len(x) > 0] != ['Res', '#', 'Cells', 'Area', '(km^2)', 'CLS', '(km)']:
          raise Exception('Unexpected stats format')
        statsActive = True
    ## prepare result
    stats = DGGRIDStats(earthRadius, statsForResolution)
    return stats, output

  def generate(self, loadCentres=True, loadPolygons=True, loadNeighbours=True, **kwargs):
    ## run
    centresFilename = 'centres'
    polygonsFilename = 'polygons'
    neighboursFilename = 'neighbours'
    parameters = self.__parameters('GENERATE_GRID', **kwargs, centresFilename=centresFilename if loadCentres and not loadPolygons else None, polygonsFilename=polygonsFilename if loadPolygons else None, neighboursFilename=neighboursFilename if loadNeighbours else None)
    output = self.__run(parameters)
    ## parse output
    cells = {}
    def makeCell(id):
      if id not in cells:
        cells[id] = DGGRIDCell(id)
    errorDetected = False
    # centres
    if loadCentres and not loadPolygons:
      with open(os.path.join(self.__tmpWorkingDir, centresFilename + '.gen')) as f:
        while True:
          line = f.readline()
          if not line:
            errorDetected = True
            break
          if line == 'END\n':
            break
          data = line.strip().split(' ')
          id = int(data[0])
          makeCell(id)
          cells[id].centre = shapely.Point(float(data[1]), float(data[2]))
      if errorDetected:
        raise Exception('The DGGRID centres output file was erroneous or incomplete')
    # polygons
    if loadPolygons:
      isInsideCell = False
      polygonCoordinates = []
      with open(os.path.join(self.__tmpWorkingDir, polygonsFilename + '.gen')) as f:
        while True:
          line = f.readline()
          if not line:
            errorDetected = True
            break
          if not isInsideCell and line == 'END\n':
            break
          data = line.strip().split(' ')
          if not isInsideCell:
            isInsideCell = True
            polygonCoordinates = []
            id = int(data[0])
            makeCell(id)
            cells[id].centre = shapely.Point(float(data[1]), float(data[2]))
          elif data == ['END']:
            isInsideCell = False
            cells[id].polygon = shapely.Polygon(polygonCoordinates)
          else:
            polygonCoordinates.append((float(data[0]), float(data[1])))
      if errorDetected:
        raise Exception('The DGGRID polygons output file was erroneous or incomplete')
    # neighbours
    if loadNeighbours:
      with open(os.path.join(self.__tmpWorkingDir, neighboursFilename + '.nbr')) as f:
        while True:
          line = f.readline()
          if not line:
            break
          data = line.strip().split(' ')
          id = int(data[0])
          makeCell(id)
          cells[id].neighbours = [int(x) for x in data[1:]]
    ## cleanup
    self.__cleanup()
    ## prepare result
    return cells, output

# USAGE
#
# dggrid = DGGRID(executable='DGGRID/build/src/apps/dggrid/dggrid')
#
# stats, _ = dggrid.stats(resolution=6)
# print(stats.numberOfCells())
# print(stats.typicalArea())
# print(stats.typicalDistance())
#
# cells, _ = dggrid.generate(resolution=6)
# print(cells[642].centre)
# print(cells[642].polygon)
# print(cells[642].neighbours)
# print(cells[642].isHexagon)
