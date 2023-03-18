import wx
import wx.adv

from src.geoGrid.geoGrid import *
from src.workerThread import *

class TaskBarIcon(wx.adv.TaskBarIcon):
  def __init__(self):
    wx.adv.TaskBarIcon.__init__(self, iconType=wx.adv.TBI_DOCK)
    self.SetIcon(wx.Icon('assets/map.png', wx.BITMAP_TYPE_PNG))

class App(wx.App):
  def OnInit(self):
    self.tskic = TaskBarIcon()
    window = Window('Map Projection')
    window.Show()
    return True

class Window(wx.Frame):
  def __init__(self, title):
    self.__worker = None
    self.__workerRunning = False
    self.__imNew = None
    self.__geoGridSettings = GeoGridSettings(resolution=3)
    self.__viewSettings = {}
    wx.Frame.__init__(self, None, wx.ID_ANY, title=title, size=(900, 600))

    ## menu bar
    menuBar = wx.MenuBar()
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
    # finalize
    self.SetMenuBar(menuBar)

    ## tool bar
    # icons
    iconPlay = wx.Icon('assets/play.png', type=wx.BITMAP_TYPE_PNG)
    iconPlay1 = wx.Icon('assets/play1.png', type=wx.BITMAP_TYPE_PNG)
    iconPause = wx.Icon('assets/pause.png', type=wx.BITMAP_TYPE_PNG)
    # init
    toolBar = self.CreateToolBar()
    toolBar.AddTool(0, 'Run', iconPlay)
    self.Bind(wx.EVT_TOOL, self.onButtonRun, id=0)
    toolBar.AddTool(1, 'Run one step', iconPlay1)
    self.Bind(wx.EVT_TOOL, self.onButtonRun1, id=1)
    toolBar.Realize()
    # update functions
    def toolPlayIconPlay(isPlaying):
      toolBar.SetToolNormalBitmap(0, iconPause if isPlaying else iconPlay)
      toolBar.Realize()
      toolBar.Refresh()
    self._toolPlayIconPlay = toolPlayIconPlay

    ## status bar
    self._statusBar = self.CreateStatusBar()
    self.setStatus('')

    ## layout
    self._panel = wx.Panel(self, style=wx.RAISED_BORDER)
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

    ## prepare worker thread
    wx.FutureCall(10, self.prepareWorkerThread)
    wx.FutureCall(10, self.prepareImageUpdate)

  def updateViewSettings(self):
    self.__worker.updateViewSettings(self.__viewSettings)

  def prepareImageUpdate(self):
    while True:
      wx.Yield()
      if self.__imNew is not None:
        im = self.__imNew
        self.__imNew = None
        im2 = wx.EmptyImage(*im.size)
        im2.SetData(im.convert('RGB').tobytes())
        self._image.SetBitmap(wx.BitmapFromImage(im2))
        self._panel.Layout()

  def loadImage(self, filename):
    self.__imNew = filename

  def setStatus(self, text):
    self._statusBar.SetStatusText(text)

  def prepareWorkerThread(self):
    EVT_WORKER_THREAD_UPDATE(self, self.__workerThreadUpdate)
    self.__worker = WorkerThread(self, self.__geoGridSettings, self.__viewSettings)
  
  def __workerThreadUpdate(self, event):
    if event.im is not None:
      self.loadImage(event.im)
    if event.status is not None:
      self.setStatus(event.status)

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

def runGui():
  app = App(redirect=False)
  app.MainLoop()
