#!/usr/bin/env python
#-*- coding: utf8 -*-
'''
Read a QuickNXS bug report and display the most important information.
'''

import sys
import gzip
from cPickle import loads
from quick_nxs.error_handling import REPORT_SAVE_PATH
from quick_nxs.main_gui import MainGUI
from PyQt4.QtGui import QApplication, QMessageBox

def _run(argv=[]):
  app=QApplication(argv)
  if len(argv)==0:
    fname=REPORT_SAVE_PATH
  else:
    fname=argv[0]
  report=loads(gzip.open(fname, 'rb').read())
  report_text=u'''QuickNXS version %(version)s
File: %(active_file)s [%(active_channel)s]


%(traceback)s'''%report
  window=MainGUI(['-ipython'])
  window.debug=report
  window.show()

  dia=QMessageBox(QMessageBox.NoIcon, u'QuickNXS debug information', report_text, parent=window,)
  dia.setModal(False)
  dia.show()
  return app.exec_()

if __name__=='__main__':
  sys.exit(_run(sys.argv[1:]))
