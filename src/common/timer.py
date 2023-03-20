import time

class timer(object):
  def __init__(self, label='', log=True, **kwargs):
    self.__label = label
    self.__log = log
    self.__formatKwargs = kwargs
    self.__time = time.time()

  def __enter__(self):
    pass

  def __exit__(self, *args):
    if self.__log:
      label1 = ''
      if 'step' in self.__formatKwargs:
        label1 = f"step {self.__formatKwargs['step']:>5}"
      print(f"{label1:<10} | {self.__label:<36} {self.end() * 10**3:8.3f} ms")

  def end(self):
    return time.time() - self.__time
