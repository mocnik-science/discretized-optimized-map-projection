import math
import numpy as np

def normalizeAngle(a, intervalStart=0): # in radiant
  return ((a + 2 * math.pi - intervalStart) % (2 * math.pi)) + intervalStart

def cartesianLength(x, y):
  return math.sqrt(x**2 + y**2)

def cartesianDistance(start, end):
  return cartesianLength(end.x - start.x, end.y - start.y)

def cartesianArea(cs):
  xs = np.array([c.x for c in cs])
  ys = np.array([c.y for c in cs])
  # Shoelace formula
  areaMain = np.dot(xs[:-1], ys[1:]) - np.dot(ys[:-1], xs[1:])
  areaCorrection = xs[-1] * ys[0] - ys[-1] * xs[0]
  return np.abs(areaMain + areaCorrection) / 2

def cartesianBearing(start, end): # in radiant, positively oriented, north is 0
  return (math.atan2(end.y - start.y, end.x - start.x) + 1.5 * math.pi) % (2 * math.pi)
