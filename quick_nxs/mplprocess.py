#-*- coding: utf-8 -*-
'''
Matplotlib plot canvas with separate plotting in background process.

The background plotting canvas uses a three object model:
  - A separate thread carries out the plotting work and sends the raw image over a pipe.
  - A QThread runs in the background communicating with the process over a pipe and
    with the GUI via signals.
  - A widget contains the plotting relevant function and sends it to the thread,
    this widget has to implement all functionalities normally provided by the Qt4Add
    backend of matplotlib.
'''
from functools import partial
#from time import time, sleep
from PyQt4 import QtCore, QtGui

from multiprocessing import Process, Pipe
from matplotlib.cbook import CallbackRegistry
from matplotlib.backend_bases import FigureCanvasBase, MouseEvent, KeyEvent
from matplotlib.axes import Axes
from matplotlib.backends.backend_agg import FigureCanvasAgg, Figure
from matplotlib.backends.backend_qt4 import NavigationToolbar2QT
from matplotlib.lines import Line2D
from matplotlib.image import AxesImage
from matplotlib.collections import QuadMesh

# objects used to represent objects present in the other process
class ConnectedObject(object):
  def __init__(self, item, index):
    self._index=index
    self._parent=None

  def __getattr__(self, name):
    known_names=self._type.__dict__.keys()
    for base in self._type.__bases__:
      known_names+=base.__dict__.keys()
    if not name.startswith("_") and not name in self.__dict__ and \
           (name in known_names):
      return partial(self._caller, name)
    return getattr(object, name)

  def _caller(self, name, *args, **opts):
    if self._parent is None:
      raise RuntimeError, "parent thread not connected"
    self._parent.scheduled_actions.append(('_object_call', (self._index, name, args, opts), {}))

  def _recall(self, name, result):
    # subclasses can overwrite to act on special method results
    pass

class ConnectedLine2D(ConnectedObject):
  _type=Line2D

class ConnectedImage(ConnectedObject):
  _type=AxesImage

class ConnectedQuadMesh(ConnectedObject):
  _type=QuadMesh

def get_connected_object(item, index):
  known_classes=[subcls._type for subcls in ConnectedObject.__subclasses__()]
  if not item.__class__ in known_classes:
#    raise ValueError, 'no connection class defined for object of type %s'%item.__class__
    return None
  idx=known_classes.index(item.__class__)
  return ConnectedObject.__subclasses__()[idx](item, index)

class FixedConnectedObject(object):
  def __init__(self, parent, attr):
    self._attr=attr
    self._parent=parent
    self._caller('_init_me', self.__class__)

  def __getattr__(self, name):
    if not name.startswith("_") and not name in self.__dict__ and \
           (name in self._type.__dict__):
      return partial(self._caller, name)
    return getattr(object, name)

  def _caller(self, name, *args, **opts):
    if self._parent is None:
      raise RuntimeError, "parent thread not connected"
    self._parent.scheduled_actions.append(('_fixed_object_call', (self._attr, name, args, opts), {}))

  def _recall(self, name, result):
    # subclasses can overwrite to act on special method results
    if name=='_init_me':
      self.__dict__.update(result)

  @classmethod
  def _do_init(cls, obj):
    return {}

class ConnectedFigure(FixedConnectedObject):
  _type=Figure
  pass

class ConnectedAxes(FixedConnectedObject):
  _type=Axes

  @classmethod
  def _do_init(cls, obj):
    xlim=obj.get_xlim()
    ylim=obj.get_ylim()
    return dict(xlim=xlim, ylim=ylim)

  def set_xlim(self, *lim):
    self.xlim=lim
    self._caller('set_xlim', *lim)

  def set_ylim(self, lim):
    self.ylim=lim
    self._caller('set_ylim', *lim)

  def get_xlim(self): return self.xlim

  def get_ylim(self): return self.ylim

# objects used to mimic matplotlib classes that cannot be pickled as e.g. events
class TransferredAxes(object):
  def __init__(self, x, y):
    self.x=x
    self.y=y

  def format_coord(self, x, y):
    return 'x=%12g y=%12g'%(x, y)

  def get_navigate(self): return True

