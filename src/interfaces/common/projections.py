import math
from pyproj import CRS, Transformer
from scipy.optimize import newton

from src.geometry.common import Common
from src.geometry.geo import Geo
from src.geometry.strategy import strategyForScale

class Projection:
  def __init__(self, name=None, srid=None, scale=None, transformRad=None, transformDeg=None, canBeOptimized=False):
    self.sortBy = [name]
    self.name = name
    self.srid = srid
    if transformRad:
      self.transform = lambda x, y: self.__multiplyByRadiusEarth(transformRad(Common.deg2rad(x), Common.deg2rad(y)))
    elif transformDeg:
      self.transform = lambda x, y: self.__multiplyByRadiusEarth(transformDeg(x, y))
    elif srid:
      self.transform = Transformer.from_crs(CRS('EPSG:4326'), CRS(srid), always_xy=True).transform
      self.name += ' (PROJ)'
    else:
      self.transform = None
    self.canBeOptimized = canBeOptimized
    self.scale = scale(self) if callable(scale) else scale if scale or (self.transform is None and srid is None) else strategyForScale()(self)
    self.sortBy += [self.name]

  def __multiplyByRadiusEarth(self, xy):
    return (Geo.radiusEarth * xy[0], Geo.radiusEarth * xy[1])

  def toJSON(self):
    return {
      'name': self.name,
      'srid': self.srid,
      'scale': self.scale,
      'canBeOptimized': self.canBeOptimized,
    }
  
  @staticmethod
  def fromJSON(self, data):
    return Projection(**data)

  def __lt__(self, obj):
    return self.sortBy < obj.sortBy
  def __gt__(self, obj):
    return self.sortBy > obj.sortBy
  def __le__(self, obj):
    return self.sortBy <= obj.sortBy
  def __ge__(self, obj):
    return self.sortBy >= obj.sortBy
  def __eq__(self, obj):
    return self.sortBy == obj.sortBy

def aitoff_transformRad(l, t):
  k = 1 / Common.sinc(math.acos(math.cos(t) * math.cos(l / 2)))
  return (2 * math.cos(t) * math.sin(l / 2) * k, math.sin(t) * k)

def eckert_IV_transformRad(l, t):
  k = (2 + Common._pi_2) * math.sin(t)
  p = newton(lambda x: x + math.sin(x) * math.cos(x) + 2 * math.sin(x) - k, t)
  return (2 * l * (1 + math.cos(p)) / math.sqrt(4 * Common._pi + Common._pi__2), 2 * Common._sqrtPi * math.sin(p) / math.sqrt(4 + Common._pi))

def eckert_VI_transformRad(l, t):
  k = (1 + Common._pi_2) * math.sin(t)
  p = newton(lambda x: x + math.sin(x) - k, t)
  return (l * (1 + math.cos(p)) / math.sqrt(2 + Common._pi), 2 * p / math.sqrt(2 + Common._pi))

def hammer_aitoff_transformRad(l, t):
  k = 1 / math.sqrt(1 + math.cos(t) * math.cos(l / 2))
  return (2 * Common._sqrt2 * math.cos(t) * math.sin(l / 2) * k, Common._sqrt2 * math.sin(t) * k)

def rectangular_Projection_transformRad(l, t, standardParallels=0):
  return (l * (1 if standardParallels == 0 else math.cos(standardParallels)), t)

def winkel_Tripel_transformRad(l, t):
  (x1, y1) = aitoff_transformRad(l, t)
  (x2, y2) = rectangular_Projection_transformRad(l, t, standardParallels=math.acos(1 / Common._pi_2))
  return ((x1 + x2) / 2, (y1 + y2) / 2)

