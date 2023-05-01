import wx

from src.app.renderThread import RenderThread, EVT_RENDER_THREAD_UPDATE
from src.app.windows import isWindowDestroyed
from src.app.windowAbout import WindowAbout
from src.app.windowSimulationSettings import WindowSimulationSettings
from src.app.workerThread import WorkerThread, EVT_WORKER_THREAD_UPDATE
from src.geoGrid.geoGridSettings import GeoGridSettings

class WindowMain(wx.Frame):
  def __init__(self, title):
    self.__workerThread = None
    self.__renderThread = None
    self.__workerThreadRunning = False
    self.__newImage = None
    self.__isLoadingNewImage = False
    self.__geoGridSettings = GeoGridSettings()
    # self.__simulationSettings = {}
    self.__viewSettings = {}
    self.__windowSimulationSettings = None
    self.__windowAbout = None
    wx.Frame.__init__(self, None, wx.ID_ANY, title=title, size=(900, 600))

    ## menu bar
    # functions
    self.__menuDict = {}
    def addItem(menu, label, data, callback):
      newId = wx.NewId()
      self.__menuDict[newId] = data
      menuItem = menu.Append(newId, label, label)
      self.Bind(wx.EVT_MENU, lambda event: callback(self.__menuDict[event.Id]), menuItem)
      return menuItem
    # def addCheckItem(menu, label, object, key, data, callback, default=False):
    #   newId = wx.NewId()
    #   self.__menuDict[newId] = data
    #   menuItem = menu.Append(newId, label, label, wx.ITEM_CHECK)
    #   if default:
    #     menuItem.Check(True)
    #   def cb(event):
    #     object[key][self.__menuDict[event.Id]] = menuItem.IsChecked()
    #     callback()
    #   self.Bind(wx.EVT_MENU, cb, menuItem)
    #   if key not in object:
    #     object[key] = {}
    #   object[key][data] = default
    #   return menuItem
    def addRadioItem(menu, label, object, key, data, callback, default=False):
      newId = wx.NewId()
      self.__menuDict[newId] = data
      menuItem = menu.Append(newId, label, label, wx.ITEM_RADIO)
      if default:
        menuItem.Check(True)
      def cb(event):
        object[key] = self.__menuDict[event.Id]
        callback()
      self.Bind(wx.EVT_MENU, cb, menuItem)
      if key not in object or default:
        object[key] = data
      return menuItem
    # init
    menuBar = wx.MenuBar()
    # simulation menu
    simulationMenu = wx.Menu()
    menuBar.Append(simulationMenu, "&Simulation")
    # simulation menu: start/stop animation
    startMenuItem = addItem(simulationMenu, 'Start', None, self.onRun)
    startStopMenuItem = addItem(simulationMenu, 'Start, and stop at threshold\tSpace', None, self.onRunStop)
    stopMenuItem = addItem(simulationMenu, 'Stop\tSpace', None, self.onRun)
    addItem(simulationMenu, 'Compute next step\tRight', None, self.onRun1)
    resetMenuItem = addItem(simulationMenu, 'Reset\tBack', None, self.onReset)
    simulationMenu.AppendSeparator()
    # # simulation menu: potentials
    # key = 'simulationSelectedPotential'
    # for potential in self.__geoGridSettings.potentials:
    #   addCheckItem(simulationMenu, f"consider {potential.kind.lower()}", self.__simulationSettings, key, potential.kind, self.updateSimulationSettings, default=True)
    # simulationMenu.AppendSeparator()
    # simulation menu: simulation settings
    addItem(simulationMenu, 'Simulation settings...\tCtrl+.', None, self.onSimulationSettings)
    simulationMenu.AppendSeparator()
    addItem(simulationMenu, 'About...', None, self.onAbout)
    # view menu
    viewMenu = wx.Menu()
    menuBar.Append(viewMenu, "&View")
    # view menu: potentials
    key = 'selectedPotential'
    addRadioItem(viewMenu, 'Hide forces', self.__viewSettings, key, None, self.updateViewSettings)
    addRadioItem(viewMenu, 'All forces', self.__viewSettings, key, 'ALL', self.updateViewSettings, default=True)
    for potential in self.__geoGridSettings.potentials:
      addRadioItem(viewMenu, f"Force for {potential.kind.lower()}", self.__viewSettings, key, potential.kind, self.updateViewSettings)
    viewMenu.AppendSeparator()
    # view menu: visualization method
    key = 'selectedVisualizationMethod'
    addRadioItem(viewMenu, 'Sum', self.__viewSettings, key, 'SUM', self.updateViewSettings)
    addRadioItem(viewMenu, 'Individually', self.__viewSettings, key, 'INDIVIDUALLY', self.updateViewSettings)
    viewMenu.AppendSeparator()
    # view menu: energy
    key = 'selectedEnergy'
    addRadioItem(viewMenu, 'Hide energies', self.__viewSettings, key, None, self.updateViewSettings, default=True)
    addRadioItem(viewMenu, 'All energies', self.__viewSettings, key, 'ALL', self.updateViewSettings)
    for potential in self.__geoGridSettings.potentials:
      addRadioItem(viewMenu, f"Energy for {potential.kind.lower()}", self.__viewSettings, key, potential.kind, self.updateViewSettings)
    viewMenu.AppendSeparator()
    # view menu: draw neighbours
    key = 'drawNeighbours'
    addRadioItem(viewMenu, 'Hide neighbours', self.__viewSettings, key, False, self.updateViewSettings)
    addRadioItem(viewMenu, 'Show neighbours', self.__viewSettings, key, True, self.updateViewSettings)
    viewMenu.AppendSeparator()
    # view menu: draw labels
    key = 'drawLabels'
    addRadioItem(viewMenu, 'Hide labels', self.__viewSettings, key, False, self.updateViewSettings)
    addRadioItem(viewMenu, 'Show labels', self.__viewSettings, key, True, self.updateViewSettings)
    viewMenu.AppendSeparator()
    # view menu: draw colours
    key = 'drawColours'
    addRadioItem(viewMenu, 'Show active state', self.__viewSettings, key, 'ACTIVE', self.updateViewSettings)
    for potential in self.__geoGridSettings.potentials:
      addRadioItem(viewMenu, f"Show weights for {potential.kind.lower()}", self.__viewSettings, key, potential.kind, self.updateViewSettings)
    viewMenu.AppendSeparator()
    # view menu: draw original polygons
    key = 'drawOriginalPolygons'
    addRadioItem(viewMenu, 'Hide initial cells', self.__viewSettings, key, False, self.updateViewSettings)
    addRadioItem(viewMenu, 'Show initial cells', self.__viewSettings, key, True, self.updateViewSettings)
    viewMenu.AppendSeparator()
    # view menu: draw continents
    key = 'drawContinentsTolerance'
    addRadioItem(viewMenu, 'Hide continents', self.__viewSettings, key, False, self.updateViewSettings)
    addRadioItem(viewMenu, 'Show strongly simplified continents (faster)', self.__viewSettings, key, 3, self.updateViewSettings)
    addRadioItem(viewMenu, 'Show simplified continents (slow)', self.__viewSettings, key, 1, self.updateViewSettings)
    addRadioItem(viewMenu, 'Show continents (very slow)', self.__viewSettings, key, 'full', self.updateViewSettings)
    viewMenu.AppendSeparator()
    # view menu: showNthStep
    key = 'showNthStep'
    addRadioItem(viewMenu, 'Try to render every step', self.__viewSettings, key, 1, self.updateViewSettings)
    addRadioItem(viewMenu, 'Render every 5th step', self.__viewSettings, key, 5, self.updateViewSettings, default=True)
    addRadioItem(viewMenu, 'Render every 10th step', self.__viewSettings, key, 10, self.updateViewSettings)
    addRadioItem(viewMenu, 'Render every 25th step', self.__viewSettings, key, 25, self.updateViewSettings)
    # finalize
    self.SetMenuBar(menuBar)

    ## tool bar
    # icons
    iconPlayStop = wx.Icon('assets/playStop.png', type=wx.BITMAP_TYPE_PNG)
    # iconPlay = wx.Icon('assets/play.png', type=wx.BITMAP_TYPE_PNG)
    iconPlay1 = wx.Icon('assets/play1.png', type=wx.BITMAP_TYPE_PNG)
    iconPause = wx.Icon('assets/pause.png', type=wx.BITMAP_TYPE_PNG)
    iconReset = wx.Icon('assets/reset.png', type=wx.BITMAP_TYPE_PNG)
    iconGear = wx.Icon('assets/gear.png', type=wx.BITMAP_TYPE_PNG)
    # functions
    def addTool(id, label, icon, callback):
      tool = toolBar.AddTool(id, label, icon)
      self.Bind(wx.EVT_TOOL, callback, tool)
    # init
    toolBar = self.CreateToolBar()
    addTool(0, 'RunStop', iconPlayStop, self.onRunStop)
    # addTool(1, 'Run', iconPlay, self.onRun)
    addTool(2, 'Run one step', iconPlay1, self.onRun1)
    addTool(3, 'Reset', iconReset, self.onReset)
    addTool(4, 'Simulation settings', iconGear, self.onSimulationSettings)
    toolBar.Realize()

    # update functions
    def guiPlay(isPlaying):
      # menu
      startMenuItem.Enable(enable=not isPlaying)
      startStopMenuItem.Enable(enable=not isPlaying)
      stopMenuItem.Enable(enable=isPlaying)
      resetMenuItem.Enable(enable=not isPlaying)
      # toolbar
      toolBar.SetToolNormalBitmap(0, iconPause if isPlaying else iconPlayStop)
      # toolBar.SetToolNormalBitmap(1, iconPause if isPlaying else iconPlay)
      toolBar.EnableTool(3, not isPlaying)
      toolBar.Realize()
      toolBar.Refresh()
    self._guiPlay = guiPlay

    ## status bar
    self._statusBar = self.CreateStatusBar(3)
    self._statusBar.SetStatusWidths([250, -1, 130])

    ## layout
    self._panel = wx.Panel(self, style=wx.DEFAULT)
    box = wx.BoxSizer(wx.VERTICAL)

    ## image
    self._image = wx.StaticBitmap(self._panel)
    self._image.SetBackgroundColour(wx.WHITE)
    box.Add(self._image, 1, wx.EXPAND)

    ## layout
    self._panel.SetSizer(box)
    self._panel.Layout()

    ## register handlers
    self.Bind(wx.EVT_CLOSE, self.onClose)

    ## adapt app menu
    appMenu = self.MenuBar.OSXGetAppleMenu()
    for m in appMenu.GetMenuItems():
      if m.GetId() == wx.ID_EXIT:
        self.Bind(wx.EVT_MENU, self.onClose, m)

    ## reset
    wx.CallLater(10, self.reset)

  def updateViewSettings(self):
    self.__workerThread.updateViewSettings(self.__viewSettings)
    self.__renderThread.updateViewSettings(self.__viewSettings)

  def loadImage(self, image):
    self.__newImage = image
    if self.__isLoadingNewImage:
      return
    self.__isLoadingNewImage = True
    while self.__newImage is not None:
      wx.Yield()
      im = self.__newImage
      self.__newImage = None
      try:
        im2 = wx.Image(*im.size)
        im2.SetData(im.convert('RGB').tobytes())
        self._image.SetBitmap(wx.Bitmap(im2))
        self._panel.Layout()
      except:
        pass
    self.__isLoadingNewImage = False

  def setStatus(self, text):
    try:
      self._statusBar.SetStatusText(text, 0)
    except:
      pass
  def setStatus2(self, text):
    try:
      self._statusBar.SetStatusText(text, 1)
    except:
      pass

  def setEnergy(self, energy):
    try:
      self._statusBar.SetStatusText(f"energy = {energy:.2E}", 2)
    except:
      pass

  def quitThreads(self):
    if self.__workerThread is not None:
      self.__workerThread.quit()
    self.__workerThread = None
    if self.__renderThread is not None:
      self.__renderThread.quit()
    self.__renderThread = None

  def reset(self):
    self.quitThreads()
    self.__workerThreadRunning = False
    self._guiPlay(False)
    self.__newImage = None
    self.__isLoadingNewImage = False
    self.prepareRenderThread()
    self.prepareWorkerThread()

  def prepareRenderThread(self):
    EVT_RENDER_THREAD_UPDATE(self, self.__renderThreadUpdate)
    self.__renderThread = RenderThread(self, self.__geoGridSettings, self.__viewSettings)
  def prepareWorkerThread(self):
    EVT_WORKER_THREAD_UPDATE(self, self.__workerThreadUpdate)
    self.__workerThread = WorkerThread(self, self.__geoGridSettings, self.__viewSettings)
  
  def __renderThreadUpdate(self, event):
    if self.__renderThread is None:
      return
    if event.im is not None:
      self.loadImage(event.im)
      if self.__viewSettings['showNthStep']:
        self.__workerThread.updateGui()
    if event.status is not None:
      self.setStatus2(event.status)
  def __workerThreadUpdate(self, event):
    if self.__workerThread is None:
      return
    if event.projection is not None:
      self.__renderThread.setProjection(event.projection)
    if event.serializedDataForProjection is not None:
      self.__renderThread.updateSerializedDataForProjection(event.serializedDataForProjection)
    if event.serializedData is not None:
      self.__renderThread.render(event.serializedData)
    if event.status is not None:
      self.setStatus(event.status)
    if event.energy is not None:
      self.setEnergy(event.energy)
    if event.stopThresholdReached == True:
      self.onRun(None, forceStop=True)

  def onSimulationSettings(self, event):
    if self.__windowSimulationSettings is None or isWindowDestroyed(self.__windowSimulationSettings):
      self.__windowSimulationSettings = WindowSimulationSettings(self.__geoGridSettings, self.__workerThread)
    else:
      self.__windowSimulationSettings.Destroy()
      self.__windowSimulationSettings = None

  def onAbout(self, event):
    if self.__windowAbout is None or isWindowDestroyed(self.__windowAbout):
      self.__windowAbout = WindowAbout()
    else:
      self.__windowAbout.Destroy()
      self.__windowAbout = None

  def onRun(self, event, forceStop=False):
    if self.__workerThreadRunning or forceStop:
      self.__workerThreadRunning = False
      self._guiPlay(False)
      self.__workerThread.pause()
    else:
      self.__workerThreadRunning = True
      self._guiPlay(True)
      self.__workerThread.unpause()

  def onRun1(self, event):
    self.__workerThreadRunning = False
    self._guiPlay(False)
    self.__workerThread.unpause1()

  def onRunStop(self, event):
    if self.__workerThreadRunning:
      self.__workerThreadRunning = False
      self._guiPlay(False)
      self.__workerThread.pause()
    else:
      self.__workerThreadRunning = True
      self._guiPlay(True)
      self.__workerThread.unpauseStop()

  def onReset(self, event):
    self.reset()

  def onClose(self, event):
    self.quitThreads()
    self.Destroy()