class TransferredEvent(object):
  inaxes=None

  def __init__(self, event, ax=None):
    for attr in self._attrs:
      if attr=='inaxes' and event.inaxes:
        self.inaxes=TransferredAxes(event.xdata, event.ydata)
      else:
        setattr(self, attr, getattr(event, attr, None))

class TransferredMouseEvent(TransferredEvent):
  _attrs=['x', 'y', 'inaxes', 'xdata', 'ydata', 'button', 'step', 'dblclick']

class TransferredKeyEvent(TransferredEvent):
  _attrs=['x', 'y', 'inaxes', 'xdata', 'ydata', 'key']

TransferredEvents={MouseEvent: TransferredMouseEvent,
             KeyEvent: TransferredKeyEvent}

class MPLProcess(FigureCanvasAgg, Process):
  '''
  Separate process carrying out plots with matplotlib in memory.
  Communication is done via three pipes. The first receives the
  method to be called and with which arguments, the second
  sends back any results and the third sends matplotlib event messages.
  '''
  _object_index=0

  def __init__(self, pipe_in, pipe_out, event_pipe,
               width=10, height=12, dpi=100., sharex=None, sharey=None, adjust={}):
    Process.__init__(self)
    self.pipe_in=pipe_in
    self.pipe_out=pipe_out
    self.event_pipe=event_pipe
    self.fig=Figure(figsize=(width, height), dpi=dpi, facecolor='#FFFFFF')
    FigureCanvasAgg.__init__(self, self.fig)
    self.ax=self.fig.add_subplot(111, sharex=sharex, sharey=sharey)
    self.ax2=None
    self.fig.subplots_adjust(left=0.15, bottom=0.1, right=0.95, top=0.95)
    self.xtitle=""
    self.ytitle=""
    self.PlotTitle=""
    self.grid_status=True
    self.xaxis_style='linear'
    self.yaxis_style='linear'
    self.ax.hold(True)
    self._connect_objects={}
    self.exit_set, self.exit_get=Pipe()

  def _connect_events(self):
    for name in ['button_press_event', 'button_release_event',
                  'key_press_event', 'key_release_event', 'motion_notify_event',
                  'pick_event',
                  'scroll_event',
                  'figure_enter_event',
                  'figure_leave_event',
                  'axes_enter_event',
                  'axes_leave_event']:
      callback=partial(self._event_callback, name)
      self.mpl_connect(name, callback)

  def _event_callback(self, s, event):
    try:
      event=TransferredEvents[event.__class__](event, ax=self.ax)
      self.event_pipe.send((s, event))
    except:
      pass

  def run(self):
    self._connect_events()
    while True:
      if not self.pipe_in.poll(0.05):
        if self.exit_get.poll(0.01):
          return
        continue
      # read everything from the pipe, to be able to drop unneeded actions before a clear call
      action_buffer=[]
      while self.pipe_in.poll():
        action_buffer.append(self.pipe_in.recv())
      for i, (action, ignore, ignore) in reversed(tuple(enumerate(action_buffer))):
        # if clear is amongst the calls drop everything before the last clear command
        if action=='clear':
          action_buffer=action_buffer[i:]
          break
      # apply actions
      for action, args, opts in action_buffer:
        result=getattr(self, action)(*args, **opts)
        self.pipe_out.send(result)

  def join(self, timeout=None):
    # send a signal to process to finish the loop
    self.exit_set.send(True)
    Process.join(self, timeout)

  ######### plotting related methods

  def _getPaintData(self):
    try:
      if QtCore.QSysInfo.ByteOrder==QtCore.QSysInfo.LittleEndian:
          stringBuffer=self.renderer._renderer.tostring_bgra()
      else:
          stringBuffer=self.renderer._renderer.tostring_argb()
      return stringBuffer, self.renderer.width, self.renderer.height
    except AttributeError:
      return '', 0, 0

  def plot(self, *args, **opts):
    return self._add_object(self.ax.plot(*args, **opts))

  def errorbar(self, *args, **opts):
    return self._add_object(self.ax.plot(*args, **opts))

  def semilogy(self, *args, **opts):
    return self._add_object(self.ax.semilogy(*args, **opts))

  def imshow(self, *args, **opts):
    return self._add_object(self.ax.imshow(*args, **opts))

  def pcolormesh(self, *args, **opts):
    return self._add_object(self.ax.pcolormesh(*args, **opts))

  def axvline(self, *args, **opts):
    return self._add_object(self.ax.axvline(*args, **opts))

  def axhline(self, *args, **opts):
    return self._add_object(self.ax.axHline(*args, **opts))

  def draw(self):
    FigureCanvasAgg.draw(self)
    return self._getPaintData()

  def clear(self):
    self.cplot=None
    self._connect_objects={}
    self.ax.clear()
    if self.ax2 is not None:
      self.ax2.clear()

  def set_size_inches(self, w, h):
    self.fig.set_size_inches(w, h)

  def _add_object(self, item):
    if type(item) is list:
      return map(self._add_object, item)
    if type(item) is tuple:
      return tuple(map(self._add_object, item))
    idx=self._object_index
    self._object_index+=1
    self._connect_objects[idx]=item
    citem=get_connected_object(item, idx)
    return citem

  def _object_call(self, index, name, args, opts):
    return index, getattr(self._connect_objects[index], name)(*args, **opts)

  def _fixed_object_call(self, attr, name, args, opts):
    if name=='_init_me':
      # use the classes own method to create initialization parameters to be returned
      return args[0]._do_init(getattr(self, attr))
    return getattr(getattr(self, attr), name)(*args, **opts)

