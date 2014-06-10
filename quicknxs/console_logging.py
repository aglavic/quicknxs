#-*- coding: utf-8 -*-
'''
Create a logging environment more suitable for a daemon process with logging of
debug information to a file and info level for the command line.
As at least two threads are used it adds thread information to the messages.
'''

import sys
import logging
from .config import paths

def setup_logging():
  logger=logging.getLogger()#logging.getLogger('quicknxs')
  logger.setLevel(logging.DEBUG)

  # no console logger for windows (py2exe)
  console=logging.StreamHandler(sys.__stdout__)
  formatter=logging.Formatter('%(levelname) 7s - %(threadName)s: %(message)s')
  console.setFormatter(formatter)
  console.setLevel(logging.INFO)
  logger.addHandler(console)

  logfile=logging.FileHandler(paths.AUTOREFL_LOG_FILE, 'w')
  formatter=logging.Formatter('[%(levelname)s] - %(asctime)s - %(threadName)s - %(filename)s:%(lineno)i:%(funcName)s %(message)s', '')
  logfile.setFormatter(formatter)
  logfile.setLevel(logging.DEBUG)
  logger.addHandler(logfile)
