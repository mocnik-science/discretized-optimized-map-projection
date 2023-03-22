from threading import Thread
import time
import wx

from src.common.timer import timer
from src.geoGrid.geoGrid import GeoGrid

EVT_WORKER_THREAD_UPDATE_ID = wx.NewId()

def EVT_WORKER_THREAD_UPDATE(win, f):
  win.Connect(-1, -1, EVT_WORKER_THREAD_UPDATE_ID, f)

class WorkerResultEvent(wx.PyEvent):
  def __init__(self, projection=None, serializedData=None, serializedDataForProjection=None, status=None, energy=None):
    wx.PyEvent.__init__(self)
    self.SetEventType(EVT_WORKER_THREAD_UPDATE_ID)
    self.projection = projection
    self.serializedData = serializedData
    self.serializedDataForProjection = serializedDataForProjection
    self.status = status
    self.energy = energy

class WorkerThread(Thread):
  def __init__(self, notifyWindow, geoGridSettings, viewSettings):
    Thread.__init__(self)
    self.__notifyWindow = notifyWindow
    self.__geoGridSettings = geoGridSettings
    self.__viewSettings = viewSettings
    self.__shallRun = False
    self.__shallRun1 = False
    self.__shallQuit = False
    self.__needsGUIUpdate = False
    self.__shallUpdateGui = False
    self.start()
  
  def run(self):
    self.__gg = GeoGrid(self.__geoGridSettings, callbackStatus=lambda status, energy: self.__post(status=status, energy=energy))
    self.__post(projection=self.__gg.projection())
    # initialize
    self.updateViewSettings()
    t = timer(log=False)
    # loop
    while not self.__shallQuit:
      if not self.__shallRun and not self.__shallRun1:
        # perform gui update if necessary
        if self.__needsGUIUpdate:
          guiData = self.__updateGui1()
          self.__updateGui2(guiData)
        # wait
        time.sleep(.01)
      else:
        # preparations
        shallUpdateGui = self.__shallUpdateGui or self.__shallRun1 or (self.__gg.step() + 1) % (self.__viewSettings['showNthStep'] if 'showNthStep' in self.__viewSettings else 1) == 0
        self.__shallRun1 = False
        self.__needsGUIUpdate = True
        # step
        with t:
          self.__gg.performStep()
          serializedDataForProjection = self.__gg.serializedDataForProjection()
          energy = self.__gg.energy()
          if shallUpdateGui:
            guiData = self.__updateGui1()
        # cleanup
        self.__post(status=f"Step {self.__gg.step()}, {1 / t.average():.0f} fps", serializedDataForProjection=serializedDataForProjection, **(self.__updateGui2(guiData, post=False) if shallUpdateGui else {}), energy=energy)

  def __post(self, **kwargs):
    wx.PostEvent(self.__notifyWindow, WorkerResultEvent(**kwargs))

  def __updateGui1(self):
    serializedData = self.__gg.serializedData(self.__viewSettings)
    return serializedData

  def __updateGui2(self, serializedData, post=True):
    self.__needsGUIUpdate = False
    self.__shallUpdateGui = False
    kwargs = {
      'serializedData': serializedData,
    }
    if post:
      self.__post(**kwargs)
    else:
      return kwargs

  def updateViewSettings(self, viewSettings=None):
    if viewSettings is not None:
      self.__viewSettings = viewSettings
    serializedData = self.__gg.serializedData(self.__viewSettings)
    self.__post(serializedData=serializedData)

  def updateGui(self):
    self.__shallUpdateGui = True

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