class MPLProcessHolder(QtCore.QThread, QtCore.QObject):
  '''
  Interface between the MplBGCanvas and MplProcess objects. Mostly just runs
  in the background to send method calls to the process and emit signals
  depending on the result.
  '''
  MAX_IMAGE_SIZE=4*4000*4000
  drawFinished=QtCore.pyqtSignal()
  paintFinished=QtCore.pyqtSignal(object)
  eventEmitted=QtCore.pyqtSignal(object, object)

  def __init__(self, width=10, height=12, dpi=100., sharex=None, sharey=None, adjust={}):
    QtCore.QThread.__init__(self)
    self.pipe_in, pipe_in=Pipe()
    pipe_out, self.pipe_out=Pipe()
    event_pipe, self.event_pipe=Pipe()
    self.canvas_process=MPLProcess(pipe_in, pipe_out, event_pipe,
                                   width, height, dpi,
                                   sharex, sharey, adjust={})
    self.stay_alive=True
    self.scheduled_actions=[]
    self.scheduled_receives=[]
    self._plots=[]
    self._imgs=[]
    self._lines=[]
    self._objts=[]

    self.fig=ConnectedFigure(self, 'fig')
    self.ax=ConnectedAxes(self, 'ax')

  def run(self):
    # start the plot process
    self.canvas_process.start()
    # create a timer to regularly communicate with the process
    self.timer=QtCore.QTimer()
    self.timer.timeout.connect(self.checkit)
    self.timer.start(10)
    self.exec_()

  def checkit(self):
    if self.scheduled_actions:
      actions=list(self.scheduled_actions)
      # remove all but last draw from action list
      action_names=[a[0] for a in actions]
      for ignore in range(action_names.count('draw')-1):
        idx=action_names.index('draw')
        actions.pop(idx)
        action_names.pop(idx)
      self.scheduled_actions=[]
      map(self.pipe_in.send, actions)
      self.scheduled_receives+=actions
    paint_result=None
    while self.scheduled_receives and self.pipe_out.poll():
      item=self.scheduled_receives.pop(0)
      result=self.pipe_out.recv()
      if item[0]=='draw':
        paint_result=result
      elif item[0] in ['plot', 'errorbar', 'semilogy']:
        for resulti in result:
          resulti._parent=self
        self._plots+=result
        self._objts+=result
      elif item[0] in ['axvline', 'axhline']:
        result._parent=self
        self._lines.append(result)
        self._objts.append(result)
      elif item[0] in ['imshow', 'pcolormesh']:
        result._parent=self
        self._imgs.append(result)
        self._objts.append(result)
      elif item[0]=='_object_call':
        oidx=[obj._index for obj in self._objts]
        if result[0] in oidx:
          obj=self._objts[oidx.index(result[0])]._recall(item[0], result[1])
      elif item[0]=='_fixed_object_call':
        getattr(self, item[1][0])._recall(item[1][1], result)
    if paint_result:
        self.paintFinished.emit(paint_result)
    if self.event_pipe.poll():
      # process only last event of specific type
      evnts={}
      while self.event_pipe.poll():
        s, event=self.event_pipe.recv()
        evnts[s]=event
      for s, event in evnts.items():
        self.eventEmitted.emit(s, event)

  # Makes interfacing to the process convenient by passing
  # all methods available in the process class on access.
  # This means that thread.draw() will append ('draw', (), {}) to the process.
  def __getattr__(self, name):
    if not name.startswith("_") and not name in self.__dict__ and \
           (name in MPLProcess.__dict__ or name in FigureCanvasBase.__dict__):
      self.next_action=name
      return self
    return QtCore.QThread.__getattr__(self, name)

  def __call__(self, *args, **opts):
    self.scheduled_actions.append((self.next_action, args, opts))

