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
from cPickle import PicklingError
from PyQt4 import QtCore, QtGui

from multiprocessing import Process, Pipe, Event
from matplotlib.cbook import CallbackRegistry
from matplotlib.backend_bases import FigureCanvasBase, MouseEvent, KeyEvent
from matplotlib.axes import Axes
from matplotlib.backends.backend_agg import FigureCanvasAgg, Figure
from matplotlib.backends.backend_qt4 import NavigationToolbar2QT
from matplotlib.lines import Line2D
from matplotlib.container import ErrorbarContainer
from matplotlib.collections import LineCollection
from matplotlib.image import AxesImage
from matplotlib.legend import Legend
from matplotlib.collections import QuadMesh
from matplotlib import widgets
from matplotlib.transforms import Affine2D, CompositeGenericTransform
from matplotlib.colors import LogNorm

from logging import debug, error

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

class ConnectedLineCollection(ConnectedObject):
  _type=LineCollection

class ConnectedImage(ConnectedObject):
  _type=AxesImage

  def set_clim(self, *args, **opts):
    return self._caller('set_clim', *args, **opts)

class ConnectedQuadMesh(ConnectedObject):
  _type=QuadMesh

def get_connected_object(item, index):
  known_classes=[subcls._type for subcls in ConnectedObject.__subclasses__()]
  if not item.__class__ in known_classes:
    print item.__class__
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
      self._init(result)

  def _init(self, result):
    self.__dict__.update(result)

  def _update(self, result):
    self._init(result)

  @classmethod
  def _do_init(cls, obj):
    return {}

  @classmethod
  def _do_update(cls, obj):
    return cls._do_init(obj)

class ConnectedFigure(FixedConnectedObject):
  _type=Figure
  pass

class BBox(object):
  extents=[0., 0., 0., 0.]

class ConnectedAxes(FixedConnectedObject):
  _type=Axes
  viewLim=None
  transData=None
  bbox=BBox()

  def _init(self, result):
    self.__dict__.update(result)
#    self.transData=Affine2D(self.transData_data)

  @classmethod
  def _do_init(cls, obj):
    xlim=obj.get_xlim()
    ylim=obj.get_ylim()
    pos=obj.get_position()
    bbox=BBox()
    bbox.extents=obj.bbox.extents
    viewLim=BBox()
    viewLim.extents=obj.viewLim.extents
    transData=[]#obj.transData.frozen().to_values()

    return dict(xlim=xlim, ylim=ylim,
                points=pos._points,
                points_orig=pos._points_orig,
                bbox=bbox, viewLim=viewLim,
                transData=transData)

  def set_xlim(self, *lim):
    if len(lim)==1:
      lim=lim[0]
    self.xlim=lim
    self._caller('set_xlim', *lim)

  def set_ylim(self, *lim):
    if len(lim)==1:
      lim=lim[0]
    self.ylim=lim
    self._caller('set_ylim', *lim)

  def get_xlim(self): return self.xlim

  def get_ylim(self): return self.ylim

  def get_position(self, orig=False):
    if orig:
      return self.points_orig
    else:
      return self.points

  def can_zoom(self):
    return True

  def get_navigate(self):
    return True

class ConnectedLegend(ConnectedObject):
  _type=Legend

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

class AttribCaller(object):

  def __init__(self, parent, name):
    self._parent=parent
    self._name=name

  def __getattr__(self, name):
    if not name.startswith("_") and not name in self.__dict__:
      return partial(self._caller, name)

  def _caller(self, name, *args, **opts):
    self._parent.scheduled_actions.append(('_attrib_call', (self._name, name, args, opts), {}))

