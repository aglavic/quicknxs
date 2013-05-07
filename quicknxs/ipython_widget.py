#coding: utf-8
'''
Updated for IPython 0.13
Created on 18-03-2012
Updated:   2012
author: Paweł Jarosz, Artur Glavic
'''

import atexit

from PyQt4 import QtCore, QtGui

from IPython.zmq.ipkernel import IPKernelApp
from IPython.lib.kernel import find_connection_file
from IPython.frontend.qt.kernelmanager import QtKernelManager
from IPython.frontend.qt.console.rich_ipython_widget import RichIPythonWidget
from IPython.config.application import catch_config_error

DEFAULT_INSTANCE_ARGS=['qtconsole', '--pylab=inline', '--colors=linux']

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
      kernelapp=IPythonLocalKernelApp.instance()
      kernelapp.initialize()
      self.set_default_style(colors='linux')
      self.connect_kernel(connection_file=kernelapp.get_connection_file())
      self.namespace=kernelapp.get_user_namespace()
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