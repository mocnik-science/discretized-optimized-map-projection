import time

class timer(object):
  def __init__(self, label='', log=True, **kwargs):
    self.__label = label
    self.__log = log
    self.__formatKwargs = kwargs
    self.__durations = []
    self.__time = None

  def __enter__(self):
    self.start()

  def __exit__(self, *args):
    duration = self.end()
    if not self.__log or self.__time is None:
      return
    label1 = ''
    if 'step' in self.__formatKwargs:
      label1 = f"step {self.__formatKwargs['step']:>5}"
    print(f"{label1:<10} | {self.__label:<36} {duration * 10**3:8.3f} ms")

  def end(self):
    if self.__time is None:
      return None
    duration = time.time() - self.__time
    self.__durations.append(duration)
    return duration

  def start(self):
    self.__time = time.time()

  def t(self):
    return self.__durations

  def average(self, n=50):
    if len(self.__durations) == 0:
      return None
    self.__durations = self.__durations[-n:]
    return sum(self.__durations) / len(self.__durations)
