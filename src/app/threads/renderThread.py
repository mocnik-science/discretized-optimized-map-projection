from threading import Thread
import time
import wx

from src.common.timer import timer
from src.geoGrid.geoGridRenderer import GeoGridRenderer

EVT_RENDER_THREAD_UPDATE_ID = wx.NewId()

def EVT_RENDER_THREAD_UPDATE(win, f):
  win.Connect(-1, -1, EVT_RENDER_THREAD_UPDATE_ID, f)

class RenderResultEvent(wx.PyEvent):
  def __init__(self, im=None, status=None):
    wx.PyEvent.__init__(self)
    self.SetEventType(EVT_RENDER_THREAD_UPDATE_ID)
    self.im = im
    self.status = status

class RenderThread(Thread):
  def __init__(self, notifyWindow, geoGridSettings, viewSettings):
    Thread.__init__(self)
    self.__notifyWindow = notifyWindow
    self.__geoGridSettings = geoGridSettings
    self.__viewSettings = viewSettings
    self.__projection = None
    self.__shallQuit = False
    self.__serializedData = None
    self.__serializedDataLast = None
    self.__size = None
    self.__shallViewUpdate = False
    self.start()
  
  def run(self):
    t = timer(log=False)
    # loop
    while not self.__shallQuit:
      if not ((self.__serializedData is not None or (self.__shallViewUpdate and self.__serializedDataLast is not None)) and self.__projection is not None):
        # wait
        time.sleep(.01)
      else:
        self.__shallViewUpdate = False
        # render
        with t:
          im = GeoGridRenderer.render(self.__serializedData or self.__serializedDataLast, geoGridSettings=self.__geoGridSettings, viewSettings=self.__viewSettings, projection=self.__projection, size=self.__size)
        # cleanup
        self.__post(im=im, status=f"rendering {1000 * t.average():.0f} ms")
        self.__serializedDataLast = self.__serializedData or self.__serializedDataLast
        self.__serializedData = None

  def __post(self, **kwargs):
    wx.PostEvent(self.__notifyWindow, RenderResultEvent(**kwargs))

  def setProjection(self, projection):
    self.__projection = projection

  def updateSerializedDataForProjection(self, serializedDataForProjection):
    self.__projection.updateSerializedDataForProjection(serializedDataForProjection)

  def render(self, serializedData):
    self.__serializedData = serializedData

  def updateSize(self, size):
    self.__size = size
    self.__shallViewUpdate = True

  def updateViewSettings(self, viewSettings=None):
    if viewSettings is not None:
      self.__viewSettings = viewSettings

  def updateView(self):
    self.__shallViewUpdate = True

  def quit(self):
    self.__shallQuit = True
