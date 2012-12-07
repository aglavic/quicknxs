#-*- coding: utf-8 -*-
'''
  Installation script for the QuickNXS program.
  Also used to create stand alone executables.
'''

from cx_Freeze.dist import setup
from cx_Freeze.freezer import Executable

import sys
import matplotlib
#from glob import glob
matplotlib.use('Qt4Agg')

version='0.1'
packages=['quick_nxs']
scripts=['quicknxs.py']

build_exe_options={"packages": packages,
                   "excludes": [
                                "Tkinter", "tcl", "tcltk", "IPython", 'tk',
#                                "matplotlib.backends.backend_wx",
#                                "matplotlib.backends.backend_wxagg",
#                                "matplotlib.backends.backend_qt",
#                                "matplotlib.backends.backend_qtagg",
#                                "matplotlib.backends.backend_tkagg",
#                                "matplotlib.backends.backend_gtk",
#                                "matplotlib.backends.backend_gtkagg",
#                                "matplotlib.backends.backend_gtkcairo",
#                                "matplotlib.backends.backend_gdk",
#                                "matplotlib.backends.backend_fltkagg",
                                ],
                   "includes": [
                                "sip", "PyQt4.QtCore", "PyQt4.QtGui",
#                                "numpy", "scipy",
#                                "matplotlib", "subprocess", "multiprocessing",
#                                "urllib", "hashlib", "xmlrpclib",
#                                "matplotlib.backends.backend_qt4agg",
#                                "matplotlib.backends.backend_qt4"
                                ],
                   "include_files":[(matplotlib.get_data_path(), "mpl-data"),
                                    ]}

# GUI applications require a different base on Windows (the default is for a
# console application).
base=None
if sys.platform=="win32":
    base="Win32GUI"

setup(name="QuickNXS",
      author='Artur Glavic',
      author_email='glavicag@ornl.gov',
      url='quicknxs.sourceforge.net',
      version=version,
      packages=packages,
      scripts=scripts,
      description="Data reduction software of the SNS magnetism reflectometer",
      options={"build_exe": build_exe_options},
      executables=[Executable(scripts[0], base=base)])

