from src.geoGrid.geoGridWeight import GeoGridWeight
from src.mechanics.potential.potentialShape import PotentialShape

class PotentialOrientation(PotentialShape):
  kind = 'ORIENTATION'
  defaultWeight = GeoGridWeight(active=True, weightLand=.3, weightOceanActive=False, weightOcean=0.1, distanceTransitionStart=100000, distanceTransitionEnd=800000)
  
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs, enforceNorth=True)
