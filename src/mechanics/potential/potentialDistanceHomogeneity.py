import math
import sys

from src.geometry.cartesian import Cartesian, Point
from src.geometry.common import Common
from src.geoGrid.geoGridWeight import GeoGridWeight
from src.mechanics.force import Force
from src.mechanics.potential.potential import Potential

class PotentialDistanceHomogeneity(Potential):
  kind = 'DISTANCE_HOMOGENEITY'
  defaultWeight = GeoGridWeight(active=False, weightLand=.2, weightOceanActive=True, weightOcean=0.05, distanceTransitionStart=100000, distanceTransitionEnd=800000)
  calibrationPossible = False
  __dataForCellCache = {}

  def __init__(self, *args, enforceNorth=False, **kwargs):
    super().__init__(*args, **kwargs)
    self._enforceNorth = enforceNorth

  def emptyCacheForStep(self):
    super().emptyCacheForStep()
    self.__dataForCellCache = {}

  def __dataForCell(self, cell, neighbouringCells):
    key = cell._id2
    if key not in self.__dataForCellCache:
      lenNeighbours = len(neighbouringCells)
      bearingGeo = self._geoBearingsForCell(cell, neighbouringCells)
      # compute bearings
      bearings = [Cartesian.bearing(cell, neighbouringCell) for neighbouringCell in neighbouringCells]
      # compute average difference
      avgDiff = sum([Common.normalizeAngle(bearings[i] - bearingGeo[i], intervalStart=-Common._pi) for i in range(0, lenNeighbours)]) / lenNeighbours
      # compute scales
      rs = []
      sins, coss = [], []
      sinScales, cosScales = 1, 1
      sinWeights, cosWeights = 0, 0
      for i, neighbouringCell in enumerate(neighbouringCells):
        r = Cartesian.distance(neighbouringCell, cell) * self.calibrationFactor
        if r <= 1e-3 * self._settings._typicalDistance:
          rs.append(None)
          sins.append(None)
          coss.append(None)
          continue
        rGeo = self._geoDistanceForCells(neighbouringCell, cell)
        sin, cos = math.sin(bearings[i]), math.cos(bearings[i])
        sinGeo, cosGeo = math.sin(bearingGeo[i] + avgDiff), math.cos(bearingGeo[i] + avgDiff)
        absSinCos = abs(sin) + abs(cos)
        if abs(sin) >= 1e-1 and abs(sinGeo) >= 1e-1 and sin * sinGeo > 0:
          sinWeight = abs(sin) / absSinCos
          sinWeights += sinWeight
          sinScales *= (r * sin / (rGeo * sinGeo))**sinWeight
        if abs(cos) >= 1e-1 and abs(cosGeo) >= 1e-1 and cos * cosGeo > 0:
          cosWeight = abs(cos) / absSinCos
          cosWeights += cosWeight
          cosScales *= (r * cos / (rGeo * cosGeo))**cosWeight
        rs.append(r)
        sins.append(sin)
        coss.append(cos)
      # only proceed if scales are found
      if sinWeights == 0 or cosWeights == 0:
        self.__dataForCellCache[key] = None
      else:
        # determine the weighted geometric average of the scales
        try:
          scaleX = math.exp(sinScales**(1 / sinWeights))
        except OverflowError:
          scaleX = math.sqrt(sys.float_info.max)
        try:
          scaleY = math.exp(cosScales**(1 / cosWeights))
        except OverflowError:
          scaleY = math.sqrt(sys.float_info.max)
        # geometric average scale of X and Y direction
        scale = math.sqrt(scaleX * scaleY)
        # force vectors
        forceVectors = [Point((scale - scaleX) * r * sin, (scale - scaleY) * r * cos) if r is not None else None for r, sin, cos in zip(rs, sins, coss)]
        # value
        value = max(abs(scaleX / scaleY), abs(scaleY / scaleX)) - 1
        # result
        self.__dataForCellCache[key] = forceVectors, value
    return self.__dataForCellCache[key]

  def energy(self, cell, neighbouringCells):
    if not cell._isActive:
      return 0
    return self._quantity(cell, neighbouringCells, energy=True)
  def forces(self, cell, neighbouringCells):
    if not cell._isActive:
      return []
    d = self.__dataForCell(cell, neighbouringCells)
    if d is None:
      return []
    forceVectors, _ = d
    return [Force.byDelta(self.kind, neighbouringCell, forceVector, self._quantity(cell, neighbouringCells, force=True)) for forceVector, neighbouringCell in zip(forceVectors, neighbouringCells) if forceVector is not None]

  def _value(self, cell, neighbouringCells):
    d = self.__dataForCell(cell, neighbouringCells)
    if d is None:
      return 0
    _, value = d
    return min(1, value)