class PROJECTION:
  allProjections = [] # initialized below
  relevantProjections = [] # initialized below
  canBeOptimizedProjections = [] # initialized below

  unprojected = Projection(
    name='unprojected',
    transformRad=rectangular_Projection_transformRad,
    scale=1,
    canBeOptimized=True,
  )
  Aitoff = Projection(
    name='Aitoff',
    srid='ESRI:53043',
    transformRad=aitoff_transformRad,
    canBeOptimized=True,
  )
  Aitoff_PROJ = Projection(
    name='Aitoff',
    srid='ESRI:53043',
  )
  # Albers = Projection( # Maßstab unklar
  #   name='Albers',
  #   srid='EPSG:5072',
  # )
  # Bonne = Projection( # Maßstab unklar
  #   name='Bonne',
  #   srid='ESRI:53024',
  # )
  Eckert_I = Projection(
    name='Eckert I',
    srid='ESRI:53015',
    transformRad=lambda l, t: (math.sqrt(1 / (3 * Common._pi_8)) * l * (1 - abs(t) / Common._pi), math.sqrt(1 / (3 * Common._pi_8)) * t),
    canBeOptimized=True,
  )
  Eckert_I_PROJ = Projection(
    name='Eckert I',
    srid='ESRI:53015',
  )
  Eckert_II = Projection(
    name='Eckert II',
    srid='ESRI:53014',
    transformRad=lambda l, t: (2 * l * math.sqrt((4 - 3 * math.sin(abs(t))) / (6 * Common._pi)), math.sqrt(2 * Common._pi / 3) * (2 - math.sqrt(4 - 3 * math.sin(abs(t)))) * Common.sign(t)),
    canBeOptimized=True,
  )
  Eckert_II_PROJ = Projection(
    name='Eckert II',
    srid='ESRI:53014',
  )
  Eckert_III = Projection(
    name='Eckert III',
    srid='ESRI:53013',
    transformRad=lambda l, t: (2 * l * (1 + math.sqrt(1 - (t / Common._pi_2)**2)) / math.sqrt(4 * Common._pi + Common._pi__2), 4 * t / math.sqrt(4 * Common._pi + Common._pi__2)),
    canBeOptimized=True,
  )
  Eckert_III_PROJ = Projection(
    name='Eckert III',
    srid='ESRI:53013',
  )
  Eckert_IV = Projection(
    name='Eckert IV',
    srid='ESRI:53012',
    transformRad=eckert_IV_transformRad,
    canBeOptimized=True,
  )
  Eckert_IV_PROJ = Projection(
    name='Eckert IV',
    srid='ESRI:53012',
  )
  Eckert_V = Projection(
    name='Eckert V',
    srid='ESRI:53011',
    transformRad=lambda l, t: (l * (1 + math.cos(t)) / math.sqrt(2 + Common._pi), 2 * t / math.sqrt(2 + Common._pi)),
    canBeOptimized=True,
  )
  Eckert_V_PROJ = Projection(
    name='Eckert V',
    srid='ESRI:53011',
  )
  Eckert_VI = Projection(
    name='Eckert VI',
    srid='ESRI:53010',
    transformRad=eckert_VI_transformRad,
    canBeOptimized=True,
  )
  Eckert_VI_PROJ = Projection(
    name='Eckert VI',
    srid='ESRI:53010',
  )
  Gall_Peters = Projection(
    name='Gall-Peters',
    srid='unknown',
    transformRad=lambda l, t: (l / Common._sqrt2, Common._sqrt2 * math.sin(t)),
    canBeOptimized=True,
  )
  # Gall_Peters_PROJ = Projection( # SRID unclear
  #   name='Gall-Peters',
  #   srid='unknown',
  # )
  Hammer_Aitoff = Projection(
    name='Hammer-Aitoff',
    srid='ESRI:53044',
    transformRad=hammer_aitoff_transformRad,
    canBeOptimized=True,
  )
  # Hammer_Aitoff_PROJ = Projection( # ProjError: Input is not a transformation
  #   name='Hammer-Aitoff',
  #   srid='ESRI:53044',
  # )
  Mercator = Projection(
    name='Mercator',
    srid='EPSG:3395',
    transformRad=lambda l, t: (l, math.log(math.tan(Common._pi_4 + Common.restrict(t, minValue=-Common._pi_2, maxValue=Common._pi_2, epsilon=1e3 * Common._epsilon) / 2))),
    canBeOptimized=True,
  )
  Mercator_PROJ = Projection(
    name='Mercator',
    srid='EPSG:3395',
  )
  Mollweide = Projection(
    name='Mollweide',
    srid='ESRI:53009',
    transformRad=lambda l, t: (Common._sqrt2 / Common._pi_2 * l * math.cos(t), Common._sqrt2 * math.sin(t)),
    canBeOptimized=True,
  )
  Mollweide_PROJ = Projection(
    name='Mollweide',
    srid='ESRI:53009',
  )
  Natural_Earth = Projection(
    name='Natural Earth',
    srid='ESRI:53077',
    transformRad=lambda l, t: (l * (.870700 - .131979 * t**2 - .013791 * t**4 + .003971 * t**10 - .001529 * t**12), (1.007226 * t + .015085 * t**3 - .044475 * t**7 + .028874 * t**9 - .005916 * t**11)),
    canBeOptimized=True,
  )
  Natural_Earth_PROJ = Projection(
    name='Natural Earth',
    srid='ESRI:53077',
  )
  Natural_Earth_II = Projection(
    name='Natural Earth II',
    srid='ESRI:53078',
    transformRad=lambda l, t: (l * (.84719 - .13063 * t**2 - .04515 * t**12 + .05494 * t**14 - .02326 * t**16 + .00331 * t**18), (1.01183 * t - .02625 * t**9 + .01926 * t**11 - .00396 * t**13)),
    canBeOptimized=True,
  )
  Natural_Earth_II_PROJ = Projection(
    name='Natural Earth II',
    srid='ESRI:53078',
  )
  Peirce_Quincuncial_North_Pole = Projection(
    name='Peirce Quincuncial North Pole',
    srid='ESRI:54090',
    scale=strategyForScale(corners=[[-180, 0], [-90, 0], [0, 0], [90, 0]], horizontal=True, vertical=True, diagonalUp=True, diagonalDown=True, degreeHorizontal=360, degreeVertical=360, degreeDiagonalUp=360, degreeDiagonalDown=360, epsilon=0),
  )
  # Robinson = Projection( # there is no closed-form expression
  #   name='Robinson',
  #   srid='ESRI:53030',
  # )
  Robinson_PROJ = Projection(
    name='Robinson',
    srid='ESRI:53030',
  )
  Sinusoidal = Projection(
    name='Sinusoidal',
    srid='ESRI:53008',
    transformRad=lambda l, t: (l * math.cos(t), t),
    canBeOptimized=True,
  )
  Sinusoidal_PROJ = Projection(
    name='Sinusoidal',
    srid='ESRI:53008',
  )
  Winkel_Tripel = Projection(
    name='Winkel-Tripel',
    srid='ESRI:53042',
    transformRad=winkel_Tripel_transformRad,
    canBeOptimized=True,
  )
  Winkel_Tripel_PROJ = Projection(
    name='Winkel-Tripel',
    srid='ESRI:53042',
  )

PROJECTION.allProjections = sorted([getattr(PROJECTION, attr) for attr in dir(PROJECTION) if isinstance(getattr(PROJECTION, attr), Projection)])
PROJECTION.relevantProjections = sorted([proj for proj in PROJECTION.allProjections if proj not in [PROJECTION.unprojected]])
PROJECTION.canBeOptimizedProjections = sorted([proj for proj in PROJECTION.allProjections if proj.canBeOptimized])
