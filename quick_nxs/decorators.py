'''
  Module for usefull decorators e.g. for logging function calls, input and output.
'''

import inspect
import logging


#
# Help functions adopted from Michele Simionato's decorator module 
# http://www.phyast.pitt.edu/~micheles/python/decorator.zip
#

def getinfo(func):
    """
      Returns an info dictionary containing:
      - name (the name of the function : str)
      - argnames (the names of the arguments : list)
      - defaults (the values of the default arguments : tuple)
      - signature (the signature : str)
      - doc (the docstring : str)
      - module (the module name : str)
      - dict (the function __dict__ : str)
    """
    assert inspect.ismethod(func) or inspect.isfunction(func)
    regargs, varargs, varkwargs, defaults=inspect.getargspec(func)
    argnames=list(regargs)
    if varargs:
        argnames.append(varargs)
    if varkwargs:
        argnames.append(varkwargs)
    signature=inspect.formatargspec(regargs, varargs, varkwargs, defaults,
                                      formatvalue=lambda value: "")[1:-1]
    output=dict(name=func.__name__, argnames=argnames, signature=signature,
                defaults=func.func_defaults, doc=func.__doc__,
                module=func.__module__, dict=func.__dict__,
                globals=func.func_globals, closure=func.func_closure)
    return output

def update_wrapper(wrapper, wrapped, create=False):
    """
      An improvement over functools.update_wrapper. By default it works the
      same, but if the 'create' flag is set, generates a copy of the wrapper
      with the right signature and update the copy, not the original.
      Moreovoer, 'wrapped' can be a dictionary with keys 'name', 'doc', 'module',
      'dict', 'defaults'.
    """
    if isinstance(wrapped, dict):
        infodict=wrapped
    else: # assume wrapped is a function
        infodict=getinfo(wrapped)
    assert not '_wrapper_' in infodict["argnames"], \
           '"_wrapper_" is a reserved argument name!'
    if create: # create a brand new wrapper with the right signature
        src="lambda %(signature)s: _wrapper_(%(signature)s)"%infodict
        # import sys; print >> sys.stderr, src # for debugging purposes
        wrapper=eval(src, dict(_wrapper_=wrapper))        
    try:
        wrapper.__name__=infodict['name']
    except: # Python version < 2.4
        pass
    wrapper.__doc__=infodict['doc']
    wrapper.__module__=infodict['module']
    wrapper.__dict__.update(infodict['dict'])
    wrapper.func_defaults=infodict['defaults']
    return wrapper


# the real meat is here
def _decorator(caller, func):
    infodict=getinfo(func)
    argnames=infodict['argnames']
    assert not ('_call_' in argnames or '_func_' in argnames), \
           'You cannot use _call_ or _func_ as argument names!'
    src="lambda %(signature)s: _call_(_func_, %(signature)s)"%infodict
    dec_func=eval(src, dict(_func_=func, _call_=caller))
    return update_wrapper(dec_func, func)

def decorator(caller):
    """
    General purpose decorator factory: takes a caller function as
    input and returns a decorator with the same attributes.
    """
    return update_wrapper(lambda f : _decorator(caller, f), caller)


########################### Decorators for logging ##################################

def _nicetype(item):
  if 'array' in type(item).__name__:
    return type(item).__name__+("[%s]"%str(item.shape))
  elif type(item) in [list, tuple]:
    return type(item).__name__+('[%i]'%len(item))
  else:
    return type(item).__name__

class DecoratorLogger(logging.getLoggerClass()):
  '''
    A logger that makes sure the actual function definition filename, lineno and function name
    is used for logging.
  '''
  
  def makeRecord(self, name, lvl, fn, lno, msg, args, exc_info, func=None, extra=None):
    if extra is None:
      return super(DecoratorLogger, self).makeRecord(name, lvl, fn, lno, msg, args, exc_info,
                                                     func=func, extra=None)
    else:
      
      return super(DecoratorLogger, self).makeRecord(name, lvl, extra['name'], extra['lno'],
                                                     msg, args,
                                                     exc_info, func=extra['func'], extra=None)      

old_class=logging.getLoggerClass()
logging.setLoggerClass(DecoratorLogger)
logger=logging.getLogger('deco')
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.NullHandler())
logging.setLoggerClass(old_class)

def _logformat(msg, decname, func):
  if hasattr(func, 'im_func'):
    co=func.im_func.func_code
  else:
    co=func.func_code
  fname=co.co_filename
  lno=co.co_firstlineno
  logger.debug(msg, extra={'func': '@'+decname, 'name': fname, 'lno': lno})

@decorator
def log_call(func, *args, **kw):
  '''
    Decorator to log just the method call.
  '''
  infodict=getinfo(func)
  if len(infodict['argnames'])>0 and infodict['argnames'][0]=='self':
    _logformat('%s.%s.%s'%(infodict['module'],
                                   args[0].__class__.__name__, infodict['name']),
               'log_call', func)
  else:
    _logformat('%s.%s'%(infodict['module'], infodict['name']), 'log_call', func)
  return func(*args, **kw)

