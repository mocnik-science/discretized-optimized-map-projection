def isWindowDestroyed(window):
  try:
    window.Enabled
  except RuntimeError:
    return True
  return False
