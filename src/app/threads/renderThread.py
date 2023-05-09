import random
import os
from threading import Thread
import time
import wx

from src.app.common import APP_VIDEO_PATH
from src.common.timer import timer
from src.common.video import renderVideo
from src.geoGrid.geoGridRenderer import GeoGridRenderer

EVT_RENDER_THREAD_UPDATE_ID = wx.NewId()

def EVT_RENDER_THREAD_UPDATE(win, f):
  win.Connect(-1, -1, EVT_RENDER_THREAD_UPDATE_ID, f)

class RenderResultEvent(wx.PyEvent):
  def __init__(self, im=None, status=None, frameSaved=False):
    wx.PyEvent.__init__(self)
    self.SetEventType(EVT_RENDER_THREAD_UPDATE_ID)
    self.im = im
    self.status = status
    self.frameSaved = frameSaved

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
    self.__stepData = None
    self.__randomHash = f'{random.randrange(0, 10**6):06d}'
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
        frameSaved = False
        # render
        with t:
          im = GeoGridRenderer.render(self.__serializedData or self.__serializedDataLast, geoGridSettings=self.__geoGridSettings, viewSettings=self.__viewSettings, projection=self.__projection, size=(1920, 1080) if self.__viewSettings['captureVideo'] else self.__size)
          if self.__stepData:
            os.makedirs(os.path.join(APP_VIDEO_PATH, self.__randomHash), exist_ok=True)
            im.save(os.path.join(APP_VIDEO_PATH, self.__randomHash, f"frame-{self.__stepData['step']:08d}.png"))
            self.__stepData = None
            frameSaved = True
        # cleanup
        self.__post(im=im, status=f"rendering {1000 * t.average():.0f} ms", frameSaved=frameSaved)
        self.__serializedDataLast = self.__serializedData or self.__serializedDataLast
        self.__serializedData = None

  def __post(self, **kwargs):
    wx.PostEvent(self.__notifyWindow, RenderResultEvent(**kwargs))

  def setProjection(self, projection):
    self.__projection = projection

  def updateSerializedDataForProjection(self, serializedDataForProjection):
    self.__projection.updateSerializedDataForProjection(serializedDataForProjection)

  def render(self, serializedData, stepData=None):
    if stepData:
      self.__stepData = stepData
    self.__serializedData = serializedData

  def updateSize(self, size):
    self.__size = size
    self.__shallViewUpdate = True

  def updateViewSettings(self, viewSettings=None):
    if viewSettings is not None:
      self.__viewSettings = viewSettings

  def updateView(self):
    self.__shallViewUpdate = True

  def renderVideo(self):
    renderVideo(os.path.join(APP_VIDEO_PATH, self.__randomHash), 20)

  def quit(self):
    self.__shallQuit = True
