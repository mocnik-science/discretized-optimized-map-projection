import json
import random
import os
from threading import Thread
import time
import wx

from src.app.common import APP_CAPTURE_PATH
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
    self.__randomHashData = self.__hash()
    self.__randomHashVideo = self.__hash()
    self.start()
  
  def __hash(self):
    return f'{random.randrange(0, 10**6):06d}'

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
            self.__saveDataToTmp()
            self.__stepData['saveData'] = False
          # render
          im = GeoGridRenderer.render(self.__serializedData or self.__serializedDataLast, geoGridSettings=self.__geoGridSettings, viewSettings=self.__viewSettings, projection=self.__projection, size=(1920, 1080) if self.__viewSettings['captureVideo'] else self.__size, stepData=self.__stepData)
          if self.__stepData and self.__stepData['saveImage']:
            GeoGridRenderer.save(im, hash=self.__randomHashVideo, step=self.__stepData['step'])
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

  def __saveDataToTmp(self):
    fileNameTmp = os.path.join(APP_CAPTURE_PATH, self.__randomHashData + '.csv')
    innerEnergy, outerEnergy = self.__stepData['energy']
    settings = self.__geoGridSettings.toJSON()
    info = self.__geoGridSettings.info()
    data = {
      'step': str(self.__stepData['step']),
      'innerEnergy': f"{innerEnergy:.0f}",
      'outerEnergy': f"{outerEnergy:.0f}",
    }
    for key, value in self.__stepData['energyPerPotential'].items():
      innerEnergy, outerEnergy = value
      data = {
        **data,
        'innerEnergy_' + key: f"{innerEnergy:.0f}",
        'outerEnergy_' + key: f"{outerEnergy:.0f}",
      }
    data = {
      **data,
      'hash': info['hash'],
      'initialCRS': settings['initialCRS'],
      'resolution': str(settings['resolution']),
      'dampingFactor': str(settings['dampingFactor']),
      'stopThreshold': str(settings['stopThreshold']),
      'limitLatForEnergy': str(settings['limitLatForEnergy']),
      'weights': '"' + json.dumps(settings['weights']) + '"',
    }
    dataRow = f"{','.join(data.values())}\n"
    if not os.path.exists(fileNameTmp):
      os.makedirs(APP_CAPTURE_PATH, exist_ok=True)
      with open(fileNameTmp, 'w') as f:
        headerRow = f"{','.join(data.keys())}\n"
        f.write(headerRow)
        f.write(dataRow)
    if self.__stepData['step'] > 0:
      with open(fileNameTmp, 'a') as f:
        f.write(dataRow)

  def saveData(self, parentWindow):
    fileNameTmp = os.path.join(APP_CAPTURE_PATH, self.__randomHashData + '.csv')
    info = self.__geoGridSettings.info()
    dialog = wx.FileDialog(parentWindow, message='Save data', defaultDir='~/Downloads', defaultFile=f"domp-{info['hash']}-{self.__randomHashData}.csv", wildcard='CSV files (*.csv)|*.csv', style=wx.FD_SAVE)
    if dialog.ShowModal() == wx.ID_OK:
      os.replace(fileNameTmp, dialog.GetPath())

  def saveScreenshot(self, parentWindow):
    randomHash = self.__hash()
    info = self.__geoGridSettings.info()
    dialog = wx.FileDialog(parentWindow, message='Save screenshot', defaultDir='~/Downloads', defaultFile=f"domp-{info['hash']}-{self.__stepData['step']}-{randomHash}.png", wildcard='Image files (*.png)|*.png', style=wx.FD_SAVE)
    if dialog.ShowModal() == wx.ID_OK:
      if os.path.exists(dialog.GetPath()):
        os.unlink(dialog.GetPath())
      im = GeoGridRenderer.render(self.__serializedData or self.__serializedDataLast, geoGridSettings=self.__geoGridSettings, viewSettings=self.__viewSettings, projection=self.__projection, size=(1920, 1080), stepData=self.__stepData)
      im.save(dialog.GetPath(), optimize=False, compress_level=1)

  def renderVideo(self, parentWindow):
    fileNameTmp = os.path.join(APP_CAPTURE_PATH, self.__randomHashVideo)
    renderVideo(fileNameTmp, 20)
    info = self.__geoGridSettings.info()
    dialog = wx.FileDialog(parentWindow, message='Save video', defaultDir='~/Downloads', defaultFile=f"domp-{info['hash']}-{self.__randomHashVideo}.mp4", wildcard='Video files (*.mp4)|*.mp4', style=wx.FD_SAVE)
    if dialog.ShowModal() == wx.ID_OK:
      os.replace(fileNameTmp + '.mp4', dialog.GetPath())
    self.__randomHashVideo = self.__hash()

  def quit(self):
    self.__shallQuit = True