class MPLBackgroundWidget(QtGui.QWidget, FigureCanvasBase):
  _running_threads=[]
  buttond={QtCore.Qt.LeftButton  : 1,
           QtCore.Qt.MidButton   : 2,
           QtCore.Qt.RightButton : 3,
           }

  def __init__(self, parent=None, width=10, height=12, dpi=100., sharex=None, sharey=None, adjust={}):
    QtGui.QWidget.__init__(self, parent)
    self.callbacks=CallbackRegistry()
    self.setMouseTracking(True)

    self.dpi=dpi
    self.width=width
    self.height=height
    self.draw_process=MPLProcessHolder(width, height, dpi, sharex, sharey, adjust)
    self.draw_process.paintFinished.connect(self.paintFinished)
    self.draw_process.eventEmitted.connect(self._event_callback)
    self.draw_process.start()
    self.drawRect=False
    self.stringBuffer=None
    self.buffer_width, self.buffer_height=0, 0
    self.resize(width, height)

  def update(self):
    QtGui.QWidget.update(self)

  def paintFinished(self, data):
    self.stringBuffer=data[0]
    self.buffer_width=data[1]
    self.buffer_height=data[2]
    self.update()

  def resizeEvent(self, event):
    QtGui.QWidget.resizeEvent(self, event)
    w=event.size().width()
    h=event.size().height()
    winch=w/self.dpi
    hinch=h/self.dpi
    self.width=w
    self.height=h
    self.draw_process.set_size_inches(winch, hinch)
    self.draw()

  def sizeHint(self):
      return QtCore.QSize(self.width, self.height)

  def minumumSizeHint(self):
      return QtCore.QSize(10, 10)

  def paintEvent(self, e):
    stringBuffer=self.stringBuffer
    if stringBuffer is None:
      return
    qImage=QtGui.QImage(stringBuffer, self.buffer_width, self.buffer_height,
                          QtGui.QImage.Format_ARGB32)
    p=QtGui.QPainter(self)
    p.drawPixmap(QtCore.QPoint(0, 0), QtGui.QPixmap.fromImage(qImage))

    # draw the zoom rectangle to the QPainter
    if self.drawRect:
        p.setPen(QtGui.QPen(QtCore.Qt.black, 1, QtCore.Qt.DotLine))
        p.drawRect(self.rect[0], self.rect[1], self.rect[2], self.rect[3])
    p.end()
    self.drawRect=False

  def draw(self):
    self.draw_process.draw()

  def drawRectangle(self, rect):
    self.rect=rect
    self.drawRect=True
    self.repaint()

  ###### user interaction events similar to matplotlib default but with process interaction ##
  def mousePressEvent(self, event):
    x=event.pos().x()
    # flipy so y=0 is bottom of canvas
    y=self.height-event.y()
    button=self.buttond.get(event.button())
    if button is not None:
        self.draw_process.button_press_event(x, y, button)

