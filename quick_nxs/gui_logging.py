#-*- coding: utf-8 -*-
'''
  Module used to setup the default GUI logging and messaging system.
  The system contains on a python logging based approach with logfile,
  console output and GUI output dependent on startup options and
  message logLevel.
'''

import os
import sys
import logging

# default options used
CONSOLE_LEVEL=logging.WARNING
FILE_LEVEL=logging.DEBUG
GUI_LEVEL=logging.INFO

USER_DIR=os.path.expanduser('~/.quicknxs')
LOG_DIR=os.path.join(USER_DIR, 'debug.log')
if not os.path.exists(USER_DIR):
  os.makedirs(USER_DIR)

def excepthook_overwrite(*exc_info):
  logging.error('unexpected python error', exc_info=exc_info)

def setup_system():
  logger=logging.root#logging.getLogger('quick_nxs')
  logger.setLevel(logging.DEBUG)
  console=logging.StreamHandler(sys.__stdout__)
  formatter=logging.Formatter('%(levelname) 7s: %(message)s')
  console.setFormatter(formatter)
  console.setLevel(CONSOLE_LEVEL)
  
  logger.addHandler(console)
  logfile=logging.FileHandler(LOG_DIR, 'w')
  formatter=logging.Formatter('[%(levelname)s] - %(asctime)s - %(filename)s:%(lineno)i:%(funcName)s %(message)s',
                              '')
  logfile.setFormatter(formatter)
  logfile.setLevel(FILE_LEVEL)
  logger.addHandler(logfile)
  
  sys.excepthook=excepthook_overwrite
