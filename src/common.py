import math

flatten = lambda xss: [x for xs in xss for x in xs]
sign = lambda x: math.copysign(1, x)
