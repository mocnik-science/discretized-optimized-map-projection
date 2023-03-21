import time

class timer(object):
  __durationsByLabel = {}
  
  def __init__(self, label='', log=True, showAverage=20, **kwargs):
    self.__label = label
    self.__log = log
    self.__showAverage = showAverage
    self.__formatKwargs = kwargs
    self.__time = None
    self.__durations = []

  def __enter__(self):
    self.start()

  def __exit__(self, *args):
    duration = self.end()
    if not self.__log or self.__time is None:
      return
    label1 = ''
    if 'step' in self.__formatKwargs:
      label1 = f"step {self.__formatKwargs['step']:>5}"
    avg = ''
    if self.__showAverage is not False:
      avg = f", avg {sum(timer.__durationsByLabel[self.__label]) / len(timer.__durationsByLabel[self.__label]) * 10**3:8.3f} ms"
    print(f"{label1:<10} | {self.__label:<36} {duration * 10**3:8.3f} ms{avg}")

  def end(self):
    if self.__time is None:
      return None
    duration = time.time() - self.__time
    self.__durations.append(duration)
    if self.__showAverage is not False:
      if self.__label not in timer.__durationsByLabel:
        timer.__durationsByLabel[self.__label] = []
      timer.__durationsByLabel[self.__label] = timer.__durationsByLabel[self.__label][-self.__showAverage:] + [duration]
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
