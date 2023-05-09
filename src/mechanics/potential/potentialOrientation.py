from src.mechanics.potential.potentialShape import PotentialShape

class PotentialOrientation(PotentialShape):
  kind = 'ORIENTATION'
  
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs, enforceNorth=True)
