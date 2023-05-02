from threading import Thread
import time
import wx

from src.common.timer import timer
from src.geoGrid.geoGrid import GeoGrid

EVT_WORKER_THREAD_UPDATE_ID = wx.NewId()

def EVT_WORKER_THREAD_UPDATE(win, f):
  win.Connect(-1, -1, EVT_WORKER_THREAD_UPDATE_ID, f)

class WorkerResultEvent(wx.PyEvent):
  def __init__(self, projection=None, serializedData=None, serializedDataForProjection=None, status=None, energy=None, stopThresholdReached=None):
    wx.PyEvent.__init__(self)
    self.SetEventType(EVT_WORKER_THREAD_UPDATE_ID)
    self.projection = projection
    self.serializedData = serializedData
    self.serializedDataForProjection = serializedDataForProjection
    self.status = status
    self.energy = energy
    self.stopThresholdReached = stopThresholdReached

class WorkerThread(Thread):
  def __init__(self, notifyWindow, geoGridSettings, viewSettings):
    Thread.__init__(self)
    self.__notifyWindow = notifyWindow
    self.__geoGridSettings = geoGridSettings
    self.__viewSettings = viewSettings
    self.__shallRun = False
    self.__shallRun1 = False
    self.__shallRunStop = False
    self.__shallQuit = False
    self.__needsUpdate = False
    self.__needsGUIUpdate = False
    self.__shallUpdateGui = False
    self.start()
  
  def fullReload(self):
    self.__geoGrid = GeoGrid(self.__geoGridSettings, callbackStatus=lambda status, energy: self.__post(status=status, energy=energy))
    self.__post(projection=self.__geoGrid.projection())
    self.updateViewSettings()

  def run(self):
    self.fullReload()
    self.__geoGridSettings.setUntouched()
    # initialize
    t = timer(log=False)
    # loop
    while not self.__shallQuit:
      if not self.__shallRun and not self.__shallRun1 and not self.__shallRunStop and not self.__needsUpdate:
        # perform gui update if necessary
        if self.__needsGUIUpdate:
          guiData = self.__updateGui1()
          self.__updateGui2(guiData)
        # wait
        time.sleep(.01)
      else:
        # preparations
        shallUpdateGui = self.__needsUpdate or self.__shallUpdateGui or self.__shallRun1 or self.__shallRunStop or (self.__geoGrid.step() + 1) % (self.__viewSettings['showNthStep'] if 'showNthStep' in self.__viewSettings else 1) == 0
        with t:
          # step
          if self.__shallRun or self.__shallRun1 or self.__shallRunStop:
            self.__geoGrid.performStep()
          else:
            self.__geoGrid.computeForcesAndEnergies()
          serializedDataForProjection = self.__geoGrid.serializedDataForProjection()
          # compute energy
          energy = self.__geoGrid.energy()
          # check whether the threshold has been reached
          stopThresholdReached = None
          if self.__shallRunStop:
            # maxForceStrength is in units of the coordinate system in which the cells are located: radiusEarth * deg2rad(lon), radiusEarth * deg2rad(lat)
            # maxForceStrength is divided by the typical distance (which works perfectly at the equator) to normalize
            # The normalized maxForceStrength is divided by the speed (100 * (1 - dampingFactor)), in order to compensate for varying speeds
            stopThresholdReached = self.__geoGrid.maxForceStrength() / self.__geoGridSettings._typicalDistance / (100 * (1 - self.__geoGridSettings._dampingFactor)) < self.__geoGridSettings._stopThreshold
            if stopThresholdReached:
              self.__geoGridSettings.setThresholdReached()
          if shallUpdateGui:
            guiData = self.__updateGui1()
        # update transient information in the settings
        self.__geoGridSettings.updateTransient(energy=energy, step=self.__geoGrid.step())
        # post result
        self.__post(status=f"Step {self.__geoGrid.step()}, {1 / t.average():.0f} fps", serializedDataForProjection=serializedDataForProjection, **(self.__updateGui2(guiData, post=False) if shallUpdateGui else {}), energy=energy, stopThresholdReached=stopThresholdReached)
        # cleanup
        self.__needsUpdate = False
        self.__shallRun1 = False
        if stopThresholdReached:
          self.__shallRunStop = False
        self.__needsGUIUpdate = True

  def __post(self, **kwargs):
    wx.PostEvent(self.__notifyWindow, WorkerResultEvent(**kwargs))

  def __updateGui1(self):
    serializedData = self.__geoGrid.serializedData(self.__viewSettings)
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
    serializedData = self.__geoGrid.serializedData(self.__viewSettings)
    self.__post(serializedData=serializedData)

  def exportProjectionTIN(self):
    return self.__geoGrid.exportProjectionTIN()

  def update(self):
    self.__needsUpdate = True

  def updateGui(self):
    self.__shallUpdateGui = True

  def pause(self):
    self.__shallRun = False
    self.__shallRun1 = False
    self.__shallRunStop = False

  def unpause(self):
    self.__shallRun1 = False
    self.__shallRunStop = False
    self.__shallRun = True

  def unpause1(self):
    self.__shallRun = False
    self.__shallRunStop = False
    self.__shallRun1 = True

  def unpauseStop(self):
    self.__shallRun = False
    self.__shallRun1 = False
    self.__shallRunStop = True

  def quit(self):
    self.__shallQuit = True
