#-*- coding: utf-8 -*-
'''
  Capture stderr text to be shown to the user as a dialog
  and export information to a file for error analysis.
'''

import os, sys
import gzip
from cPickle import dumps
from PyQt4 import QtGui
from .gui_utils import DelayedTrigger
from .version import str_version


DEVELOPER_EMAIL=u'Artur Glavic <glavicag@ornl.gov>'
# file to write any error report information to
REPORT_SAVE_PATH=os.path.expanduser(u'~/quicknxs_error.pkl.gz')
# MainGUI object attributes to collect together with the traceback
COLLECT_GUI_ATTRIBUTES=['active_file', 'active_channel', 'refl', 'ref_norm', 'reduction_list', ]

class ErrorHandler(QtGui.QWidget):
  '''
    A filelike object to be used to replace sys.stderr.
    Catches each write and shows the result to the user
    in a dialog with a delay to get multiple writes together.
  '''

  def __init__(self, parent):
    QtGui.QWidget.__init__(self)
    self.parent=parent
    self.last_text=u''
    # use a delay threat
    self.trigger=DelayedTrigger()
    # make sure the delay does not coincide with main window delay trigger
    self.trigger.delay=0.2
    self.trigger.activate.connect(self.showError)
    self.trigger.start()

  def write(self, text):
    self.last_text+=text
    # double the error to normal stderr
    sys.__stderr__.write(text)
    self.trigger('error')

  def flush(self): sys.__stderr__.flush()

  def showError(self, _1, _2):
    '''
    Dump error report to gziped file and show an error dialog.
    '''
    try:
      report={'traceback': self.last_text, 'version': str_version}
      for attrib in COLLECT_GUI_ATTRIBUTES:
        report[attrib]=getattr(self.parent, attrib, None)
      report_dump=dumps(report, 2)
      gzip.open(REPORT_SAVE_PATH, 'w').write(report_dump)
      written=True
    except:
      written=False
    traceback=self.last_text
    tbl=traceback.splitlines()
    if len(tbl)>15:
      traceback="\n".join(tbl[:5])+'\n   ...\n'+"\n".join(tbl[-5:])
    if written:
      QtGui.QMessageBox.critical(self.parent,
                        'Unexpected Error',
u'''An unexpected error has occurred, please notify the developer 
  (%s).

The traceback (see below) and debug information 
has been written to "%s".


%s'''%(DEVELOPER_EMAIL, REPORT_SAVE_PATH, traceback))
    else:
      QtGui.QMessageBox.critical(self.parent,
                        'Unexpected Error',
u'''An unexpected error has occurred, please notify the developer 
  (%s).

The traceback (see below) could not be collected or 
written to "%s".


%s'''%(DEVELOPER_EMAIL, REPORT_SAVE_PATH, traceback))
    self.last_text=u''

