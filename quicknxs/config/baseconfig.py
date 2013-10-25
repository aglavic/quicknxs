# -*- coding: utf-8 -*-
'''
  Basis of the configuration system. The :class:`ConfigProxy` object
  combines module parameters with temporary and user changeable
  configuration file options. When used in other modules
  this facility is completely hidden to the API.
  
  As each parameter can be accessed as an attribute of the ConfigHolder object
  it behaves exactly like the according module would to, thus
  IDEs with context sensitive syntax completion work with it as well.
  
  The initialization of all config modules is done in the config __init__ module.
'''

import os
import atexit
import re
import sys
from .configobj import ConfigObj, ConfigObjError
from ..decorators import log_call, log_input


class ConfigProxy(object):
  '''
  Handling of configuration options with temporal and fixed storage to .ini files
  in the used folder.
  Each configuration has it's own ConfigHolder object for access but one .ini file
  can hold several configurations.
  '''
  _KEYCRE=re.compile(r"%\(([^)]*)\)s") # search pattern for interpolation
  _PARSE_ERRORS=None

  default_storage='general'
  config_path=''
  configs={}
  storages={}
  aliases={}

  def __init__(self, config_path):
    self._PARSE_ERRORS=[]
    self.configs={}
    self.aliases={}
    self.storages={}
    self.tmp_storages={}
    self.config_path=config_path
    # store .ini files on interpreter exit
    atexit.register(self.store)

  @log_input
  def add_config(self, name, items, storage=''):
    '''
    Crate a new dictionary connected to a storage config file.
    
    :returns: The corresponding :class:`ConfigHolder` object.
    '''
    if storage=='':
      storage=self.default_storage
    if storage is None:
      storage='_temp'
      if not '_temp' in self.storages:
        self.tmp_storages[storage]={}
        # use the exact same dictionary object
        self.storages[storage]=self.tmp_storages[storage]
    elif not storage in self.storages:
      sfile=os.path.join(self.config_path, storage+'.ini')
      try:
        self.storages[storage]=ConfigObj(
                                        infile=sfile,
                                        unrepr=True,
                                        encoding='utf8',
                                        indent_type='    ',
                                        interpolation=False,
                                        )
      except ConfigObjError:
        self._PARSE_ERRORS.append(
            ("Could not parse configfile %s, using temporary config.\nFix or delete the file!"%sfile,
              sys.exc_info()))
        self.storages[storage]={}
      self.tmp_storages[storage]={}
    self.configs[name]=storage
    if name in self.storages[storage]:
      # update additional options from config
      for key, value in items.items():
        if not key in self.storages[storage][name]:
          self.storages[storage][name][key]=value
    else:
      self.storages[storage][name]=dict(items)
    self.tmp_storages[storage][name]={}
    return self[name]

  @log_input
  def add_alias(self, config, alias):
    '''
    Crate an alias for another configuration item.
    
    :returns: The corresponding :class:`ConfigHolder` object.
    '''
    if not config in self.configs:
      raise KeyError, 'no configuration named %s found'%config
    self.aliases[alias]=config
    return self[config]

  @log_call
  def store(self):
    """store configuration data into .ini files."""
    for item in self.storages.values():
      if not hasattr(item, 'write'):
        continue
      # remove constants for storage
      restore={}
      for cname, config in item.items():
        restore[cname]={}
        for key in config.keys():
          if key==key.upper():
            restore[cname][key]=config[key]
            del(config[key])
      # only write to ConfigObj items
      item.write()
      # restore constants
      for cname, cdict in restore.items():
        for key, value in cdict.items():
          item[cname][key]=value

  def __getitem__(self, name):
    if isinstance(name, basestring):
      if name in self.configs or name in self.aliases:
        return ConfigHolder(self, name)
      raise KeyError, "%s is no known configuration"%name
    else:
      raise KeyError, "Only strings are allowed as keys"

  def get_config_item(self, config, item):
    """Called by :class:`ConfigHolder` to retreive an item"""
    if config in self.aliases:
      config=self.aliases[config]
    if not config in self.configs:
      raise KeyError, "%s is no known configuration"%config
    storage=self.configs[config]
    if item in self.tmp_storages[storage][config]:
      # if value has been stored temporarily, return it
      value=self.tmp_storages[storage][config][item]
    else:
      value=self.storages[storage][config][item]
    if isinstance(value, basestring) and '%' in value and \
          not self.storages[storage][config].get('NO_INTERPOLATION', False):
      # perform interpolation with constants if possible
      value=self.interpolate(config, value)
    return value

  def interpolate(self, config, value, recdepth=0):
    '''
    Interpolate value with available options starting in the same configuration.
    '''
    vtype=type(value)
    storage=self.configs[config]
    if recdepth>5:
      # limit maximum number of recursive insertions
      return value
    match=self._KEYCRE.search(value)
    match_start=0
    while match:
      match_str=match.group()
      match_key=match.groups()[0]
      match_end=match.span()[1]
      match=self._KEYCRE.search(value[match_start+match_end:])
      if not '.' in match_key:
        # search same config for value
        if match_key in self.tmp_storages[storage][config]:
          value=value.replace(match_str, vtype(self.tmp_storages[storage][config][match_key]))
        if match_key in self.storages[storage][config]:
          value=value.replace(match_str, vtype(self.storages[storage][config][match_key]))
      else:
        # search other config for values
        configi, match_key=match_key.split('.', 1)
        if not (configi in self.configs or configi in self.aliases):
          continue
        if configi in self.aliases:
          configi=self.aliases[configi]
        storagei=self.configs[configi]
        if match_key in self.tmp_storages[storagei][configi]:
          value=value.replace(match_str, vtype(self.tmp_storages[storagei][configi][match_key]))
        if match_key in self.storages[storagei][configi]:
          value=value.replace(match_str, vtype(self.storages[storagei][configi][match_key]))
    if '%' in value:
      return self.interpolate(config, value, recdepth+1)
    return value

  def set_config_item(self, config, item, value, temporary=False):
    """Called by :class:`ConfigHolder` to set an item value"""
    if config in self.aliases:
      config=self.aliases[config]
    if not config in self.configs:
      raise KeyError, "%s is no known configuration"%config
    storage=self.configs[config]
    if temporary:
      # store value in temporary dictionary
      self.tmp_storages[storage][config][item]=value
    else:
      self.storages[storage][config][item]=value

  def get_config_keys(self, config):
    """Called by :class:`ConfigHolder` to get the keys for it's config"""
    if config in self.aliases:
      config=self.aliases[config]
    if not config in self.configs:
      raise KeyError, "%s is no known configuration"%config
    storage=self.configs[config]
    return self.storages[storage][config].keys()

  def keys(self):
    """Return the available configurations"""
    keys=self.configs.keys()+self.aliases.keys()
    keys.sort()
    return keys

  def values(self):
    return [self[key] for key in self.keys()]

  def items(self):
    return [(key, self[key]) for key in self.keys()]

  def __len__(self):
    return len(self.keys())

  def __repr__(self):
    output=self.__class__.__name__
    output+='(storages=%i, configs=%i)'%(len(self.storages), len(self))
    return output



