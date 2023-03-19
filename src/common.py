import math

flatten = lambda xss: [x for xs in xss for x in xs]
sign = lambda x: math.copysign(1, x)

def minBy(xs, by, includeMin=False):
  xMin = None
  fMin = None
  for x in xs:
    f = by(x)
    if xMin is None or f < fMin:
      xMin = x
      fMin = f
  if includeMin:
    return xMin, fMin
  return xMin