class MPLProcess(FigureCanvasAgg, Process):
  '''
  Separate process carrying out plots with matplotlib in memory.
  Communication is done via three pipes. The first receives the
  method to be called and with which arguments, the second
  sends back any results and the third sends matplotlib event messages.
  '''
  _object_index=0
  cplot=None

  def __init__(self, pipe_in, pipe_out, event_pipe, action_pending,
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
    self._fixed_connect_objects={}
    self.exitEvent=Event()
    self.parentActionPending=action_pending

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
      self.parentActionPending.set()
    except:
      pass

  def run(self):
    self._connect_events()
    self.exitEvent.clear()
    self.parentActionPending.clear()
    while not self.exitEvent.is_set():
      try:
        self._run()
      except Exception, error:
        error('Error in process:'+str(error))

  def _run(self):
    action_buffer=[]
    while not self.exitEvent.is_set():
      if self.exitEvent.is_set():
        return
      if not (action_buffer or self.pipe_in.poll(0.05)):
        continue
      # read everything from the pipe, to be able to drop unneeded actions before a clear call
      while self.pipe_in.poll():
        action_buffer.append(self.pipe_in.recv())
      # apply actions
      if action_buffer:
        action, args, opts=action_buffer.pop(0)
        if action=='draw' and 'draw' in [buf[0] for buf in action_buffer]:
          # there is another draw following so skip this one
          self.pipe_out.send(None)
          self.parentActionPending.set()
          continue
        # call the method given as action
        result=getattr(self, action)(*args, **opts)
        try:
          self.pipe_out.send(result)
          self.parentActionPending.set()
        except PicklingError:
          print "Can't pickle object for function call return: "+repr(result)
          self.pipe_out.send(None)
          self.parentActionPending.set()

  def join(self, timeout=None):
    # send a signal to process to finish the loop
    self.exitEvent.set()
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
    return self._add_object(self.ax.errorbar(*args, **opts))

  def semilogy(self, *args, **opts):
    return self._add_object(self.ax.semilogy(*args, **opts))

  def imshow(self, *args, **opts):
    self.cplot=self.ax.imshow(*args, **opts)
    return self._add_object(self.cplot)

  def pcolormesh(self, *args, **opts):
    self.cplot=self.ax.pcolormesh(*args, **opts)
    return self._add_object(self.cplot)

  def axvline(self, *args, **opts):
    return self._add_object(self.ax.axvline(*args, **opts))

  def axhline(self, *args, **opts):
    return self._add_object(self.ax.axhline(*args, **opts))

  def set_xlabel(self, *args, **opts):
    self.ax.set_xlabel(*args, **opts)

  def set_ylabel(self, *args, **opts):
    self.ax.set_xlabel(*args, **opts)

  def set_xscale(self, *args, **opts):
    self.ax.set_xscale(*args, **opts)

  def set_yscale(self, *args, **opts):
    self.ax.set_yscale(*args, **opts)

  def set_xlim(self, *args, **opts):
    self.ax.set_xlim(*args, **opts)

  def set_ylim(self, *args, **opts):
    self.ax.set_ylim(*args, **opts)

  def axis(self, *args, **opts):
    self.ax.axis(*args, **opts)

  def get_config(self):
    spp=self.fig.subplotpars
    config=dict(left=spp.left,
                right=spp.right,
                bottom=spp.bottom,
                top=spp.top)
    return config

  def legend(self, *args, **opts):
    return self._add_object(self.ax.legend(*args, **opts))

  def draw(self):
    FigureCanvasAgg.draw(self)
    self._update_fixed_objects()
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
    if type(item) is ErrorbarContainer:
      return list(map(self._add_object, item))
    idx=self._object_index
    self._object_index+=1
    self._connect_objects[idx]=item
    citem=get_connected_object(item, idx)
    self._update_fixed_objects()
    return citem

  def _object_call(self, index, name, args, opts):
    return index, getattr(self._connect_objects[index], name)(*args, **opts)

  def _attrib_call(self, attrib, name, args, opts):
    return getattr(getattr(self, attrib), name)(*args, **opts)

  def _update_fixed_objects(self):
    for attr, cls in self._fixed_connect_objects.items():
      result=cls._do_update(getattr(self, attr))
      self.event_pipe.send((attr, result))
      self.parentActionPending.set()

  def _fixed_object_call(self, attr, name, args, opts):
    if name=='_init_me':
      # use the classes own method to create initialization parameters to be returned
      self._fixed_connect_objects[attr]=args[0]
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
  cplot=None
  vlines=[]
  hlines=[]

  def __init__(self, width=10, height=12, dpi=100., sharex=None, sharey=None, adjust={}):
    QtCore.QThread.__init__(self)
    pipe_in, self.pipe_in=Pipe(False)
    self.pipe_out, pipe_out=Pipe(False)
    self.event_pipe, event_pipe=Pipe(False)
    self.actionPending=Event()
    self.canvas_process=MPLProcess(pipe_in, pipe_out, event_pipe, self.actionPending,
                                   width, height, dpi,
                                   sharex, sharey, adjust={})
    self.stay_alive=True
    self.scheduled_actions=[]
    self.scheduled_receives=[]
    self._plots=[]
    self._imgs=[]
    self.vlines=[]
    self.hlines=[]
    self._objts=[]

    self.fig=ConnectedFigure(self, 'fig')
    self.figure=self.fig
    self.ax=ConnectedAxes(self, 'ax')
    self.cplot=AttribCaller(self, 'cplot')

  def run(self):
    while True:
      try:
        self._run()
      except:
        error('ERROR in Thread %i:'%self.currentThreadId(), exc_info=True)

  def _run(self):
    # start the plot process
    self.canvas_process.start()
    # create a timer to regularly communicate with the process
    while True:
      if self.scheduled_actions:
        self.checkit()
      if self.pipe_out.poll():
        self.check_result()
      if self.event_pipe.poll():
        self.check_event()
      if not self.scheduled_actions and not self.scheduled_receives:
        self.actionPending.clear()
        self.actionPending.wait(1.) # don't block forever in some unforeseen situation

  def checkit(self):
    if self.scheduled_actions:
      debug('Thread %i enter actions'%self.currentThreadId())
      actions=self.scheduled_actions
      self.scheduled_actions=[]
      map(self.pipe_in.send, actions)
      self.scheduled_receives+=actions

  def check_result(self):
    paint_result=None
    while self.scheduled_receives and self.pipe_out.poll():
      debug('Thread %i enter results'%self.currentThreadId())
      item=self.scheduled_receives.pop(0)
      result=self.pipe_out.recv()
      if item[0]=='draw' and result is not None:
        paint_result=result
      elif item[0] in ['plot', 'errorbar', 'semilogy']:
        for resulti in result:
          if type(resulti) is tuple:
            for resultj in resulti:
              resultj._parent=self
          else:
            resulti._parent=self
        self._plots+=result
        self._objts+=result
      elif item[0] in ['axvline', 'axhline']:
        result._parent=self
        if item[0]=='axvline':
          self.vlines.append(result)
        else:
          self.hlines.append(result)
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
      elif item[0]=='clear':
        self.vlines=[]
        self.hlines=[]
    if paint_result:
        self.paintFinished.emit(paint_result)

  def check_event(self):
    # process only last event of specific type
    evnts={}
    while self.event_pipe.poll():
      debug('Thread %i enter event'%self.currentThreadId())
      s, event=self.event_pipe.recv()
      if s in ['fig', 'ax']:
        getattr(self, s)._update(event)
      else:
        evnts[s]=event
    for s, event in evnts.items():
      self.eventEmitted.emit(s, event)


  def imshow(self, data, log=False, imin=None, imax=None, update=True, **opts):
    '''
      Convenience wrapper for self.canvas.ax.plot
    '''
    self.next_action='imshow'
    if log:
      self(data, norm=LogNorm(imin, imax), **opts)
    else:
      self(data, **opts)
    return self.cplot

  def pcolormesh(self, data, log=False, imin=None, imax=None, update=True, **opts):
    '''
      Convenience wrapper for self.canvas.ax.plot
    '''
    self.next_action='pcolormesh'
    if log:
      self(data, norm=LogNorm(imin, imax), **opts)
    else:
      self(data, **opts)
    return self.cplot


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
    debug('Thread %i - Call method '%self.currentThreadId()+self.next_action)
    self.scheduled_actions.append((self.next_action, args, opts))
    self.actionPending.set()

class MPLBackgroundWidget(QtGui.QWidget, FigureCanvasBase):
  _running_threads=[]
  buttond={QtCore.Qt.LeftButton  : 1,
           QtCore.Qt.MidButton   : 2,
           QtCore.Qt.RightButton : 3,
           }
  vbox=None
  toolbar=None

  def __init__(self, parent=None, width=10, height=12, dpi=100., sharex=None, sharey=None, adjust={},
               toolbar=True):
    QtGui.QWidget.__init__(self, parent)
    self.setContentsMargins(0, 0, 0, 0)
    self.callbacks=CallbackRegistry()
    self.widgetlock=widgets.LockDraw()

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

    self.vbox=QtGui.QVBoxLayout(self)
    self.setMouseTracking(True)
    self.vbox.addStretch(1)
    if toolbar:
      self.toolbar=BackgroundNavigationToolbar(self, self)
      self.vbox.addWidget(self.toolbar, 0, QtCore.Qt.AlignBottom)
      self.tb_offset=self.toolbar.height()+5
    else:
      self.tb_offset=0.

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
    h=event.size().height()-self.tb_offset
    winch=w/self.dpi
    hinch=h/self.dpi
    self.width=w
    self.height=h
    self.draw_process.set_size_inches(winch, hinch)
    self.draw()

  def sizeHint(self):
      return QtCore.QSize(self.width, self.height+self.tb_offset)

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
    if not name.startswith("_") and not name in self.__dict__ and (name in MPLProcess.__dict__ or
                                                                   name in MPLProcessHolder.__dict__):
      return getattr(self.draw_process, name)
    return QtGui.QWidget.__getattr__(self, name)

class BackgroundNavigationToolbar(NavigationToolbar2QT, QtGui.QToolBar):
  def __init__(self, canvas, parent, coordinates=True):
    NavigationToolbar2QT.__init__(self, canvas, parent, coordinates)
    self.draw_process=canvas.draw_process

  def draw_rubberband(self, event, x0, y0, x1, y1):
    height=self.canvas.height
    y1=height-y1
    y0=height-y0

    w=abs(x1-x0)
    h=abs(y1-y0)

    rect=[int(val) for val in (min(x0, x1), min(y0, y1), w, h)]
    self.canvas.drawRectangle(rect)

  def zoom(self, *args):
    'activate zoom to rect mode'
    if self._active=='ZOOM':
      self._active=None
    else:
      self._active='ZOOM'

    if self._idPress is not None:
      self._idPress=self.canvas.mpl_disconnect(self._idPress)
      self.mode=''

    if self._idRelease is not None:
      self._idRelease=self.canvas.mpl_disconnect(self._idRelease)
      self.mode=''

    if  self._active:
      self._idPress=self.canvas.mpl_connect('button_press_event', self.press_zoom)
      self._idRelease=self.canvas.mpl_connect('button_release_event', self.release_zoom)
      self.mode='zoom rect'
      self.canvas.widgetlock(self)
    else:
        self.canvas.widgetlock.release(self)

    self.draw_process.ax.set_navigate_mode(self._active)

    self.set_message(self.mode)

  def press_zoom(self, event):
    'the press mouse button in zoom to rect mode callback'
    if event.button==1:
      self._button_pressed=1
    elif  event.button==3:
      self._button_pressed=3
    else:
      self._button_pressed=None
      return

    x, y, xdata, ydata=event.x, event.y, event.xdata, event.ydata

    # push the current view to define home if stack is empty
    if self._views.empty(): self.push_current()

    self._xypress=[]
    i, a=0, self.draw_process.ax
    if (x is not None and y is not None and event.inaxes and
      a.get_navigate() and a.can_zoom()) :
      self._xypress.append((x, y, a, i, a.viewLim,
                             [xdata, ydata]))

    id1=self.canvas.mpl_connect('motion_notify_event', self.drag_zoom)

    id2=self.canvas.mpl_connect('key_press_event',
                                  self._switch_on_zoom_mode)
    id3=self.canvas.mpl_connect('key_release_event',
                                  self._switch_off_zoom_mode)

    self._ids_zoom=id1, id2, id3

    self._zoom_mode=None


    self.press(event)

  def release_zoom(self, event):
    'the release mouse button callback in zoom to rect mode'
    for zoom_id in self._ids_zoom:
        self.canvas.mpl_disconnect(zoom_id)
    self._ids_zoom=[]

    if not self._xypress: return

    last_a=[]

    for cur_xypress in self._xypress:
      x, y=event.x, event.y
      lastx, lasty, a, ind, lim, trans=cur_xypress
      # ignore singular clicks - 5 pixels is a threshold
      if abs(x-lastx)<5 or abs(y-lasty)<5:
          self._xypress=None
          self.release(event)
          self.draw()
          return

      x0, y0, x1, y1=lim.extents

      # zoom to rect
#      inverse=a.transData.inverted()
#      lastx, lasty=inverse.transform_point((lastx, lasty))
#      x, y=inverse.transform_point((x, y))
      lastx, lasty=trans
      x, y=event.xdata, event.ydata
      Xmin, Xmax=a.get_xlim()
      Ymin, Ymax=a.get_ylim()

      # detect twinx,y axes and avoid double zooming
      twinx, twiny=False, False
      if last_a:
          for la in last_a:
              if a.get_shared_x_axes().joined(a, la): twinx=True
              if a.get_shared_y_axes().joined(a, la): twiny=True
      last_a.append(a)

      if twinx:
          x0, x1=Xmin, Xmax
      else:
          if Xmin<Xmax:
              if x<lastx:  x0, x1=x, lastx
              else: x0, x1=lastx, x
              if x0<Xmin: x0=Xmin
              if x1>Xmax: x1=Xmax
          else:
              if x>lastx:  x0, x1=x, lastx
              else: x0, x1=lastx, x
              if x0>Xmin: x0=Xmin
              if x1<Xmax: x1=Xmax

      if twiny:
          y0, y1=Ymin, Ymax
      else:
          if Ymin<Ymax:
              if y<lasty:  y0, y1=y, lasty
              else: y0, y1=lasty, y
              if y0<Ymin: y0=Ymin
              if y1>Ymax: y1=Ymax
          else:
              if y>lasty:  y0, y1=y, lasty
              else: y0, y1=lasty, y
              if y0>Ymin: y0=Ymin
              if y1<Ymax: y1=Ymax

      if self._button_pressed==1:
          if self._zoom_mode=="x":
              a.set_xlim((x0, x1))
          elif self._zoom_mode=="y":
              a.set_ylim((y0, y1))
          else:
              a.set_xlim((x0, x1))
              a.set_ylim((y0, y1))
      elif self._button_pressed==3:
          if a.get_xscale()=='log':
              alpha=np.log(Xmax/Xmin)/np.log(x1/x0)
              rx1=pow(Xmin/x0, alpha)*Xmin
              rx2=pow(Xmax/x0, alpha)*Xmin
          else:
              alpha=(Xmax-Xmin)/(x1-x0)
              rx1=alpha*(Xmin-x0)+Xmin
              rx2=alpha*(Xmax-x0)+Xmin
          if a.get_yscale()=='log':
              alpha=np.log(Ymax/Ymin)/np.log(y1/y0)
              ry1=pow(Ymin/y0, alpha)*Ymin
              ry2=pow(Ymax/y0, alpha)*Ymin
          else:
              alpha=(Ymax-Ymin)/(y1-y0)
              ry1=alpha*(Ymin-y0)+Ymin
              ry2=alpha*(Ymax-y0)+Ymin

          if self._zoom_mode=="x":
              a.set_xlim((rx1, rx2))
          elif self._zoom_mode=="y":
              a.set_ylim((ry1, ry2))
          else:
              a.set_xlim((rx1, rx2))
              a.set_ylim((ry1, ry2))

    self.draw()
    self._xypress=None
    self._button_pressed=None

    self._zoom_mode=None

    self.push_current()
    self.release(event)

  def push_current(self):
    'push the current view limits and position onto the stack'
    lims=[]; pos=[]
    a=self.draw_process.ax
    xmin, xmax=a.get_xlim()
    ymin, ymax=a.get_ylim()
    lims.append((xmin, xmax, ymin, ymax))
    # Store both the original and modified positions
    pos.append((a.get_position(True), a.get_position()))
    self._views.push(lims)
    self._positions.push(pos)
    self.set_history_buttons()

  def draw(self):
    self.canvas.draw()



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
          plot.draw_process.vlines[1].set_xdata([event.xdata, event.xdata])
          plot.draw()
      else:
        for plot in plots:
          plot.draw_process.vlines[0].set_xdata([event.xdata, event.xdata])
          plot.draw()
  for i in range(10):
    # start 4 processes with plots
    plot=MPLBackgroundWidget(left, toolbar=False)
    vbox1.addWidget(plot)
    for j in range(50):
      plot.plot(np.arange(100)*j)
    plot.axvline(10)
    plot.axvline(50, color='red')
    plot.draw()
    plot.mpl_connect('motion_notify_event', line_follow)
    plots.append(plot)

  implot=MPLBackgroundWidget(right, toolbar=True)
  vbox2.addWidget(implot)
  y, x=np.mgrid[0:201:4000j, 0:201:4000j]
  z=-(x-100)**2-(y-100)**2
  implot.imshow(z, extent=[0, 200, 200, 0])
  implot.draw()
  rect_1=[0., 0.]
  def follow_pos(event):
    if not event.inaxes:
      return
    if event.button==1:
      z=-(x-event.xdata)**2-(y-event.ydata)**2
      rect_1[0]=event.x
      rect_1[1]=event.y
    else:
      z=(x-event.xdata)**2+(y-event.ydata)**2-20000
    implot.draw_process._imgs[0].set_data(z)
    implot.draw()
  implot.mpl_connect('button_press_event', follow_pos)

  dia.show()
  exit(app.exec_())