class ConfigHolder(object):
  '''
  Dictionary like object connected to the a :class:`ConfigProxy` reading
  and writing values directly to that object.
  Each key can also be accessed as attribute of the object.
  
  To store items temporarily, the object supports a "temp"
  attribute, which itself is a ConfigHolder object. 
  '''

  def __init__(self, proxy, name, storetmp=False):
    self._proxy=proxy
    self._name=name
    self._storetmp=storetmp

  def _get_tmporary(self):
    return ConfigHolder(self._proxy, self._name, storetmp=True)

  temp=property(_get_tmporary,
          doc="A representation of this :class:`ConfigHolder` which stores items only for this session.")

  def __getattribute__(self, name):
    """
      Basis of the parameter access (e.g. can use
      object.key to access object[key]). If a 
    """
    if name.startswith('_') or name in dir(ConfigHolder):
      return object.__getattribute__(self, name)
    else:
      return self.__getitem__(name)

  def __setattr__(self, name, value):
    if name.startswith('_') or name in dir(ConfigHolder):
      object.__setattr__(self, name, value)
    else:
      return self.__setitem__(name, value)

  def __getitem__(self, name):
    return self._proxy.get_config_item(self._name, name)

  def __setitem__(self, name, value):
    if name==name.upper():
      raise ValueError, "%s is a constant and thus cannot be altered"%name
    self._proxy.set_config_item(self._name, name, value,
                                temporary=self._storetmp)

  def __contains__(self, other):
    return other in self.keys()

  def keys(self):
    return self._proxy.get_config_keys(self._name)

  def values(self):
    return [self[key] for key in self.keys()]

  def items(self):
    return [(str(key), self[key]) for key in self.keys()]

  def __repr__(self):
    output=self.__class__.__name__+'('
    spacer='\n'+' '*len(output)
    output+=repr(dict(self.items())).replace('\n', spacer)
    output+=')'
    return output

  def __dir__(self):
    return self.__dict__.keys()+self.keys()
