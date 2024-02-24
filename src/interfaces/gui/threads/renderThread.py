import json
import os
from threading import Thread
import time
import wx

from src.common.timer import timer
from src.interfaces.common.interfaceCommon import InterfaceCommon

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
    self.__dataData = InterfaceCommon.startData()
    self.__videoData = InterfaceCommon.startVideo()
    self.start()
  
  def run(self):
    t = timer(log=False)
    # loop
    while not self.__shallQuit:
      if (self.__serializedData is None and not (self.__shallViewUpdate and self.__serializedDataLast is not None)) or self.__projection is None:
        # wait
        time.sleep(.01)
      else:
        self.__shallViewUpdate = False
        frameSaved = False
        with t:
          # data
          if self.__stepData and (self.__stepData['saveData'] or self.__stepData['step'] == 0):
            InterfaceCommon.stepData(self.__dataData, self.__geoGridSettings, stepData=self.__stepData, appendOnlyIf=self.__stepData['step'] > 0)
            self.__stepData['saveData'] = False
          # render
          im, _ = InterfaceCommon.renderImage(self.__geoGridSettings, self.__viewSettings, serializedData=self.__serializedData or self.__serializedDataLast, projection=self.__projection, stepData=self.__stepData, size=self.__size if not self.__viewSettings['captureVideo'] else None)
          if self.__stepData and self.__stepData['saveImage']:
            InterfaceCommon.stepVideo(im, self.__videoData, stepData=self.__stepData)
            self.__stepData['saveImage'] = False
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

  @staticmethod
  def __fileFunction(*args, **kwargs):
    return lambda file: file.byDialog(wx.FileDialog, wx.ID_OK, *args, **kwargs, style=wx.FD_SAVE)

  def saveData(self, parentWindow):
    _fileFunction = RenderThread.__fileFunction(parentWindow, message='Save data', wildcard='CSV files (*.csv)|*.csv')
    InterfaceCommon.saveData(_fileFunction, self.__dataData, self.__geoGridSettings)

  def saveScreenshot(self, parentWindow, largeSymbols=False, svg=False):
    _fileFunction = RenderThread.__fileFunction(parentWindow, message='Save screenshot', wildcard='Scalable Vector Graphics (*.svg)|*.svg' if svg else 'Portable Network Graphics (*.png)|*.png')
    InterfaceCommon.saveScreenshot(_fileFunction, self.__geoGridSettings, self.__viewSettings, serializedData=self.__serializedData or self.__serializedDataLast, projection=self.__projection, stepData=self.__stepData, largeSymbols=largeSymbols, extension='svg' if svg else 'png')

  def saveVideo(self, parentWindow):
    _fileFunction = RenderThread.__fileFunction(parentWindow, message='Save video', wildcard='Video files (*.mp4)|*.mp4')
    InterfaceCommon.saveVideo(_fileFunction, self.__videoData, self.__geoGridSettings)
    self.__videoData = InterfaceCommon.startVideo()

  def quit(self):
    self.__shallQuit = True
