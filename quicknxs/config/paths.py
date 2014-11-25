#-*- coding: utf-8 -*-
'''
Configured path variables.
'''

import os, sys

config_file=''
from getpass import getuser

# define global path variables usable in config strings or other modules
HOME=os.path.expanduser(u'~')
CFG_PATH=os.path.join(HOME, u'.quicknxs')
CFG_FILE=os.path.join(CFG_PATH, u'config.cfg')
if sys.version_info[0]>=3:
  USER=getuser()
  # path to the quicknxs package
  PACKAGE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
else:
  USER=unicode(getuser(), 'utf8')
  # path to the quicknxs package
  PACKAGE=unicode(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'utf8')
if not os.path.exists(CFG_PATH):
  os.makedirs(CFG_PATH)

results=u'%(HOME)s/results'
export_name=u'%(instrument.NAME)s_{numbers}_{item}_{state}.{type}'
DOC_INDEX=u'%(PACKAGE)s/htmldoc/node3.html'
STATE_FILE=u'%(CFG_PATH)s/run_state.dat'
LOG_FILE=u'%(CFG_PATH)s/debug.log'
AUTOREFL_LOG_FILE=u'%(CFG_PATH)s/autorefl.log'
GENX_TEMPLATES=u'%(PACKAGE)s/genx_templates'
