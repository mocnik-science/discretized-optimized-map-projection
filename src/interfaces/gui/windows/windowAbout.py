import wx

from src.interfaces.common.common import APP_NAME, APP_COPYRIGHT

class WindowAbout(wx.Frame):
  def __init__(self):
    wx.Frame.__init__(self, None, wx.ID_ANY, title=APP_NAME, size=(400, 300))
    self.SetMinSize((400, 300))
    self.SetMaxSize((400, 300))

    ## layout
    self._panel = wx.Panel(self, style=wx.DEFAULT)
    box = wx.BoxSizer(wx.VERTICAL)

    ## functions
    def image(box, filename, size):
      image = wx.Image(filename, wx.BITMAP_TYPE_ANY).ConvertToBitmap()
      bitmap = wx.StaticBitmap(self._panel, -1, image, size=size)
      box.Add(bitmap, 0, wx.ALIGN_CENTRE_HORIZONTAL, 10)
    def text(box, label, fontSize=None):
      staticText = wx.StaticText(self._panel, label=label, style=wx.ALIGN_CENTER_HORIZONTAL)
      if fontSize is not None:
        staticText.SetFont(wx.Font(fontSize, wx.DEFAULT, wx.NORMAL, wx.NORMAL))
      box.Add(staticText, 0, wx.ALIGN_CENTRE_HORIZONTAL, 5)

    ## content
    box.AddSpacer(45)
    image(box, 'assets/globe.png', size=(100, 100))
    box.AddSpacer(10)
    text(box, APP_NAME, fontSize=18)
    box.AddSpacer(30)
    text(box, APP_COPYRIGHT)

    ## layout
    self._panel.SetSizer(box)
    self._panel.Layout()

    ## show
    self.Show()
