# -*- encoding: utf-8 -*-
'''
  Script used for setup and installation purpose. 
  
  The script can create exe stand alone programs under windows, but py2app doesn't word until now.
'''

import sys, os
import matplotlib
try:
  # Use easy setup to ensure dependencies
  import ez_setup
  ez_setup.use_setuptools()
except ImportError:
  pass

from quick_nxs.version import str_version

__package_name__='QuickNXS'
__author__="Artur Glavic"
__copyright__="Copyright 2012-2013"
__license__="GPL v3"
__version__=str_version
__email__="glavicag@ornl.gov"
__author_email__=__email__
__url__="http://"
__description__='''Magnetism reflectometer data reduction software'''

__scripts__=['quicknxs']
__py_modules__=[]
__package_dir__={}
__packages__=['quick_nxs']
__package_data__={
                  'quick_nxs': ['genx_templates/*.gx'],
                  }
__data_files__=[]

if "py2exe" in sys.argv:
  import py2exe #@UnusedImport @UnresolvedImport
  __data_files__+=matplotlib.get_py2exe_datafiles()
  __options__={
                #"setup_requires": ['py2exe'],
                #"console": [ "__init__.py"], # set the executable for py2exe
                "windows": [ {
                            "script": "quicknxs",
                            "icon_resources": [(1, "icons/logo.png")]
                            }, ], # executable for py2exe is windows application
                "options": {  "py2exe": {
                              "includes": "numpy",
                              "optimize": 2, # Keep docstring (e.g. Shell usage)
                              "skip_archive": False, # setting not to move compiled code into library.zip file
                              'packages': 'PyQt4, sip, matplotlib, scipy',
                              "dll_excludes": ["MSVCP90.dll"],
                              'excludes': [ 'pdb', 'doctest', 'tcl', 'tk', 'Tkinter'],
                             },
                           }
              }
else:
  __options__={#"setup_requires":[],
                }

__requires__=['numpy', 'PyQt4']
from distutils.core import setup

# extensions modules written in C
__extensions_modules__=[]

if 'install' not in sys.argv:
  # Remove MANIFEST before distributing to be sure no file is missed
  if os.path.exists('MANIFEST'):
    os.remove('MANIFEST')

#### Run the setup command with the selected parameters ####
setup(name=__package_name__,
      version=__version__,
      description=__description__,
      author=__author__,
      author_email=__email__,
      url=__url__,
      scripts=__scripts__,
      py_modules=__py_modules__,
      ext_modules=__extensions_modules__,
      packages=__packages__,
      package_dir=__package_dir__,
      package_data=__package_data__,
      data_files=__data_files__,
      requires=__requires__, #does not do anything
      **__options__
     )
