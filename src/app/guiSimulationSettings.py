import wx

from src.geoGrid.geoGridWeight import GeoGridWeight

class WindowSimulationSettings(wx.Frame):
  def __init__(self, geoGridSettings):
    self.__geoGridSettings = geoGridSettings
    self.__data = {}
    wx.Frame.__init__(self, None, wx.ID_ANY, title='Simulation Settings', size=(400, 200))
    self.SetMinSize((400, 200))
    self.SetMaxSize((400, 200))

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
    def weight(box, key, callback, defaultValue=1, disabled=[], label=None):
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

    ## content
    for potential in self.__geoGridSettings.potentials:
      box.AddSpacer(5)
      potentialBox = wx.BoxSizer(wx.HORIZONTAL)
      potentialBox.AddSpacer(10)
      checkBox(potentialBox, potential.kind, self.onDataUpdate, proportion=1, label=potential.kind.lower(), size=(200, -1))
      weight(potentialBox, potential.kind + '-weight', self.onDataUpdate, disabled=[potential.kind], label='land')
      potentialBox.AddSpacer(5)
      checkBox(potentialBox, potential.kind + '-ocean', self.onDataUpdate, defaultValue=False, disabled=[potential.kind])
      weight(potentialBox, potential.kind + '-ocean-weight', self.onDataUpdate, disabled=[potential.kind, potential.kind + '-ocean'], label='ocean')
      potentialBox.AddSpacer(5)
      box.Add(potentialBox, 0, wx.ALL, 0)

    ## layout
    self._panel.SetSizer(box)
    self._panel.Layout()

    ## show
    self.Show()

  def onDataUpdate(self):
    # enable and disable elements
    for element, ks in self.__disabled.items():
      if all(self.__data[k] for k in ks):
        element.Enable()
      else:
        element.Disable()
    # update geoGridSettings
    weights = {}
    for potential in self.__geoGridSettings.potentials:
      if not self.__data[potential.kind]:
        weights[potential.kind] = None
      else:
        weights[potential.kind] = GeoGridWeight(weightLand=self.__data[potential.kind + '-weight'], weightOcean=self.__data[potential.kind + '-ocean-weight'] if self.__data[potential.kind + '-ocean'] else self.__data[potential.kind + '-weight'])
    self.__geoGridSettings.updatePotentialsWeights(weights)
