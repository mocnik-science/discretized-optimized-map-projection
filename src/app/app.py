import wx
import wx.adv

from src.app.common import APP_NAME
from src.app.windowMain import WindowMain

class TaskBarIcon(wx.adv.TaskBarIcon):
  def __init__(self):
    wx.adv.TaskBarIcon.__init__(self, iconType=wx.adv.TBI_DOCK)
    self.SetIcon(wx.Icon('assets/appIcon.png', wx.BITMAP_TYPE_PNG))

class App(wx.App):
  def OnInit(self):
    self.tskic = TaskBarIcon()
    windowMain = WindowMain(APP_NAME)
    windowMain.Show()
    return True

def run():
  app = App(redirect=False)
  app.MainLoop()
