from threading import *
import time
import wx

from src.common.timer import *
from src.geoGrid.geoGrid import *
from src.geoGrid.geoGridSettings import *

EVT_RENDER_THREAD_UPDATE_ID = wx.NewId()

def EVT_RENDER_THREAD_UPDATE(win, f):
  win.Connect(-1, -1, EVT_RENDER_THREAD_UPDATE_ID, f)

class RenderResultEvent(wx.PyEvent):
  def __init__(self, im=None):
    wx.PyEvent.__init__(self)
    self.SetEventType(EVT_RENDER_THREAD_UPDATE_ID)
    self.im = im

class RenderThread(Thread):
  def __init__(self, notifyWindow, viewSettings):
    Thread.__init__(self)
    self.__notifyWindow = notifyWindow
    self.__viewSettings = viewSettings
    self.__projection = None
    self.__shallQuit = False
    self.__serializedData = None
    self.__serializedDataPrevious = None
    self.start()
  
  def run(self):
    while not self.__shallQuit:
      if self.__serializedData is None or self.__projection is None:
        # wait
        time.sleep(.01)
      else:
        # render
        im = GeoGridRenderer.render(self.__serializedData, viewSettings=self.__viewSettings, projection=self.__projection)
        self.__post(im=im)
        self.__serializedDataPrevious = self.__serializedData
        self.__serializedData = None

  def __post(self, **kwargs):
    wx.PostEvent(self.__notifyWindow, RenderResultEvent(**kwargs))

  def setProjection(self, projection):
    self.__projection = projection

  def updateSerializedDataForProjection(self, serializedDataForProjection):
    self.__projection.updateSerializedDataForProjection(serializedDataForProjection)

  def render(self, serializedData):
    self.__serializedData = serializedData

  def updateViewSettings(self, viewSettings=None):
    if viewSettings is not None:
      self.__viewSettings = viewSettings
      self.__serializedData = self.__serializedDataPrevious

  def quit(self):
    self.__shallQuit = True
