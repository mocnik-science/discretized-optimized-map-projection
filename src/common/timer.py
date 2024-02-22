import time

from src.common.console import Console

class TimerConfig(object):
  def __new__(cls):
    if not hasattr(cls, 'instance'):
      cls.instance = super(TimerConfig, cls).__new__(cls)
      cls.instance.__disableAllLog = False
      cls.instance.__filterLog = None
    return cls.instance

  def disableAllLog(self, *value):
    if len(value) > 0:
      self.__disableAllLog = value[0]
    return self.__disableAllLog
  def filterLog(self, *value):
    if len(value) > 0:
      self.__filterLog = value[0]
    return self.__filterLog

timerConfig = TimerConfig()

class timer(object):
  __durationsByLabel = {}
  
  def __init__(self, label='', log=True, forceLog=False, showAverage=100, **kwargs):
    self.__label = label
    self.__log = log and (not timerConfig.disableAllLog() or forceLog)
    self.__forceLog = forceLog
    self.__showAverage = showAverage
    self.__formatKwargs = kwargs
    self.__time = None
    self.__durations = []

  def __enter__(self):
    self.start()

  def __exit__(self, *args):
    duration = self.end()
    if not self.__log or (timerConfig.disableAllLog() and not self.__forceLog) or self.__time is None or (timerConfig.filterLog() is not None and timerConfig.filterLog() not in self.__label):
      return
    label1 = ''
    if 'step' in self.__formatKwargs:
      label1 = f"step {self.__formatKwargs['step']:>5}"
    avg = ''
    if self.__showAverage is not False:
      avg = f", avg {sum(timer.__durationsByLabel[self.__label]) / len(timer.__durationsByLabel[self.__label]) * 10**3:8.3f} ms"
    Console.print(f"{label1:<10} | {self.__label:<60} {duration * 10**3:8.3f} ms{avg}")

  def end(self):
    if self.__time is None:
      return None
    duration = time.time() - self.__time
    self.__durations.append(duration)
    if self.__showAverage is not False and self.__log:
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
