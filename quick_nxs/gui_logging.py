#-*- coding: utf-8 -*-
'''
  Module used to setup the default GUI logging and messaging system.
  The system contains on a python logging based approach with logfile,
  console output and GUI output dependent on startup options and
  message logLevel.
'''

import os
import errno
import sys
import atexit
import logging
import traceback
from .version import str_version
from .config import PATHS, ADMIN_MAIL

# default options used for logging
CONSOLE_LEVEL=logging.WARNING
if '--debug' in sys.argv:
  sys.argv.remove('--debug')
  FILE_LEVEL=logging.DEBUG
else:
  FILE_LEVEL=logging.INFO
GUI_LEVEL=logging.INFO

def excepthook_overwrite(*exc_info):
  logging.critical('python error', exc_info=exc_info)

def ip_excepthook_overwrite(self, etype, value, tb, tb_offset=None):
  logging.critical('python error', exc_info=(etype, value, tb))

def goodby():
  logging.info('*** QuickNXS %s Logging ended ***'%str_version)


def pid_exists(pid):
    """Check whether pid exists in the current process table."""
    if pid<0:
        return False
    try:
        os.kill(pid, 0)
    except OSError, e:
        return e.errno==errno.EPERM
    else:
        return True

def check_runstate():
  '''
  Check for running application by this user.
  '''
  if os.path.exists(PATHS['state_file']):
    pid=int(open(PATHS['state_file']).readline().split()[-1])
    running=pid_exists(pid)
    return running
  else:
    return False

def setup_system():
  logger=logging.getLogger()#logging.getLogger('quick_nxs')
  logger.setLevel(min(FILE_LEVEL, CONSOLE_LEVEL, GUI_LEVEL))
  if not sys.platform.startswith('win'):
    # no console logger for windows (py2exe)
    console=logging.StreamHandler(sys.__stdout__)
    formatter=logging.Formatter('%(levelname) 7s: %(message)s')
    console.setFormatter(formatter)
    console.setLevel(CONSOLE_LEVEL)
    logger.addHandler(console)

  logfile=logging.FileHandler(PATHS['log_file'], 'w')
  formatter=logging.Formatter('[%(levelname)s] - %(asctime)s - %(filename)s:%(lineno)i:%(funcName)s %(message)s', '')
  logfile.setFormatter(formatter)
  logfile.setLevel(FILE_LEVEL)
  logger.addHandler(logfile)

  logging.info('*** QuickNXS %s Logging started ***'%str_version)

  sys.excepthook=excepthook_overwrite
  atexit.register(goodby)

class QtHandler(logging.Handler):
  '''
  A logging Handler to be used by a GUI widget to show the data.
  '''
  max_items=1e5
  info_limit=logging.INFO
  warn_limit=logging.WARNING

  def __init__(self, main_window):
    logging.Handler.__init__(self, level=GUI_LEVEL)
    self.logged_items=[]
    self.reported_bugs=[]
    self.main_window=main_window

  def emit(self, record):
    self.logged_items.append(record)
    # make sure the buffer doesn't get infinitly large
    if len(self.logged_items)>self.max_items:
      self.logged_items.pop(0)
    if record.levelno<=self.info_limit:
      self.show_info(record)
    elif record.levelno<=self.warn_limit:
      self.show_warning(record)
    else:
      self.show_error(record)

  def show_info(self, record):
    msg=record.msg
    if record.levelno!=logging.INFO:
      msg=record.levelname+': '+msg
    self.main_window.ui.statusbar.showMessage(msg, 5000.)
    # make sure the message gets displayed during method executions
    self.main_window.ui.statusbar.update()

  def show_warning(self, record):
    '''
      Warning messages display a dialog to the user.
    '''
    from PyQt4.QtGui import QMessageBox
    QMessageBox.warning(self.main_window, 'QuickNXS '+record.levelname, record.msg)

  def show_error(self, record):
    '''
      More urgent error messages allow to send a bug report.
    '''
    from PyQt4.QtGui import QMessageBox
    from PyQt4.QtCore import Qt
    mbox=QMessageBox(self.main_window)
    mbox.setIcon(QMessageBox.Critical)
    mbox.setTextFormat(Qt.RichText)
    mbox.setInformativeText('Do you want to send the logfile to software support?')
    mbox.setStandardButtons(QMessageBox.Yes|QMessageBox.No)
    mbox.setDefaultButton(QMessageBox.No)
    mbox.setWindowTitle('QuickNXS Error')

    if record.exc_info:
      tb=traceback.format_exception(*record.exc_info)
      message='\n'.join(tb)
      mbox.setDetailedText(message)
      mbox.setText(u'An unexpected error has occurred: <b>%s</b><br />&nbsp;&nbsp;&nbsp;&nbsp;<i>%s</i>: %s'%(
                                    record.msg,
                                    record.exc_info[0].__name__,
                                    record.exc_info[1]))
      if message in self.reported_bugs:
        mbox.setStandardButtons(QMessageBox.Close)
        mbox.setInformativeText('This error has already been reported to the support team.')
    else:
      message=''
      mbox.setText(u'An unexpected error has occurred: <br />&nbsp;&nbsp;<b>%s</b>'%record.msg)
    result=mbox.exec_()
    if result==QMessageBox.Yes:
      logging.info('Sending mail')
      try:
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from getpass import getuser

        msg=MIMEMultipart()
        msg['Subject']='QuickNXS error report'
        msg['From']='%s@ornl.gov'%getuser()
        msg['To']=ADMIN_MAIL
        text='This is an automatic bugreport from QuickNXS\n\n%s'%record.msg
        if record.exc_info:
          text+='\n\n'+message
        text+='\n'
        msg.preamble=text
        msg.attach(MIMEText(text))

        mitem=MIMEText(open(PATHS['log_file'], 'r').read(), 'log')
        mitem.add_header('Content-Disposition', 'attachment', filename='debug.log')
        msg.attach(mitem)

        smtp=smtplib.SMTP('160.91.4.26')
        smtp.sendmail(msg['From'], msg['To'].split(','), msg.as_string())
        smtp.quit()
        logging.info('Mail sent')
      except:
        logging.warning('problem sending the mail', exc_info=True)
      else:
        # after successful email notification the same error is not reported twice
        self.reported_bugs.append(message)

def install_gui_handler(main_window):
  logging.root.addHandler(QtHandler(main_window))
