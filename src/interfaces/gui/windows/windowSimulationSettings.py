import wx

from src.geometry.geo import Geo
from src.geoGrid.geoGridWeight import GeoGridWeight

class WindowSimulationSettings(wx.Frame):
  def __init__(self, appSettings, geoGridSettings, workerThread):
    self.__appSettings = appSettings
    self.__geoGridSettings = geoGridSettings
    self.__workerThread = workerThread
    self.__data = {}
    size = (840, 330)
    wx.Frame.__init__(self, None, wx.ID_ANY, title='Simulation Settings', size=size)
    self.SetMinSize(size)
    self.SetMaxSize(size)

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
    def staticText(box, label):
      staticText = wx.StaticText(self._panel, label=label)
      box.Add(staticText, 0, wx.ALIGN_CENTRE_VERTICAL, 5)
      return staticText
    def number(box, key, callback, defaultValue=1, minValue=0, maxValue=100, digits=0, increment=1, disabled=[], label=None, unit=None):
      box.AddSpacer(5)
      labelStaticText = staticText(box, label)
      numberEntry = wx.SpinCtrlDouble(self._panel)
      numberEntry.SetMin(minValue)
      numberEntry.SetMax(maxValue)
      numberEntry.SetDigits(digits)
      numberEntry.SetValue(defaultValue)
      numberEntry.SetIncrement(increment)
      numberEntry.SetLabel(label)
      box.Add(numberEntry, 0, wx.ALL, 5)
      _bind(wx.EVT_SPINCTRLDOUBLE, numberEntry, lambda event: event.GetValue(), key, defaultValue, callback)
      _registerDisabled(disabled, labelStaticText)
      _registerDisabled(disabled, numberEntry)
      if unit is not None:
        labelStaticTextAfter = wx.StaticText(self._panel, label=unit)
        box.Add(labelStaticTextAfter, 0, wx.ALIGN_CENTRE_VERTICAL, 5)
        _registerDisabled(disabled, labelStaticTextAfter)
    def weightNumber(box, key, callback, defaultValue=1, disabled=[], label=None):
      number(box, key, callback, defaultValue=defaultValue, minValue=0, maxValue=100, digits=2, increment=.1, disabled=disabled, label=label)
    def distanceNumber(box, key, callback, defaultValue=1, disabled=[], label=None, unit=None):
      number(box, key, callback, defaultValue=defaultValue, minValue=0, maxValue=Geo.radiusEarth / 1000, digits=2, increment=1, disabled=disabled, label=label, unit=unit)
    def checkBox(box, key, callback, defaultValue=True, disabled=[], proportion=0, **kwargs):
      checkBox = wx.CheckBox(self._panel, **kwargs)
      checkBox.SetValue(defaultValue)
      box.Add(checkBox, proportion, wx.EXPAND, 5)
      _bind(wx.EVT_CHECKBOX, checkBox, lambda event: event.IsChecked(), key, defaultValue, callback)
      _registerDisabled(disabled, checkBox)

    ## content: resolution and speed
    box.AddSpacer(5)
    generalSettingsBox1 = wx.BoxSizer(wx.HORIZONTAL)
    generalSettingsBox1.AddSpacer(5)
    gap = 140
    number(generalSettingsBox1, 'resolution', lambda: self.onDataUpdate(fullReload=True), defaultValue=self.__geoGridSettings.resolution, minValue=2, maxValue=10, label='resolution:')
    generalSettingsBox1.AddSpacer(gap)
    number(generalSettingsBox1, 'limitLatForEnergy', self.onDataUpdate, defaultValue=self.__geoGridSettings.limitLatForEnergy, minValue=45, maxValue=90, digits=0, increment=1, label='limit latitude (energy computation):', unit='°N/S')
    generalSettingsBox1.AddSpacer(gap)
    number(generalSettingsBox1, 'speed100', self.onDataUpdate, defaultValue=100 * (1 - self.__geoGridSettings._dampingFactor), minValue=.1, maxValue=20, digits=2, increment=.1, label='speed:')
    box.Add(generalSettingsBox1, 0, wx.ALL, 0)
    generalSettingsBox2 = wx.BoxSizer(wx.HORIZONTAL)
    generalSettingsBox2.AddSpacer(10)
    gap = 20
    staticText(generalSettingsBox2, 'stop')
    generalSettingsBox2.AddSpacer(gap)
    number(generalSettingsBox2, 'stopThresholdMaxForceStrength100', self.onDataUpdate, defaultValue=100 * self.__geoGridSettings._stopThresholdMaxForceStrength, minValue=.01, maxValue=2, digits=2, increment=.1, label='… when max force below:', unit='%')
    generalSettingsBox2.AddSpacer(gap)
    number(generalSettingsBox2, 'stopThresholdCountDeficiencies', self.onDataUpdate, defaultValue=self.__geoGridSettings._stopThresholdCountDeficiencies, minValue=1, maxValue=1000, digits=0, increment=1, label='… when exceeding deficiencies:')
    generalSettingsBox2.AddSpacer(gap)
    number(generalSettingsBox2, 'stopThresholdMaxSteps', self.onDataUpdate, defaultValue=self.__geoGridSettings._stopThresholdMaxSteps, minValue=1, maxValue=50000, digits=0, increment=1, label='… when exceeding steps:')
    box.Add(generalSettingsBox2, 0, wx.ALL, 0)
    box.AddSpacer(8)
    generalSettingsBox3 = wx.BoxSizer(wx.HORIZONTAL)
    generalSettingsBox3.AddSpacer(10)
    checkBox(generalSettingsBox3, 'normalizeWeights', self.onDataUpdate, defaultValue=self.__geoGridSettings._normalizeWeights, label='normalize weights')
    box.Add(generalSettingsBox3, 0, wx.ALL, 0)
    box.AddSpacer(8)

    ## content: weights
    for weight, potential in self.__geoGridSettings.weightedPotentials():
      potentialBox = wx.BoxSizer(wx.HORIZONTAL)
      potentialBox.AddSpacer(10)
      checkBox(potentialBox, potential.kind, self.onDataUpdate, defaultValue=weight.isActive(), proportion=1, label=potential.kind.lower().replace('_', ' ') + ':', size=(200, -1))
      potentialBox.AddSpacer(20)
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

  def onDataUpdate(self, fullReload=False):
    # update GUI
    self.onGuiUpdate()
    # update the app settings I
    keys = [
      'resolution',
      'speed100',
      'stopThresholdMaxForceStrength100',
      'stopThresholdCountDeficiencies',
      'stopThresholdMaxSteps',
      'limitLatForEnergy',
    ]
    for potential in self.__geoGridSettings.potentials:
      keys += [
        potential.kind,
        potential.kind + '-weight',
        potential.kind + '-ocean-weight',
        potential.kind + '-ocean',
        potential.kind + '-distanceTransitionStart',
        potential.kind + '-distanceTransitionEnd',
      ]
    hasChanged = False
    for key in keys:
      if key not in self.__appSettings or self.__appSettings[key] != self.__data[key]:
        hasChanged = True
    # update geoGridSettings: weights
    weights = {}
    for potential in self.__geoGridSettings.potentials:
      active = self.__data[potential.kind]
      weightLand = self.__data[potential.kind + '-weight']
      weightOcean = self.__data[potential.kind + '-ocean-weight']
      weightOceanActive = self.__data[potential.kind + '-ocean']
      distanceTransitionStart = self.__data[potential.kind + '-distanceTransitionStart'] * 1000
      distanceTransitionEnd = self.__data[potential.kind + '-distanceTransitionEnd'] * 1000
      weights[potential.kind] = GeoGridWeight(active=active, weightLand=weightLand, weightOceanActive=weightOceanActive, weightOcean=weightOcean, distanceTransitionStart=distanceTransitionStart, distanceTransitionEnd=distanceTransitionEnd)
      self.__geoGridSettings.updatePotentialsWeights(weights)
    # update geoGridSettings: resolution
    self.__geoGridSettings.updateResolution(round(self.__data['resolution']))
    # update geoGridSettings: damping factor
    self.__geoGridSettings.updateDampingFactor(1 - self.__data['speed100'] / 100)
    # update geoGridSettings: stop threshold max force strength
    self.__geoGridSettings.updateStopThresholdMaxForceStrength(self.__data['stopThresholdMaxForceStrength100'] / 100)
    # update geoGridSettings: stop threshold count deficiencies
    self.__geoGridSettings.updateStopThresholdCountDeficiencies(self.__data['stopThresholdCountDeficiencies'])
    # update geoGridSettings: stop threshold max steps
    self.__geoGridSettings.updateStopThresholdMaxSteps(self.__data['stopThresholdMaxSteps'])
    # update geoGridSettings: limit latitude for energy
    self.__geoGridSettings.updateLimitLatForEnergy(self.__data['limitLatForEnergy'])
    # update geoGridSettings: normalize weights
    self.__geoGridSettings.updateNormalizeWeights(self.__data['normalizeWeights'])
    # update the app settings II
    if hasChanged:
      self.__appSettings['geoGridSettings'] = self.__geoGridSettings.toJSON()
      self.__appSettings.sync()
    # full reload or just update the view
    if fullReload:
      self.__workerThread.fullReload()
    else:
      self.__workerThread.update()
