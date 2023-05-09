import os
import subprocess
from sys import platform

class Finder:
  @staticmethod
  def isMacOS():
    return platform.startswith('darwin')
  @staticmethod
  def isLinux():
    return platform.startswith('linux')
  @staticmethod
  def isWindows():
    return platform.startswith('win')

  @staticmethod
  def showFile(filename):
    if Finder.isMacOS():
      subprocess.run(['open', '--reveal', filename])
    if Finder.isLinux():
      subprocess.run(['nautilus', filename])
    if Finder.isWindows():
      subprocess.run(['explorer', os.path.split(filename)[0]])
