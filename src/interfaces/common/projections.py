import math

from src.geometry.common import Common
from src.geometry.geo import Geo
from src.geometry.strategy import strategyForScale

class Projection:
  def __init__(self, name=None, srid=None, scale=None, transform=None, canBeOptimized=False):
    self.name = name
    self.srid = srid
    self.transform = transform
    self.canBeOptimized = canBeOptimized
    self.scale = scale(self) if callable(scale) else scale if scale or (transform is None and srid is None) else strategyForScale()(self)

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

class PROJECTION:
  allProjections = [] # initialized below
  relevantProjections = [] # initialized below
  canBeOptimizedProjections = [] # initialized below

  unprojected = Projection(
    name='unprojected',
    srid=None,
    scale=1,
    canBeOptimized=True,
  )
  Aitoff = Projection(
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
  )
  Eckert_II = Projection(
    name='Eckert II',
    srid='ESRI:53014',
  )
  Eckert_III = Projection(
    name='Eckert III',
    srid='ESRI:53013',
  )
  Eckert_IV = Projection(
    name='Eckert IV',
    srid='ESRI:53012',
  )
  Eckert_V = Projection(
    name='Eckert V',
    srid='ESRI:53011',
  )
  Eckert_VI = Projection(
    name='Eckert VI',
    srid='ESRI:53010',
  )
  # Gall_Peters = Projection( # SRID unclear
  #   name='Gall-Peters',
  #   srid='???',
  # )
  # Hammer_Aitoff = Projection( # ProjError: Input is not a transformation
  #   name='Hammer-Aitoff',
  #   srid='ESRI:53044',
  # )
  Mercator = Projection(
    name='Mercator',
    srid='EPSG:3395',
  )
  Mollweide = Projection(
    name='Mollweide',
    srid='ESRI:53009',
  )
  Natural_Earth = Projection(
    name='Natural Earth',
    srid='ESRI:53077',
  )
  Natural_Earth_II = Projection(
    name='Natural Earth II',
    srid='ESRI:53078',
  )
  Peirce_Quincuncial_North_Pole = Projection(
    name='Peirce Quincuncial North Pole',
    srid='ESRI:54090',
    scale=strategyForScale(corners=[[-180, 0], [-90, 0], [0, 0], [90, 0]], horizontal=True, vertical=True, diagonalUp=True, diagonalDown=True, degreeHorizontal=360, degreeVertical=360, degreeDiagonalUp=360, degreeDiagonalDown=360, epsilon=0),
  )
  Robinson = Projection(
    name='Robinson',
    srid='ESRI:53030',
  )
  Sinusoidal = Projection(
    name='Sinusoidal',
    srid='ESRI:53008',
    transform=lambda x, y: (math.cos(Common.deg2rad(y)) * x * Geo.radiusEarth / 360, y * Geo.radiusEarth / 360),
    canBeOptimized=True,
  )
  # Sinusoidal_ORIGINAL = Projection(
  #   name='Sinusoidal ORIGINAL',
  #   srid='ESRI:53008',
  # )
  Winkel_Tripel = Projection(
    name='Winkel-Tripel',
    srid='ESRI:53042',
  )

PROJECTION.allProjections = [getattr(PROJECTION, attr) for attr in dir(PROJECTION) if isinstance(getattr(PROJECTION, attr), Projection)]
PROJECTION.relevantProjections = [proj for proj in PROJECTION.allProjections if proj not in [PROJECTION.unprojected]]
PROJECTION.canBeOptimizedProjections = [proj for proj in PROJECTION.allProjections if proj.canBeOptimized]
