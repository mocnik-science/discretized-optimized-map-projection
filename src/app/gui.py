import wx
import wx.adv

from src.app.guiSimulationSettings import WindowSimulationSettings
from src.app.renderThread import RenderThread, EVT_RENDER_THREAD_UPDATE
from src.app.workerThread import WorkerThread, EVT_WORKER_THREAD_UPDATE
from src.geoGrid.geoGridSettings import GeoGridSettings

class TaskBarIcon(wx.adv.TaskBarIcon):
  def __init__(self):
    wx.adv.TaskBarIcon.__init__(self, iconType=wx.adv.TBI_DOCK)
    self.SetIcon(wx.Icon('assets/map.png', wx.BITMAP_TYPE_PNG))

class App(wx.App):
  def OnInit(self):
    self.tskic = TaskBarIcon()
    window = Window('Discretized Optimized Map Projection')
    window.Show()
    return True

class Window(wx.Frame):
  def __init__(self, title):
    self.__workerThread = None
    self.__renderThread = None
    self.__workerThreadRunning = False
    self.__newImage = None
    self.__isLoadingNewImage = False
    self.__geoGridSettings = GeoGridSettings(resolution=3)
    # self.__simulationSettings = {}
    self.__viewSettings = {}
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
    startMenuItem = addItem(simulationMenu, 'start\tSpace', None, self.onRun)
    stopMenuItem = addItem(simulationMenu, 'stop\tSpace', None, self.onRun)
    addItem(simulationMenu, 'compute next step\tRight', None, self.onRun1)
    addItem(simulationMenu, 'reset\tBack', None, self.onReset)
    simulationMenu.AppendSeparator()
    # # simulation menu: potentials
    # key = 'simulationSelectedPotential'
    # for potential in self.__geoGridSettings.potentials:
    #   addCheckItem(simulationMenu, f"consider {potential.kind.lower()}", self.__simulationSettings, key, potential.kind, self.updateSimulationSettings, default=True)
    # simulationMenu.AppendSeparator()
    # simulation menu: simulation settings
    addItem(simulationMenu, 'simulation settings...\tCtrl+.', None, self.onSimulationSettings)
    # view menu
    viewMenu = wx.Menu()
    menuBar.Append(viewMenu, "&View")
    # view menu: potentials
    key = 'selectedPotential'
    addRadioItem(viewMenu, 'hide forces', self.__viewSettings, key, None, self.updateViewSettings)
    addRadioItem(viewMenu, 'all forces', self.__viewSettings, key, 'ALL', self.updateViewSettings, default=True)
    for potential in self.__geoGridSettings.potentials:
      addRadioItem(viewMenu, f"force for {potential.kind.lower()}", self.__viewSettings, key, potential.kind, self.updateViewSettings)
    viewMenu.AppendSeparator()
    # view menu: visualization method
    key = 'selectedVisualizationMethod'
    addRadioItem(viewMenu, 'sum', self.__viewSettings, key, 'SUM', self.updateViewSettings)
    addRadioItem(viewMenu, 'individually', self.__viewSettings, key, 'INDIVIDUALLY', self.updateViewSettings)
    viewMenu.AppendSeparator()
    # view menu: energy
    key = 'selectedEnergy'
    addRadioItem(viewMenu, 'hide energies', self.__viewSettings, key, None, self.updateViewSettings, default=True)
    addRadioItem(viewMenu, 'all energies', self.__viewSettings, key, 'ALL', self.updateViewSettings)
    for potential in self.__geoGridSettings.potentials:
      addRadioItem(viewMenu, f"energy for {potential.kind.lower()}", self.__viewSettings, key, potential.kind, self.updateViewSettings)
    viewMenu.AppendSeparator()
    # view menu: draw neighbours
    key = 'drawNeighbours'
    addRadioItem(viewMenu, 'hide neighbours', self.__viewSettings, key, False, self.updateViewSettings)
    addRadioItem(viewMenu, 'show neighbours', self.__viewSettings, key, True, self.updateViewSettings)
    viewMenu.AppendSeparator()
    # view menu: draw labels
    key = 'drawLabels'
    addRadioItem(viewMenu, 'hide labels', self.__viewSettings, key, False, self.updateViewSettings)
    addRadioItem(viewMenu, 'show labels', self.__viewSettings, key, True, self.updateViewSettings)
    viewMenu.AppendSeparator()
    # view menu: draw original polygons
    key = 'drawOriginalPolygons'
    addRadioItem(viewMenu, 'hide initial cells', self.__viewSettings, key, False, self.updateViewSettings)
    addRadioItem(viewMenu, 'show initial cells', self.__viewSettings, key, True, self.updateViewSettings)
    viewMenu.AppendSeparator()
    # view menu: draw continents
    key = 'drawContinentsTolerance'
    addRadioItem(viewMenu, 'hide continents', self.__viewSettings, key, False, self.updateViewSettings)
    addRadioItem(viewMenu, 'show strongly simplified continents (faster)', self.__viewSettings, key, 3, self.updateViewSettings)
    addRadioItem(viewMenu, 'show simplified continents (slow)', self.__viewSettings, key, 1, self.updateViewSettings)
    addRadioItem(viewMenu, 'show continents (very slow)', self.__viewSettings, key, 'full', self.updateViewSettings)
    viewMenu.AppendSeparator()
    # view menu: showNthStep
    key = 'showNthStep'
    addRadioItem(viewMenu, 'try to render every step', self.__viewSettings, key, 1, self.updateViewSettings)
    addRadioItem(viewMenu, 'render every 5th step', self.__viewSettings, key, 5, self.updateViewSettings, default=True)
    addRadioItem(viewMenu, 'render every 10th step', self.__viewSettings, key, 10, self.updateViewSettings)
    addRadioItem(viewMenu, 'render every 25th step', self.__viewSettings, key, 25, self.updateViewSettings)
    # finalize
    self.SetMenuBar(menuBar)

    ## tool bar
    # icons
    iconPlay = wx.Icon('assets/play.png', type=wx.BITMAP_TYPE_PNG)
    iconPlay1 = wx.Icon('assets/play1.png', type=wx.BITMAP_TYPE_PNG)
    iconPause = wx.Icon('assets/pause.png', type=wx.BITMAP_TYPE_PNG)
    iconReset = wx.Icon('assets/reset.png', type=wx.BITMAP_TYPE_PNG)
    # functions
    def addTool(id, label, icon, callback):
      tool = toolBar.AddTool(id, label, icon)
      self.Bind(wx.EVT_TOOL, callback, tool)
    # init
    toolBar = self.CreateToolBar()
    addTool(0, 'Run', iconPlay, self.onRun)
    addTool(1, 'Run one step', iconPlay1, self.onRun1)
    addTool(2, 'Reset', iconReset, self.onReset)
    toolBar.Realize()

    # update functions
    def guiPlay(isPlaying):
      # menu
      startMenuItem.Enable(enable=not isPlaying)
      stopMenuItem.Enable(enable=isPlaying)
      # toolbar
      toolBar.SetToolNormalBitmap(0, iconPause if isPlaying else iconPlay)
      toolBar.Realize()
      toolBar.Refresh()
    self._guiPlay = guiPlay

    ## status bar
    self._statusBar = self.CreateStatusBar(3)
    self._statusBar.SetStatusWidths([200, -1, 130])

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
    self.__renderThread = RenderThread(self, self.__viewSettings)
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

  def onSimulationSettings(self, event):
    WindowSimulationSettings(self.__geoGridSettings)

  def onRun(self, event):
    if self.__workerThreadRunning:
      self._guiPlay(False)
      self.__workerThread.pause()
    else:
      self._guiPlay(True)
      self.__workerThread.unpause()
    self.__workerThreadRunning = not self.__workerThreadRunning

  def onRun1(self, event):
    self.__workerThreadRunning = False
    self._guiPlay(False)
    self.__workerThread.unpause1()
  
  def onReset(self, event):
    self.reset()

  def onClose(self, event):
    self.quitThreads()
    self.Destroy()

def runGui():
  app = App(redirect=False)
  app.MainLoop()
