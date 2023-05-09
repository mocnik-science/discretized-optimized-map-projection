import wx
import wx.grid

from src.common.paths import guessProjQGIS
from src.geoGrid.geoGridProjectionTIN import GeoGridProjectionTIN
from src.common.finder import Finder
from src.common.gui import AdvancedGrid, ButtonRenderer

class WindowProj(wx.Frame):
  def __init__(self, appSettings, windowMain):
    self.__appSettings = appSettings
    self.__windowMain = windowMain
    self.__data = {}
    self.__entries = {}
    wx.Frame.__init__(self, None, wx.ID_ANY, title='Projections installed to PROJ/QGIS', size=(700, 600))
    self.SetMinSize((700, 400))
    self.SetMaxSize((700, 800))

    ## layout
    self._panel = wx.Panel(self, style=wx.DEFAULT)
    box = wx.BoxSizer(wx.VERTICAL)

    ## functions
    self.__disabled = {}
    def _bind(evt, element, eventToValue, key, defaultValue, callback):
      self.__data[key] = defaultValue
      def cb(event):
        self.__data[key] = eventToValue(event)
        callback()
      self.Bind(evt, cb, element)
    def _bindWithoutValue(evt, element, callback):
      self.Bind(evt, callback, element)
    def _registerDisabled(disabled, element):
      if element not in self.__disabled:
        self.__disabled[element] = []
      self.__disabled[element] += disabled
    def _registerEntry(entry, key):
      self.__entries[key] = entry
    def label(box, text, disabled=[]):
      labelStaticText = wx.StaticText(self._panel, label=text)
      box.Add(labelStaticText, 0, wx.ALL, 10)
      _registerDisabled(disabled, labelStaticText)
    def text(box, key, callback, defaultValue='', disabled=[], label=None):
      box.AddSpacer(5)
      labelStaticText = wx.StaticText(self._panel, label=label, size=(200, -1))
      box.Add(labelStaticText, 0, wx.ALIGN_CENTRE_VERTICAL, 5)
      textEntry = wx.TextCtrl(self._panel, size=(400, -1))
      box.Add(textEntry, 1, wx.EXPAND|wx.ALIGN_LEFT|wx.ALL, 5)
      _bind(wx.EVT_TEXT, textEntry, lambda event: event.GetString(), key, defaultValue, callback)
      _registerDisabled(disabled, labelStaticText)
      _registerDisabled(disabled, textEntry)
      _registerEntry(textEntry.SetLabelText, key)
      return textEntry
    def button(box, callback, label):
      button = wx.Button(self._panel, label=label)
      box.Add(button, 0, wx.ALL, 5)
      _bindWithoutValue(wx.EVT_BUTTON, button, callback)

    ## content: filename PROJ and QGIS
    box.AddSpacer(5)
    filenameProjQGISBox = wx.BoxSizer(wx.HORIZONTAL)
    filenameProjQGISBox.AddSpacer(5)
    self._filenameProjQGISEntry = text(filenameProjQGISBox, 'filenameProjQGIS', self.onDataUpdate, defaultValue='', label='PROJ file/QGIS app')
    button(filenameProjQGISBox, self.onChooseFilenameProjQGIS, 'Choose file')
    filenameProjQGISBox.AddSpacer(5)
    box.Add(filenameProjQGISBox, 0, wx.ALL, 0)
    box.AddSpacer(8)

    ## content: CRS grid
    self._crsGrid = AdvancedGrid(self._panel)
    self._crsGrid.CreateGrid(0, 7)
    self._crsGrid.SetRowLabelSize(30)
    self._crsGrid.SetColLabelValue(0, '#')
    self._crsGrid.SetColSize(0, 70)
    self._crsGrid.SetColLabelValue(1, 'File')
    self._crsGrid.SetColSize(1, 100)
    self._crsGrid.SetColLabelValue(2, 'PROJ')
    self._crsGrid.SetColSize(2, 100)
    self._crsGrid.SetColLabelValue(3, 'QGIS')
    self._crsGrid.SetColSize(3, 100)
    self._crsGrid.SetColLabelValue(4, '')
    self._crsGrid.SetColSize(4, 100)
    self._crsGrid.SetColLabelValue(5, '')
    self._crsGrid.SetColSize(5, 100)
    self._crsGrid.SetColLabelValue(6, '')
    self._crsGrid.SetColSize(6, 100)
    installedToLabel = {
      GeoGridProjectionTIN.INSTALLED_FULL: 'installed',
      GeoGridProjectionTIN.INSTALLED_PARTLY: 'partly installed',
      GeoGridProjectionTIN.INSTALLED_NOT: 'not installed',
    }
    def crsGridRow(i, data):
      hash, (filenameTIN, installed) = data
      self._crsGrid.SetCellValue(i, 0, hash)
      self._crsGrid.SetReadOnly(i, 0, True)
      self._crsGrid.SetCellValue(i, 1, installedToLabel[installed[GeoGridProjectionTIN.INSTALLED_FILE]])
      self._crsGrid.SetReadOnly(i, 1, True)
      self._crsGrid.SetCellValue(i, 2, installedToLabel[installed[GeoGridProjectionTIN.INSTALLED_PROJ]])
      self._crsGrid.SetReadOnly(i, 2, True)
      self._crsGrid.SetCellValue(i, 3, installedToLabel[installed[GeoGridProjectionTIN.INSTALLED_QGIS]])
      self._crsGrid.SetReadOnly(i, 3, True)
      self._crsGrid.SetCellRenderer(i, 4, ButtonRenderer('Show in Finder', lambda: self.onShowInFinder(filenameTIN), disabled=filenameTIN is None))
      self._crsGrid.SetReadOnly(i, 4, True)
      self._crsGrid.SetCellRenderer(i, 5, ButtonRenderer('(Re)install', lambda: self.onReinstall(filenameTIN, hash), disabled=filenameTIN is None))
      self._crsGrid.SetReadOnly(i, 5, True)
      self._crsGrid.SetCellRenderer(i, 6, ButtonRenderer('Uninstall', lambda: self.onUninstall(hash), isLast=True))
      self._crsGrid.SetReadOnly(i, 6, True)
    self._crsGrid.initRow(crsGridRow)
    box.Add(self._crsGrid, 1, wx.EXPAND)

    ## content: action buttons
    box.AddSpacer(5)
    actionsBox = wx.BoxSizer(wx.HORIZONTAL)
    actionsBox.AddSpacer(5)
    button(actionsBox, self.onUpdateList, 'Update list')
    button(actionsBox, self.onInstallCurrent, 'Install current projection')
    button(actionsBox, self.onInstallFromFile, 'Install from file')
    button(actionsBox, self.onUninstallAll, 'Uninstall all')
    box.Add(actionsBox, 0, wx.ALL, 0)
    box.AddSpacer(2)

    ## content: information
    label(box, '''
Please note:
(1) The installed files (*-tin.json) must not be deleted when being installed as they are accessed during the
      projection of coordinates in PROJ/QGIS.
(2) For technical reasons, a wrong (sic) projection is offered by PROJ as a ‘backup’ to each actual Discrete
      Optimized Map Projection.  To ensure that this wrong backup projection is never used, you have to
      modify the ‘Project Properties’ in QGIS by hand.  In these properties, go to ‘Transformations’ and add
      the transformation ‘EPSG:4326 to DOMP:*’, select the first ‘Transformation’ and disable ‘Allow fallback
      transforms if preferred operation fails’ at the end of the window.
(3) You might need to restart QGIS to guarantee proper functioning after installing projections. 
    '''.strip())

    ## layout
    self._panel.SetSizer(box)
    self._panel.Layout()

    ## init
    self.onInit()

    ## show
    self.Show()

    ## GUI update
    self.onGuiUpdate()

  def onInit(self):
    # init the data
    for key in self.__data.keys():
      if key in self.__appSettings:
        self.__data[key] = self.__appSettings[key]
    if self.__data['filenameProjQGIS'] == '':
      self.__data['filenameProjQGIS'] = guessProjQGIS()
    self.onUpdateList()

  def onGuiUpdate(self):
    # enable and disable elements
    for element, ks in self.__disabled.items():
      if all(self.__data[k] for k in ks):
        element.Enable()
      else:
        element.Disable()
    # update entries
    for key in self.__data.keys():
      if key in self.__entries:
        self.__entries[key](self.__data[key])
    # update table
    if 'installedTIN' in self.__data and self.__data['installedTIN'] is not None:
      self._crsGrid.update(self.__data['installedTIN'].items())

  def onShowInFinder(self, filenameTIN):
    Finder.showFile(filenameTIN)

  def onReinstall(self, filenameTIN, hash):
    GeoGridProjectionTIN.installTIN(self.__appSettings, filenameTIN, hash=hash)
    self.onUpdateList()

  def onUninstall(self, hash):
    GeoGridProjectionTIN.uninstallTIN(self.__appSettings, hash=hash)
    self.onUpdateList()

  def onUpdateList(self, event=None):
    self.__data['installedTIN'] = GeoGridProjectionTIN.collectTINInstalled(self.__appSettings)
    self.onGuiUpdate()

  def onInstallCurrent(self, event=None):
    self.__windowMain.onSaveProjectionTINToDefaultAndInstall()
    self.onUpdateList()

  def onInstallFromFile(self, event=None):
    with wx.FileDialog(self, 'Install TIN projection from file', wildcard='TIN file (*.json)|.json', style=wx.FD_OPEN) as fileDialog:
      if fileDialog.ShowModal() == wx.ID_CANCEL:
        return
      filenameTIN = fileDialog.GetPath()
      dataTIN = self.__windowMain._readFromFile(filenameTIN, 'TIN file')
      if dataTIN is not None:
        installResult = GeoGridProjectionTIN.installTIN(self.__appSettings, filenameTIN, data=dataTIN)
        if installResult is None:
          wx.LogError('Cannot find PROJ file or QGIS app')
        if installResult == False:
          wx.LogError('Error when installing the projection')
      self.onUpdateList()

  def onUninstallAll(self, event=None):
    GeoGridProjectionTIN.uninstallAllTIN(self.__appSettings)
    self.onUpdateList()

  def onDataUpdate(self, fullReload=False):
    # update GUI
    self.onGuiUpdate()
    # update the app settings
    for key in ['filenameProjQGIS']:
      if key not in self.__appSettings or self.__appSettings[key] != self.__data[key]:
        self.__appSettings[key] = self.__data[key]
        self.__appSettings.sync()

  def onChooseFilenameProjQGIS(self, event):
    with wx.FileDialog(self, 'Open PROJ file or QGIS app', wildcard='proj.db (*.db)|.db|QGIS app (*.app)|.app', style=wx.FD_OPEN) as fileDialog:
      if fileDialog.ShowModal() == wx.ID_CANCEL:
        return
      self.__data['filenameProjQGIS'] = fileDialog.GetPath()
    self.onDataUpdate(self)
