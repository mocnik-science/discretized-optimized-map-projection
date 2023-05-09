import os
import shelve
import wx
import wx.adv

from src.app.common import APP_FILES_PATH
from src.app.windows.windowMain import WindowMain

class TaskBarIcon(wx.adv.TaskBarIcon):
  def __init__(self):
    wx.adv.TaskBarIcon.__init__(self, iconType=wx.adv.TBI_DOCK)
    self.SetIcon(wx.Icon('assets/appIcon.png', wx.BITMAP_TYPE_PNG))

class App(wx.App):
  def __init__(self, *args, appSettings=None, **kwargs):
    self.__appSettings = appSettings
    super().__init__(*args, **kwargs)

  def OnInit(self):
    self.tskic = TaskBarIcon()
    windowMain = WindowMain(self.__appSettings)
    windowMain.Show()
    return True

def run():
  os.makedirs(APP_FILES_PATH, exist_ok=True)
  with shelve.open(APP_FILES_PATH + 'settings') as appSettings:
    app = App(redirect=False, appSettings=appSettings)
    app.MainLoop()
