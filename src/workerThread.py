from threading import *
import time
import wx

from src.geoGrid.geoGrid import *
from src.geoGrid.geoGridSettings import *
from src.timer import *

EVT_WORKER_THREAD_UPDATE_ID = wx.NewId()

def EVT_WORKER_THREAD_UPDATE(win, f):
  win.Connect(-1, -1, EVT_WORKER_THREAD_UPDATE_ID, f)

class ResultEvent(wx.PyEvent):
  def __init__(self, im, status):
    wx.PyEvent.__init__(self)
    self.SetEventType(EVT_WORKER_THREAD_UPDATE_ID)
    self.im = im
    self.status = status

class WorkerThread(Thread):
  def __init__(self, notifyWindow, geoGridSettings, viewSettings):
    Thread.__init__(self)
    self.__notifyWindow = notifyWindow
    self.__geoGridSettings = geoGridSettings
    self.__viewSettings = viewSettings
    self.__g = None
    self.__shallRun = False
    self.__shallRun1 = False
    self.__shallQuit = False
    self.__fpsLastRuns = []
    self.start()
  
  def run(self):
    # initialize
    self.__gg = GeoGrid(self.__geoGridSettings, callbackStatus=lambda status: wx.PostEvent(self.__notifyWindow, ResultEvent(None, status)))
    wx.PostEvent(self.__notifyWindow, ResultEvent(self.__gg.getImage(self.__viewSettings), None))
    while not self.__shallQuit:
      if not self.__shallRun and not self.__shallRun1:
        # wait
        time.sleep(.01)
      else:
        self.__shallRun1 = False
        # step
        t = timer()
        self.__gg.performStep()
        im = self.__gg.getImage(self.__viewSettings)
        self.__fpsLastRuns = self.__fpsLastRuns[-50:] + [1 / t.end()]
        wx.PostEvent(self.__notifyWindow, ResultEvent(im, f"Step {self.__gg.step()}, energy = {self.__gg.energy():>10.0f}, {sum(self.__fpsLastRuns) / len(self.__fpsLastRuns):.0f} fps"))

  def updateViewSettings(self, viewSettings):
    self.__viewSettings = viewSettings
    im = self.__gg.getImage(self.__viewSettings)
    wx.PostEvent(self.__notifyWindow, ResultEvent(im, None))

  def unpause(self):
    self.__shallRun1 = False
    self.__shallRun = True

  def pause(self):
    self.__shallRun = False
    self.__shallRun1 = False

  def unpause1(self):
    self.__shallRun1 = True
    self.__shallRun = False

  def quit(self):
    self.__shallQuit = True
