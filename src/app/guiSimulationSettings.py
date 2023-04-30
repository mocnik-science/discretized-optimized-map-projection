import wx

from src.geometry.geo import radiusEarth
from src.geoGrid.geoGridWeight import GeoGridWeight

class WindowSimulationSettings(wx.Frame):
  def __init__(self, geoGridSettings, renderThread):
    self.__geoGridSettings = geoGridSettings
    self.__renderThread = renderThread
    self.__data = {}
    wx.Frame.__init__(self, None, wx.ID_ANY, title='Simulation Settings', size=(800, 200))
    self.SetMinSize((800, 200))
    self.SetMaxSize((800, 200))

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
    def _registerDisabled(disabled, element):
      if element not in self.__disabled:
        self.__disabled[element] = []
      self.__disabled[element] += disabled
    def weightNumber(box, key, callback, defaultValue=1, disabled=[], label=None):
      box.AddSpacer(5)
      labelStaticText = wx.StaticText(self._panel, label=label)
      box.Add(labelStaticText, 0, wx.ALIGN_CENTRE_VERTICAL, 5)
      weightNumberEntry = wx.SpinCtrlDouble(self._panel)
      weightNumberEntry.SetMin(0)
      weightNumberEntry.SetDigits(2)
      weightNumberEntry.SetIncrement(.1)
      weightNumberEntry.SetValue(defaultValue)
      weightNumberEntry.SetLabel(label)
      box.Add(weightNumberEntry, 0, wx.ALL, 5)
      _bind(wx.EVT_SPINCTRLDOUBLE, weightNumberEntry, lambda event: event.GetValue(), key, defaultValue, callback)
      _registerDisabled(disabled, labelStaticText)
      _registerDisabled(disabled, weightNumberEntry)
    def checkBox(box, key, callback, defaultValue=True, disabled=[], proportion=0, **kwargs):
      checkBox = wx.CheckBox(self._panel, **kwargs)
      checkBox.SetValue(defaultValue)
      box.Add(checkBox, proportion, wx.EXPAND, 5)
      _bind(wx.EVT_CHECKBOX, checkBox, lambda event: event.IsChecked(), key, defaultValue, callback)
      _registerDisabled(disabled, checkBox)
    def distanceNumber(box, key, callback, defaultValue=1, disabled=[], label=None, unit=None):
      box.AddSpacer(5)
      labelStaticText = wx.StaticText(self._panel, label=label)
      box.Add(labelStaticText, 0, wx.ALIGN_CENTRE_VERTICAL, 5)
      distanceNumberEntry = wx.SpinCtrlDouble(self._panel)
      distanceNumberEntry.SetMin(0)
      distanceNumberEntry.SetMax(radiusEarth / 1000)
      distanceNumberEntry.SetDigits(2)
      distanceNumberEntry.SetIncrement(1)
      distanceNumberEntry.SetValue(defaultValue)
      distanceNumberEntry.SetLabel(label)
      box.Add(distanceNumberEntry, 0, wx.ALL, 5)
      _bind(wx.EVT_SPINCTRLDOUBLE, distanceNumberEntry, lambda event: event.GetValue(), key, defaultValue, callback)
      if unit is not None:
        labelStaticTextAfter = wx.StaticText(self._panel, label=unit)
        box.Add(labelStaticTextAfter, 0, wx.ALIGN_CENTRE_VERTICAL, 5)
      _registerDisabled(disabled, labelStaticText)
      _registerDisabled(disabled, distanceNumberEntry)
      if unit is not None:
        _registerDisabled(disabled, labelStaticTextAfter)

    ## content: weights
    for weight, potential in self.__geoGridSettings.weightedPotentials(allWeights=True):
      box.AddSpacer(5)
      potentialBox = wx.BoxSizer(wx.HORIZONTAL)
      potentialBox.AddSpacer(10)
      checkBox(potentialBox, potential.kind, self.onDataUpdate, defaultValue=weight.isActive(), proportion=1, label=potential.kind.lower(), size=(200, -1))
      weightNumber(potentialBox, potential.kind + '-weight', self.onDataUpdate, defaultValue=weight.weightLand(), disabled=[potential.kind], label='land')
      potentialBox.AddSpacer(5)
      checkBox(potentialBox, potential.kind + '-ocean', self.onDataUpdate, defaultValue=weight.isWeightOceanActive(), disabled=[potential.kind])
      weightNumber(potentialBox, potential.kind + '-ocean-weight', self.onDataUpdate, defaultValue=weight.weightOcean(), disabled=[potential.kind, potential.kind + '-ocean'], label='ocean')
      potentialBox.AddSpacer(5)
      distanceNumber(potentialBox, potential.kind + '-distanceTransitionStart', self.onDataUpdate, defaultValue=weight.distanceTransitionStart() / 1000, disabled=[potential.kind, potential.kind + '-ocean'], label='transition between')
      distanceNumber(potentialBox, potential.kind + '-distanceTransitionEnd', self.onDataUpdate, defaultValue=weight.distanceTransitionEnd() / 1000, disabled=[potential.kind, potential.kind + '-ocean'], label='and', unit='km')
      potentialBox.AddSpacer(5)
      box.Add(potentialBox, 0, wx.ALL, 0)

    ## layout
    self._panel.SetSizer(box)
    self._panel.Layout()

    ## show
    self.Show()

    ## GUI update
    self.onGuiUpdate()

  def onGuiUpdate(self):
    # enable and disable elements
    for element, ks in self.__disabled.items():
      if all(self.__data[k] for k in ks):
        element.Enable()
      else:
        element.Disable()

  def onDataUpdate(self):
    # update GUI
    self.onGuiUpdate()
    # update geoGridSettings
    weights = {}
    for potential in self.__geoGridSettings.potentials:
      active = self.__data[potential.kind]
      weightLand = self.__data[potential.kind + '-weight']
      weightOcean = self.__data[potential.kind + '-ocean-weight'] if self.__data[potential.kind + '-ocean'] else self.__data[potential.kind + '-weight']
      weightOceanActive = self.__data[potential.kind + '-ocean']
      distanceTransitionStart = self.__data[potential.kind + '-distanceTransitionStart'] * 1000
      distanceTransitionEnd = self.__data[potential.kind + '-distanceTransitionEnd'] * 1000
      weights[potential.kind] = GeoGridWeight(active=active, weightLand=weightLand, weightOceanActive=weightOceanActive, weightOcean=weightOcean, distanceTransitionStart=distanceTransitionStart, distanceTransitionEnd=distanceTransitionEnd)
    self.__geoGridSettings.updatePotentialsWeights(weights)
    self.__renderThread.updateView()
