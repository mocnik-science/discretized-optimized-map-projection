import wx

class AdvancedGrid(wx.grid.Grid):
  def __init__(self, parent):
    super().__init__(parent)
    self.__grid = self
    self.__grid.Bind(wx.grid.EVT_GRID_CELL_LEFT_DCLICK, self.onLeftDClick)
    self.__grid.GetGridWindow().Bind(wx.EVT_LEFT_DOWN, self.onLeftDown)
    self.__grid.GetGridWindow().Bind(wx.EVT_LEFT_UP, self.onLeftUp)
    self.__row = None
    self.__data = None

  def initRow(self, row):
    self.__row = row

  def update(self, data):
    if data is None or not self.__row:
      return
    self.__data = data
    n = len(self.__data) - self.GetNumberRows()
    if n > 0:
      self.AppendRows(n)
    elif n < 0:
      self.DeleteRows(0, -n)
    for i, d in enumerate(self.__data):
      self.__row(i, d)

  def _isValidRow(self, row):
    return row < len(self.__data)

  def onLeftDClick(self, evt):
    if self.__grid.CanEnableCellControl():
      self.__grid.EnableCellEditControl()

  def onLeftDown(self, evt):
    col, row = self.__hitTestCell(evt.GetPosition().x, evt.GetPosition().y)
    if not self._isValidRow(row):
      return
    if isinstance(self.__grid.GetCellRenderer(row, col), ButtonRenderer):
      self.__grid.GetCellRenderer(row, col)._down = True
    self.__grid.Refresh()
    evt.Skip()

  def onLeftUp(self, evt):
    col, row = self.__hitTestCell(evt.GetPosition().x, evt.GetPosition().y)
    if not self._isValidRow(row):
      return
    if isinstance(self.__grid.GetCellRenderer(row, col), ButtonRenderer):
      self.__grid.GetCellRenderer(row, col)._down = False
      self.__grid.GetCellRenderer(row, col)._click_handled = False
    self.__grid.Refresh()
    evt.Skip()

  def __hitTestCell(self, x, y):
    x, y = self.__grid.CalcUnscrolledPosition(x, y)
    return self.__grid.XToCol(x), self.__grid.YToRow(y)

class ButtonRenderer(wx.grid.GridCellRenderer):
  def __init__(self, label, callback, disabled=False, isLast=False):
    wx.grid.GridCellRenderer.__init__(self)
    self.__label = label
    self.__callback = callback
    self.__disabled = disabled
    self.__isLast = isLast
    self._down = False
    self._click_handled = False

  def Draw(self, grid, attr, dc, rect, row, col, isSelected):
    # if self.__isLast:
    #   dc.Clear()
    if True or not self.__disabled:
      flags = (wx.CONTROL_PRESSED | wx.CONTROL_SELECTED) if self._down and not self.__disabled else 0
      wx.RendererNative.Get().DrawPushButton(grid, dc, rect, flags)
    dc.SetTextForeground(wx.ColourDatabase().Find('GREY') if self.__disabled else wx.BLACK)
    wx.RendererNative.Get().DrawItemText(grid, dc, self.__label, rect, align=wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL)
    if not self.__disabled and self._down and not self._click_handled:
      self._click_handled = True
      wx.CallAfter(self.HandleClick)

  def HandleClick(self):
    self.__callback()

  def GetBestSize(self, grid, attr, dc, row, col):
    dc.SetFont(attr.GetFont())
    return wx.Size(*dc.GetTextExtent(self.__label))

  def Clone(self):
    return ButtonRenderer()
