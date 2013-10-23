# -*- encoding: utf-8 -*-
'''
  Script used for setup and installation purpose. 
  
  The script can create exe stand alone programs under windows, but py2app doesn't word until now.
'''

import sys, os
from glob import glob
import matplotlib
try:
  # Use easy setup to ensure dependencies
  import ez_setup
  ez_setup.use_setuptools()
except ImportError:
  pass


__package_name__='QuickNXS'
__author__="Artur Glavic"
__copyright__="Copyright 2012-2013"
__license__="GPL v3"
__email__="glavicag@ornl.gov"
__author_email__=__email__
__url__="http://"
__description__='''Magnetism reflectometer data reduction software'''

__scripts__=['scripts/quicknxs']
__py_modules__=[]
__package_dir__={}
__packages__=['quicknxs', 'quicknxs.config']
__package_data__={'quicknxs': ['default_config.cfg', 'htmldoc/*', 'genx_templates/*.gx']}

__data_files__=[('/usr/share/applications', ['dist_data/sns-quicknxs.desktop']),
                ('/usr/share/icons/gnome/128x128/apps/', ['dist_data/quicknxs.png'])]

if "py2exe" in sys.argv:
  import py2exe #@UnusedImport @UnresolvedImport
  import zmq
  os.environ["PATH"]+=os.path.pathsep+os.path.split(zmq.__file__)[0]
  __data_files__=matplotlib.get_py2exe_datafiles()
  sys.path.append("..\\App")
  __data_files__+=[('Microsoft.VC90.CRT', glob('..\\App\\msvc*.dll')+['..\\App\\Microsoft.VC90.CRT.manifest'])]
  __data_files__+=[(r'quicknxs', [r'quicknxs\default_config.cfg']),
                   (r'quicknxs\genx_templates', glob(r'quicknxs\genx_templates\*.gx')),
                   (r'quicknxs\htmldoc', glob(r'quicknxs\htmldoc\*')),
                   ("IPython\\config\\profile", glob('..\\App\\Lib\\site-packages\\IPython\\config\\profile\\*.*')+
                                                glob('..\\App\\Lib\\site-packages\\IPython\\config\\profile\\README*')),
                   ("IPython\\config\\profile\\cluster", glob('..\\App\\Lib\\site-packages\\IPython\\config\\profile\\cluster\\*')),
                   ]
  pexe=os.path.abspath(os.path.join('..\\App'))
  sys.path.append(pexe)
  __options__={
                "windows": [ {
                            "script": "scripts/quicknxs",
                            "icon_resources": [(1, "icons/logo.ico")],
                            }, ], # executable for py2exe is windows application
                "options": {  "py2exe": {
                              "includes": ["sip", "numpy", "scipy.stats.mstats",
#                                           "zmq.utils", "zmq.utils.jsonapi", "zmq.utils.strtypes",
                                           ],
                              "optimize": 1, # Keep docstring (e.g. Shell usage)
                              "skip_archive": True, # setting not to move compiled code into library.zip file
                              'packages': ['PyQt4', 'h5py', 'zmq', 'pygments', 'IPython'],
                              "dll_excludes": [],
                              'excludes': [ 'doctest', 'tcl', 'tk', 'Tkinter',
                                           '_gtkagg', '_tkagg', '_wxagg',
                                           '_gtk', '_gtkcairo', '_agg2', '_cairo',
                                           '_cocoaagg', '_fltkagg',
                                           ],
                             },
                           }
              }
elif 'py2app' in sys.argv:
  import py2app #@UnusedImport @UnresolvedImport
  __data_files__=[]
  __options__={
               'app': ["scripts/quicknxs"],
               'options': {'py2app': {
                          'optimize': 1,
                          'compressed': False,
                          'argv_emulation': False,
                          'iconfile': 'dist_data/quicknxs.icns',
                          'includes': ['sip', 'PyQt4._qt', 'PyQt4.QtWebKit', 'PyQt4.QtNetwork'],
                          'packages': ['h5py', 'zmq', 'pygments', 'IPython'],
                          'excludes': [ 'doctest', 'tcl', 'tk', 'Tkinter',
                                       '_gtkagg', '_tkagg', '_wxagg',
                                       '_gtk', '_gtkcairo', '_agg2', '_cairo',
                                       '_cocoaagg', '_fltkagg',
                                       ],
                         }}
               }
else:
  __options__={}

__requires__=['numpy', 'matplotlib']
from distutils.core import setup

# extensions modules written in C
__extensions_modules__=[]

if 'install' not in sys.argv:
  # Remove MANIFEST before distributing to be sure no file is missed
  if os.path.exists('MANIFEST'):
    os.remove('MANIFEST')

# make sure revision is correct before building
from subprocess import call
if not 'py2exe' in sys.argv:
  call(['/usr/bin/env', 'python', 'dist_data/update_version.py'])
if ('sdist' in sys.argv or 'py2exe' in sys.argv or 'py2app' in sys.argv) and \
    not '--nocheck' in sys.argv:
  print "Running unit test before compiling build distribution."
  from test_all import test_suites
  import unittest
  runner=unittest.TextTestRunner(sys.stderr, 'Pre-Build unit test run', 2)
  suite=unittest.TestSuite(test_suites.values())
  result=runner.run(suite)
  if len(result.errors+result.failures):
    print "Not all tests were successfull, stop building distribution!"
    exit()
if '--nocheck' in sys.argv:
  sys.argv.remove('--nocheck')

from quicknxs.version import str_version
__version__=str_version

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

if 'py2app' in sys.argv:
  # add qt.conf which fixes issues with the app and a currently installed qt4 library
  open('dist/QuickNXS.app/Contents/Resources/qt.conf', 'w').write(open('dist_data/qt.conf', 'r').read())
  
