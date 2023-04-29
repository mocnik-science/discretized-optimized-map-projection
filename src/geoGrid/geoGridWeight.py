class GeoGridWeight:
  def __init__(self, weightLand=1, weightOcean=1):
    self.__weightLand = weightLand
    self.__weightOcean = weightOcean

  def forCell(self, cell):
    return self.__weightLand if True else self._weightOcean