#  def mouseDoubleClickEvent(self, event):
#    x=event.pos().x()
#    # flipy so y=0 is bottom of canvas
#    y=self.height-event.y()
#    button=self.buttond.get(event.button())
#    if button is not None:
#        self.draw_process.button_press_event(x, y, button, dblclick=True)

  def mouseMoveEvent(self, event):
    x=event.x()
    # flipy so y=0 is bottom of canvas
    y=self.height-event.y()
    # communicate position to canvas to produce MPL event
    self.draw_process.motion_notify_event(x, y)

  def mouseReleaseEvent(self, event):
    x=event.x()
    # flipy so y=0 is bottom of canvas
    y=self.height-event.y()
    button=self.buttond.get(event.button())
    if button is not None:
        self.draw_process.button_release_event(x, y, button)

  def wheelEvent(self, event):
    x=event.x()
    # flipy so y=0 is bottom of canvas
    y=self.height-event.y()
    # from QWheelEvent::delta doc
    steps=event.delta()/120
    if (event.orientation()==QtCore.Qt.Vertical):
        self.draw_process.scroll_event(x, y, steps)

  def keyPressEvent(self, event):
    key=self._get_key(event)
    if key is None:
        return
    self.draw_process.key_press_event(key)

  def keyReleaseEvent(self, event):
    key=self._get_key(event)
    if key is None:
        return
    self.draw_process.key_release_event(key)

  def _event_callback(self, s, event):
    self.callbacks.process(s, event)

  # Makes interfacing to the process convenient by passing
  # all methods available in the process class on access.
  # This means that thread.draw() will append ('draw', (), {}) to the process.
  def __getattr__(self, name):
    if not name.startswith("_") and not name in self.__dict__ and name in MPLProcess.__dict__:
      return getattr(self.draw_process, name)
    return QtGui.QWidget.__getattr__(self, name)

class BackgroundNavigationToolbar(NavigationToolbar2QT, QtGui.QToolBar):
  def __init__(self, canvas, parent, coordinates=True):
    NavigationToolbar2QT.__init__(self, canvas, parent, coordinates)
    self.draw_rubberband(None, 10, 200, 40, 500)

  def draw_rubberband(self, event, x0, y0, x1, y1):
    height=self.canvas.height
    y1=height-y1
    y0=height-y0

    w=abs(x1-x0)
    h=abs(y1-y0)

    rect=[int(val) for val in (min(x0, x1), min(y0, y1), w, h)]
    self.canvas.drawRectangle(rect)

if __name__=='__main__':
  app=QtGui.QApplication([])
  dia=QtGui.QDialog()
  dia.resize(800, 600)
  hbox=QtGui.QHBoxLayout(dia)
  left=QtGui.QWidget(dia)
  right=QtGui.QWidget(dia)
  vbox1=QtGui.QVBoxLayout(left)
  vbox2=QtGui.QVBoxLayout(right)
  hbox.addWidget(left, 1)
  hbox.addWidget(right, 1)
  import numpy as np
  plots=[]
  def line_follow(event):
    if event.inaxes:
      if event.button:
        for plot in plots:
          plot.draw_process._lines[1].set_xdata([event.xdata, event.xdata])
          plot.draw()
      else:
        for plot in plots:
          plot.draw_process._lines[0].set_xdata([event.xdata, event.xdata])
          plot.draw()
  for i in range(10):
    # start 4 processes with plots
    plot=MPLBackgroundWidget(left)
    vbox1.addWidget(plot)
    for j in range(50):
      plot.plot(np.arange(100)*j)
    plot.axvline(10)
    plot.axvline(50, color='red')
    plot.draw()
    plot.mpl_connect('motion_notify_event', line_follow)
    plots.append(plot)

  implot=MPLBackgroundWidget(right)
  vbox2.addWidget(implot)
  y, x=np.mgrid[0:201:4000j, 0:201:4000j]
  z=-(x-100)**2-(y-100)**2
  implot.imshow(z, extent=[0, 200, 200, 0])
  implot.draw()
  def follow_pos(event):
    if not event.inaxes:
      return
    if event.button==1:
      z=-(x-event.xdata)**2-(y-event.ydata)**2
    else:
      z=(x-event.xdata)**2+(y-event.ydata)**2-20000
    implot.draw_process._imgs[0].set_data(z)
    implot.draw()
  implot.mpl_connect('button_press_event', follow_pos)

  tb=BackgroundNavigationToolbar(implot, right)
  vbox2.addWidget(tb)
  dia.show()
  exit(app.exec_())
