#-*- coding: utf-8 -*-
'''
Create a logging environment more suitable for a daemon process with logging of
debug information to a file and info level for the command line.
As at least two threads are used it adds thread information to the messages.
'''

import sys, os
import logging.handlers

logfile_handler=None

def excepthook_overwrite(*exc_info):
  logging.critical('python error', exc_info=exc_info)

def setup_logging(log_level=logging.INFO, filename='/tmp/quicknxs.log', setup_console=True):
  logger=logging.getLogger()#logging.getLogger('quicknxs')
  logger.setLevel(min(logging.DEBUG, log_level))

  if setup_console:
    # no console logger for windows (py2exe)
    console=logging.StreamHandler(sys.__stdout__)
    formatter=logging.Formatter('%(levelname) 7s - %(threadName)s: %(message)s')
    console.setFormatter(formatter)
    console.setLevel(log_level)
    logger.addHandler(console)

  if os.path.exists(filename):
    rollover=True
  else:
    rollover=False
  logfile=logging.handlers.RotatingFileHandler(filename, encoding='utf8', mode='a',
                                               maxBytes=200*1024**2, backupCount=5)
  if rollover: logfile.doRollover()
  formatter=logging.Formatter('[%(levelname)s] - %(asctime)s - %(threadName)s - %(filename)s:%(lineno)i:%(funcName)s %(message)s', '')
  logfile.setFormatter(formatter)
  logfile.setLevel(logging.DEBUG)
  logger.addHandler(logfile)

  global logfile_handler
  logfile_handler=logfile

  sys.excepthook=excepthook_overwrite
