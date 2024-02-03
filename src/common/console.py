class Console:
  __LINE_UP = '\033[1A'
  __LINE_CLEAR = '\x1b[2K'
  __STATUS_COLOR = '\x1b[32m'
  __STATUS_COLOR_END = '\x1b[39m'
  __statusLine = None

  @classmethod
  def __strCleanIfStatus(cls):
    return len(Console.__statusLine.splitlines()) * (Console.__LINE_UP + Console.__LINE_CLEAR) if Console.__statusLine is not None else ''

  @classmethod
  def __strForArgs(cls, args):
    if isinstance(args, str):
      args = [args]
    return ' '.join(str(arg) for arg in args)

  @classmethod
  def print(cls, *args):
    print(cls.__strCleanIfStatus() + cls.__strForArgs(args))
    if cls.__statusLine is not None:
      print(cls.__statusLine)

  @classmethod
  def status(cls, *args):
    statusLine = cls.__STATUS_COLOR + cls.__strForArgs(args) + cls.__STATUS_COLOR_END
    print(cls.__strCleanIfStatus() + statusLine)
    cls.__statusLine = statusLine

  @classmethod
  def clearStatus(cls):
    if cls.__statusLine is not None:
      print(cls.__strCleanIfStatus())
