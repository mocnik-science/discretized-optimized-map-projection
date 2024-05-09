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

def brange(start, stop, step=1, partitions=None, closed=True, epsilon=1e-10):
  xs = []
  if partitions is None:
    if (stop - start) / step < 0:
      raise Exception('infinite list')
    while (start < stop + epsilon if closed else start <= stop + epsilon):
      xs.append(start)
      start += step
    return xs
  else:
    return [start + (stop - start) / partitions * i for i in range(partitions + 1)]