@decorator
def log_input(func, *args, **kw):
  '''
    Decorator to log a method call with input.
  '''
  infodict=getinfo(func)
  if hasattr(func, 'im_func'):
    logstr=' call %s.%s('%(args[0].__class__.__name__, infodict['name'])
    method=True
    info_len=len('%s.%s('%(args[0].__class__.__name__, infodict['name']))
  else:
    logstr='call %s('%(infodict['name'])
    method=False
    info_len=len('%s('%(infodict['name']))
  
  namelen=max([len(name)+3 for name in infodict['argnames']]+[len(name) for name in kw.keys()])
  for i, arg in enumerate(args):
    if i==0 and (method or infodict['name']=='__init__'):
      continue
    value=repr(arg)
    value_split=value.splitlines()
    if len(value_split)>5:
      value="\n".join(value_split[:2]+[' '*(len(value_split[1])/2)+'...']+value_split[-2:])
    value.replace('\n', '\n'+' '*(namelen+7))
    logstr+='\n'+('%% %is= %%s (%%s)'%(namelen+3))%(infodict['argnames'][i], value, _nicetype(arg))
  
  for key, arg in sorted(kw.items()):
    value=repr(arg)
    value_split=value.splitlines()
    if len(value_split)>5:
      value="\n".join(value_split[:2]+[' '*(len(value_split[1])/2)+'...']+value_split[-2:])
    value.replace('\n', '\n'+' '*(namelen+4))
    logstr+='\n'+('KW %% %ss= %%s (%%s)'%namelen)%(key, repr(value), _nicetype(arg))
  logstr+='\n)'
  logstr=logstr.replace('\n', '\n'+' '*(info_len+10))
  logstr=logstr.replace('call ', 'call \n'+' '*10)
  
  _logformat(logstr, 'log_input', func)
  return func(*args, **kw)

@decorator
def log_output(func, *args, **kw):
  '''
    Decorator to log a method call with output. If combined with log_input
    the input is logged at the time before the call and the output after.
  '''
  output=func(*args, **kw)
  infodict=getinfo(func)
  if len(infodict['argnames'])>0 and infodict['argnames'][0]=='self':
    logstr='return from %s.%s'%(args[0].__class__.__name__, infodict['name'])
  else:
    logstr='return from %s'%(infodict['name'])
  value=repr(output)
  value_split=value.splitlines()
  if len(value_split)>5:
    value="\n".join(value_split[:2]+[' '*(len(value_split[1])/2)+'...']+value_split[-2:])
  logstr+='\n-> %15s (%s)'%(value, _nicetype(output))
  logstr=logstr.replace('\n', '\n'+' '*44)
  _logformat(logstr, 'log_output', func)
  return output

@decorator
def log_both(func, *args, **kw):
  '''
    Decoratore to log a method call with input and output.
  '''
  infodict=getinfo(func)
  if hasattr(func, 'im_func'):
    logstr=' call %s.%s('%(args[0].__class__.__name__, infodict['name'])
    method=True
    info_len=len('%s.%s('%(args[0].__class__.__name__, infodict['name']))
  else:
    logstr='call %s('%(infodict['name'])
    method=False
    info_len=len('%s('%(infodict['name']))
  
  namelen=max([len(name)+3 for name in infodict['argnames']]+[len(name) for name in kw.keys()])
  for i, arg in enumerate(args):
    if i==0 and (method or infodict['name']=='__init__'):
      continue
    value=repr(arg)
    value_split=value.splitlines()
    if len(value_split)>5:
      value="\n".join(value_split[:2]+[' '*(len(value_split[1])/2)+'...']+value_split[-2:])
    value.replace('\n', '\n'+' '*(namelen+7))
    logstr+='\n'+('%% %is= %%s (%%s)'%(namelen+3))%(infodict['argnames'][i], value, _nicetype(arg))
  
  for key, arg in sorted(kw.items()):
    value=repr(arg)
    value_split=value.splitlines()
    if len(value_split)>5:
      value="\n".join(value_split[:2]+[' '*(len(value_split[1])/2)+'...']+value_split[-2:])
    value.replace('\n', '\n'+' '*(namelen+4))
    logstr+='\n'+('KW %% %ss= %%s (%%s)'%namelen)%(key, repr(value), _nicetype(arg))
  logstr+='\n)'
  logstr=logstr.replace('\n', '\n'+' '*(info_len+10))
  logstr=logstr.replace('call ', 'call \n'+' '*10)
  
  _logformat(logstr, 'log_input', func)
  # call the function
  output=func(*args, **kw)
  if len(infodict['argnames'])>0 and infodict['argnames'][0]=='self':
    logstr='return from %s.%s'%(args[0].__class__.__name__, infodict['name'])
  else:
    logstr='return from %s'%(infodict['name'])
  value=repr(output)
  value_split=value.splitlines()
  if len(value_split)>5:
    value="\n".join(value_split[:2]+[' '*(len(value_split[1])/2)+'...']+value_split[-2:])
  logstr+='\n-> %s (%s)'%(value, _nicetype(output))
  logstr=logstr.replace('\n', '\n'+' '*(info_len+10))
  _logformat(logstr, 'log_output', func)
  return output

########################## General decorators ###############################

class check_input(object):
  '''
    Decorator checking the input to a function.
  '''
  try_convert=True
  types=[]
  
  def __init__(self, types, try_convert=True):
    self.types=types
    self.try_convert=try_convert
  
  def __call__(self, func):
    infodict=getinfo(func)
    argnames=infodict['argnames']
    assert not ('_call_' in argnames or '_func_' in argnames), \
           'You cannot use _call_ or _func_ as argument names!'
    src="def dec_func(%(signature)s):"%infodict
    for i, typei in enumerate(self.types):
      src+='\n  if type(%s).__name__!="%s":'%(argnames[i], typei.__name__)
      if self.try_convert:
        src+='\n    try:'
        src+='\n      %s=%s(%s)'%(argnames[i], typei.__name__, argnames[i])
        src+='\n    except:'
        src+='\n      raise ValueError, "type of %s is not %s"'%(argnames[i], typei.__name__)
      else:
        src+='\n    raise ValueError, "type of %s is not %s"'%(argnames[i], typei.__name__)
    src+='\n  return _func_(%(signature)s)'%infodict
    exec_dict=dict(_func_=func, _call_=self.__call__)
    exec(src, exec_dict)
    return update_wrapper(exec_dict['dec_func'], func)
