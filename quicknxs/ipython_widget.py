#coding: utf-8
'''
Updated for IPython 0.13
Created on 18-03-2012
Updated:   2012
author: Paweł Jarosz, Artur Glavic
'''

import atexit

from PyQt4 import QtCore, QtGui

DEFAULT_INSTANCE_ARGS=['qtconsole', '--pylab=inline', '--colors=linux']

import IPython
if IPython.__version__<'1.0':
    # does not work for ipython >= 1.0 as it is completely restructured
    from IPython.zmq.ipkernel import IPKernelApp #@UnresolvedImport
    from IPython.lib.kernel import find_connection_file #@UnresolvedImport
    from IPython.frontend.qt.kernelmanager import QtKernelManager #@UnresolvedImport
    from IPython.frontend.qt.console.rich_ipython_widget import RichIPythonWidget #@UnusedImport @UnresolvedImport
    from IPython.core.ipapi import get as get_ipython #@UnusedImport @UnresolvedImport
else:
    from IPython.qt.console.rich_ipython_widget import RichIPythonWidget #@UnresolvedImport @Reimport
    from IPython.qt.inprocess import QtInProcessKernelManager #@UnresolvedImport
    from IPython.lib import guisupport #@UnusedImport
    from IPython.core.getipython import get_ipython #@UnresolvedImport @Reimport

try:
  from traitlets.config.application import catch_config_error
except ImportError:
  from IPython.config.application import catch_config_error
from .gui_logging import ip_excepthook_overwrite

if IPython.__version__<'1.0':
    class IPythonLocalKernelApp(IPKernelApp):
        @catch_config_error
        def initialize(self, argv=DEFAULT_INSTANCE_ARGS):
            """
            :param argv: IPython args
    
            example:
    
                app = QtGui.QApplication([])
                kernelapp = IPythonLocalKernelApp.instance()
                kernelapp.initialize()
    
                widget = IPythonConsoleQtWidget()
                widget.set_default_style(colors='linux')
    
                widget.connect_kernel(connection_file=kernelapp.get_connection_file())
                # if you won't to connect to remote kernel you don't need kernelapp part, just widget part and:
    
                # widget.connect_kernel(connection_file='kernel-16098.json')
    
                # where kernel-16098.json is the kernel name
                widget.show()
    
                namespace = kernelapp.get_user_namespace()
                nxxx = 12
                namespace["widget"] = widget
                namespace["QtGui"]=QtGui
                namespace["nxxx"]=nxxx
    
                app.exec_()
            """
            super(IPythonLocalKernelApp, self).initialize(argv)
            self.kernel.eventloop=self.loop_qt4_nonblocking
            self.kernel.start()
            self.start()

        def loop_qt4_nonblocking(self, kernel):
            """Non-blocking version of the ipython qt4 kernel loop"""
            kernel.timer=QtCore.QTimer()
            kernel.timer.timeout.connect(kernel.do_one_iteration)
            kernel.timer.start(1000*kernel._poll_interval)

        def get_connection_file(self):
            """Returne current kernel connection file."""
            return self.connection_file

        def get_user_namespace(self):
            """Returns current kernel userspace dict"""
            return self.kernel.shell.user_ns

class IPythonConsoleQtWidget(RichIPythonWidget):

    def __new__(cls, parent):
      return RichIPythonWidget.__new__(cls)

    def __init__(self, parent):
      from logging import getLogger, CRITICAL
      logger=getLogger()
      silenced=None
      for handler in logger.handlers:
        if handler.__class__.__name__=='QtHandler':
          silenced=handler
          old_level=silenced.level
          silenced.setLevel(CRITICAL+1)
          break
      RichIPythonWidget.__init__(self)
      self._parent=parent
      self.buffer_size=10000 # increase buffer size to show longer outputs
      self.set_default_style(colors='linux')
      if IPython.__version__<'1.0':
        kernelapp=IPythonLocalKernelApp.instance()
        kernelapp.initialize()
        self.connect_kernel(connection_file=kernelapp.get_connection_file())
      else:
        kernel_manager=QtInProcessKernelManager(config=self.config, gui='qt4')
        kernel_manager.start_kernel()
        self.kernel_manager=kernel_manager
        self.kernel_client=kernel_manager.client()
        self.kernel_client.start_channels()
      ip=get_ipython()
      # console process exceptions (IPython controlled)
      ip.set_custom_exc((Exception,), ip_excepthook_overwrite)
      self.namespace=ip.user_ns
      self.namespace['IP']=self
      self.namespace['app']=QtGui.QApplication.instance()
      self.namespace['gui']=parent
      self.namespace['plot']=self._plot
      if silenced:
        silenced.setLevel(old_level)

    def connect_kernel(self, connection_file, heartbeat=False):
        """
        :param connection_file: str - is the connection file name, for example 'kernel-16098.json'
        :param heartbeat: bool - workaround, needed for right click/save as ... errors ... i don't know how to 
                          fix this issue. Anyone knows? Anyway it needs more testing
                          
        example1 (standalone):
                app = QtGui.QApplication([])
                widget = IPythonConsoleQtWidget()
                widget.set_default_style(colors='linux')


                widget.connect_kernel(connection_file='some connection file name')

                app.exec_()

        example2 (IPythonLocalKernelApp):
                app = QtGui.QApplication([])

                kernelapp = IPythonLocalKernelApp.instance()
                kernelapp.initialize()

                widget = IPythonConsoleQtWidget()

                # Green text, black background ;)
                widget.set_default_style(colors='linux')

                widget.connect_kernel(connection_file='kernelapp.get_connection_file())

                app.exec_()
        """
        km=QtKernelManager(connection_file=find_connection_file(connection_file), config=self.config)
        km.load_connection_file()
        km.start_channels(hb=heartbeat)
        self.kernel_manager=km
        atexit.register(self.kernel_manager.cleanup_connection_file)

    def _plot(self, *args, **opts):
      self._parent.ui.refl.clear()
      self._parent.ui.refl.plot(*args, **opts)
      self._parent.ui.refl.draw()



