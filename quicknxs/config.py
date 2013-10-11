#-*- coding: utf-8 -*-
'''
Global configurations for e.g. default paths etc. Some of these are stored
in the users account for easy changes.
'''

import os
import sys
import atexit
from ConfigParser import SafeConfigParser
from getpass import getuser

# define global path variables usable in config strings or other modules
HOME=os.path.expanduser(u'~')
CFG_PATH=os.path.join(HOME, u'.quicknxs')
CFG_FILE=os.path.join(CFG_PATH, u'config.cfg')
if sys.version_info[0]>=3:
  USER=getuser()
  PACKAGE=os.path.abspath(os.path.dirname(__file__))
else:
  USER=unicode(getuser(), 'utf8')
  PACKAGE=unicode(os.path.abspath(os.path.dirname(__file__)), 'utf8')
if not os.path.exists(CFG_PATH):
  os.makedirs(CFG_PATH)

# for the search of files by number
BASE_SEARCH=u'*/data/REF_M_%s_'
OLD_BASE_SEARCH=u'*/*/%s/NeXus/REF_M_%s*'


class UnicodeConfigParser(SafeConfigParser):
  # make config use case sensitive strings
  optionxform=str
  def __init__(self, encoding='utf8', **opts):
    SafeConfigParser.__init__(self, **opts)
    self.encoding=encoding

  if sys.version_info[0]>=3:
    def get(self, section, option, raw=False, vars=None): #@ReservedAssignment
      value=SafeConfigParser.get(self, section, option, raw=raw, vars=vars)
      return value.replace(u'\\n', u'\n').replace(u'\\t', u'\t')

    def set(self, section, option, value=None):
      return SafeConfigParser.set(self, section, option,
                                  value.replace('\n', '\\n').replace('\t', '\\t'))
  else:
    def get(self, section, option, raw=False, vars=None): #@ReservedAssignment
      value=SafeConfigParser.get(self, section, option, raw=raw, vars=vars)
      if type(value) is str:
        value=unicode(value, self.encoding)
      return value.replace(u'\\n', u'\n').replace(u'\\t', u'\t')

    def set(self, section, option, value=None):
      if type(value) is unicode:
        value=value.encode(self.encoding)
      return SafeConfigParser.set(self, section, option,
                                  value.replace('\n', '\\n').replace('\t', '\\t'))


cfg=UnicodeConfigParser()
# first read defaults and than overwrite with user options
if '.zip/' in PACKAGE:
  from zipfile import ZipFile
  zname, subpath=PACKAGE.split('.zip/')
  zname+=u'.zip'
  subpath_cfg=os.path.join(subpath, u'default_config.cfg')
  z=ZipFile(zname)
  z.extract(subpath_cfg, u'/tmp')
  cfg.read(os.path.join(u'/tmp', subpath_cfg))
  z.close()
else:
  cfg.read(os.path.join(PACKAGE, u'default_config.cfg'))
if os.path.exists(CFG_FILE):
  cfg.read(CFG_FILE)

ADMIN_MAIL=cfg.get('misc', 'admin_email')
PATHS={}
for name in cfg.options('paths'):
  PATHS[name]=cfg.get('paths', name, vars=globals()).replace(u'/', os.path.sep)
EMAIL={}
for name in cfg.options('email'):
  EMAIL[name]=cfg.get('email', name, vars=globals())
  if EMAIL[name] in [u'True', u'False', u'None']:
    EMAIL[name]=eval(EMAIL[name])
EXPORT={}
for name in cfg.options('export'):
  EXPORT[name]=cfg.get('export', name, vars=globals())
  if EXPORT[name] in [u'True', u'False', u'None']:
    EXPORT[name]=eval(EXPORT[name])

def _replace_global(text):
  match=(None, '')
  for key, value in globals().items():
    # automatically replace patterns like HOME or PACKAGE
    if isinstance(value, basestring) and text.startswith(value) and len(value)>len(match[1]):
      match=(key, value)
  if match[0] is not None:
    text=text.replace(match[1], u"%%(%s)s"%match[0])
  return text


def _store_cfg():
  # store user configuration on exit
  for name, path in PATHS.items():
    path=_replace_global(path)
    # store path as unix like string for compatibility
    cfg.set('paths', name, path.replace(os.path.sep, u'/'))
  for name, option in EMAIL.items():
    option=_replace_global(unicode(option))
    cfg.set('email', name, option)
  for name, option in EXPORT.items():
    option=_replace_global(unicode(option))
    cfg.set('export', name, option)
  cfg.write(open(CFG_FILE, 'wb'))

atexit.register(_store_cfg)
