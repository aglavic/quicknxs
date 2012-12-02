#!/usr/bin/env python
#-*- coding: utf8 -*-
'''
  Small program for quick access to SNS magnetism reflectometer raw data.
'''

import sys
from quick_nxs.main_gui import MainGUI
from PyQt4.QtGui import QApplication

def _run(argv=[]):
  app=QApplication(argv)
  window=MainGUI(argv)
  window.show()
  return app.exec_()

if __name__=='__main__':
  sys.exit(_run(sys.argv[1:]))
