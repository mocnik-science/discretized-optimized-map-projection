import wx
import wx.adv

from src.app.workerThread import *
from src.geoGrid.geoGrid import *

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
    self.__worker = None
    self.__workerRunning = False
    self.__newImage = None
    self.__isLoadingNewImage = False
    self.__geoGridSettings = GeoGridSettings(resolution=3)
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
    def addRadioItem(menu, label, object, key, data, callback):
      newId = wx.NewId()
      self.__menuDict[newId] = data
      menuItem = menu.Append(newId, label, label, wx.ITEM_RADIO)
      def cb(event):
        object[key] = self.__menuDict[event.Id]
        callback()
      self.Bind(wx.EVT_MENU, cb, menuItem)
      if key not in object:
        object[key] = data
    # init
    menuBar = wx.MenuBar()
    # view menu
    viewMenu = wx.Menu()
    menuBar.Append(viewMenu, "&View")
    # view menu: potentials
    key = 'selectedPotential'
    addRadioItem(viewMenu, 'all forces', self.__viewSettings, key, 'ALL', self.updateViewSettings)
    for potential in self.__geoGridSettings.potentials:
      addRadioItem(viewMenu, f"force for {potential.kind.lower()}", self.__viewSettings, key, potential.kind, self.updateViewSettings)
    viewMenu.AppendSeparator()
    # view menu: visualization method
    key = 'selectedVisualizationMethod'
    addRadioItem(viewMenu, 'sum', self.__viewSettings, key, 'SUM', self.updateViewSettings)
    addRadioItem(viewMenu, 'individually', self.__viewSettings, key, 'INDIVIDUALLY', self.updateViewSettings)
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
    addTool(0, 'Run', iconPlay, self.onButtonRun)
    addTool(1, 'Run one step', iconPlay1, self.onButtonRun1)
    addTool(2, 'Reset', iconReset, self.onButtonReset)
    toolBar.Realize()
    # update functions
    def toolPlayIconPlay(isPlaying):
      toolBar.SetToolNormalBitmap(0, iconPause if isPlaying else iconPlay)
      toolBar.Realize()
      toolBar.Refresh()
    self._toolPlayIconPlay = toolPlayIconPlay

    ## status bar
    self._statusBar = self.CreateStatusBar(2)
    self._statusBar.SetStatusWidths([-1, 130])

    ## layout
    self._panel = wx.Panel(self, style=wx.DEFAULT)
    box = wx.BoxSizer(wx.VERTICAL)

    ## image
    self._image = wx.StaticBitmap(self._panel)
    self._image.SetBackgroundColour(wx.WHITE)
    box.Add(self._image, 1, wx.EXPAND)

    # ## text
    # text = wx.StaticText(panel, label='Hello world')
    # box.Add(text, 0, wx.ALL, 10)

    # ## button
    # buttonRun = wx.Button(panel, label='Run')
    # buttonRun.Bind(wx.EVT_BUTTON, self.onButtonRun)
    # box.Add(buttonRun, 0, wx.ALL, 10)

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
    wx.FutureCall(10, self.reset)

  def updateViewSettings(self):
    self.__worker.updateViewSettings(self.__viewSettings)

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
        im2 = wx.EmptyImage(*im.size)
        im2.SetData(im.convert('RGB').tobytes())
        self._image.SetBitmap(wx.BitmapFromImage(im2))
        self._panel.Layout()
      except:
        pass
    self.__isLoadingNewImage = False

  def setStatus(self, text):
    try:
      self._statusBar.SetStatusText(text)
    except:
      pass

  def setEnergy(self, energy):
    try:
      self._statusBar.SetStatusText(f"energy = {energy:.2E}", 1)
    except:
      pass

  def reset(self):
    if self.__worker is not None:
      self.__worker.pause()
    self.__workerRunning = False
    self._toolPlayIconPlay(False)
    self.__newImage = None
    self.__isLoadingNewImage = False
    self.prepareWorkerThread()

  def prepareWorkerThread(self):
    EVT_WORKER_THREAD_UPDATE(self, self.__workerThreadUpdate)
    self.__worker = WorkerThread(self, self.__geoGridSettings, self.__viewSettings)
  
  def __workerThreadUpdate(self, event):
    if self.__worker is None:
      return
    if event.im is not None:
      self.loadImage(event.im)
    if event.status is not None:
      self.setStatus(event.status)
    if event.energy is not None:
      self.setEnergy(event.energy)

  def onButtonRun(self, event):
    if self.__workerRunning:
      self._toolPlayIconPlay(False)
      self.__worker.pause()
    else:
      self._toolPlayIconPlay(True)
      self.__worker.unpause()
    self.__workerRunning = not self.__workerRunning

  def onButtonRun1(self, event):
    self.__worker.unpause1()
  
  def onButtonReset(self, event):
    self.reset()

  def onClose(self, event):
    if self.__worker is not None:
      self.__worker.quit()
    self.__worker = None
    self.Destroy()

def runGui():
  app = App(redirect=False)
  app.MainLoop()
