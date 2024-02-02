import os
import shelve
import wx
import wx.adv

from src.interfaces.common.common import APP_FILES_PATH, APP_SETTINGS_PATH, APP_VIEW_SETTINGS_PATH
from src.interfaces.common.interfaceCommon import InterfaceCommon
from src.interfaces.gui.windows.windowMain import WindowMain

class TaskBarIcon(wx.adv.TaskBarIcon):
  def __init__(self):
    wx.adv.TaskBarIcon.__init__(self, iconType=wx.adv.TBI_DOCK)
    self.SetIcon(wx.Icon('assets/appIcon.png', wx.BITMAP_TYPE_PNG))

class App(wx.App):
  def __init__(self, *args, appSettings=None, viewSettings=None, **kwargs):
    self.__appSettings = appSettings
    self.__viewSettings = viewSettings
    super().__init__(*args, **kwargs)

  def OnInit(self):
    self.tskic = TaskBarIcon()
    windowMain = WindowMain(self.__appSettings, self.__viewSettings)
    windowMain.Show()
    return True

def run():
  os.makedirs(APP_FILES_PATH, exist_ok=True)
  with shelve.open(APP_SETTINGS_PATH) as appSettings:
    with shelve.open(APP_VIEW_SETTINGS_PATH) as viewSettings:
      app = App(redirect=False, appSettings=appSettings, viewSettings=viewSettings)
      app.MainLoop()
  InterfaceCommon.cleanup()
