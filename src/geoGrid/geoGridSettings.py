import shapely

from src.geoGrid.geoGrid import *
from src.mechanics.force import *
from src.mechanics.potential.potentialArea import *
from src.mechanics.potential.potentialDistance import *

# F = - G m1 m2 / r^2
# U = F * r
# E = m1 * U
#
# konservatives Kraftfeld
# F = - nabla U(r) = - del U / del x * e_x
# U = - \int F(r) dr

class GeoGridSettings:
  def __init__(self, resolution=4):
    self.resolution = resolution
    self._dampingFactor = .95
    self._typicalDistance = None
    self._typicalArea = None
    self._forceFactor = None
    self.potentials = [PotentialArea(self), PotentialDistance(self)]

  def updateGridStats(self, gridStats):
    self._typicalDistance = gridStats.at[self.resolution, 'CLS (km)'] * 10**3
    self._typicalArea = gridStats.at[self.resolution, 'Area (km^2)'] * 10**6
    self._forceFactor = (1 - self._dampingFactor) * self._typicalDistance
