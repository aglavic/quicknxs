#!/usr/bin/env python
import os
import tempfile
from multiprocessing import Process, Pipe
from PyQt4 import QtCore, QtGui
import matplotlib.cm
import matplotlib.colors
from . import icons_rc #@UnusedImport

font={
      #'family' : 'sans',
      #  'weight' : 'normal',
        'variant': 'DejaVuSerif',
        'size': 7,
        }
savefig={
         'dpi': 600,
         }

# set the default backend to be compatible with Qt in case someone uses pylab from IPython console
matplotlib.use('Qt4Agg')
def _set_default_rc():
  matplotlib.rc('font', **font)
  matplotlib.rc('savefig', **savefig)
_set_default_rc()

cmap=matplotlib.colors.LinearSegmentedColormap.from_list('default',
                  ['#0000ff', '#00ff00', '#ffff00', '#ff0000', '#bd7efc', '#000000'], N=256)
matplotlib.cm.register_cmap('default', cmap=cmap)

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4 import NavigationToolbar2QT
from matplotlib.cbook import Stack
from matplotlib.colors import LogNorm, Normalize
from matplotlib.figure import Figure
try:
    import matplotlib.backends.qt4_editor.figureoptions as figureoptions
except ImportError:
    figureoptions=None

class NavigationToolbar(NavigationToolbar2QT):
  '''
    A small change to the original navigation toolbar.
  '''
  _auto_toggle=False

  def __init__(self, canvas, parent, coordinates=False):
    NavigationToolbar2QT.__init__(self, canvas, parent, coordinates)
    self.setIconSize(QtCore.QSize(20, 20))

  def _init_toolbar(self):
    if not hasattr(self, '_actions'):
      self._actions={}
    self.basedir=os.path.join(matplotlib.rcParams[ 'datapath' ], 'images')

    icon=QtGui.QIcon()
    icon.addPixmap(QtGui.QPixmap(":/MPL Toolbar/go-home.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
    a=self.addAction(icon, 'Home', self.home)
    a.setToolTip('Reset original view')
    icon=QtGui.QIcon()
    icon.addPixmap(QtGui.QPixmap(":/MPL Toolbar/zoom-previous.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
    a=self.addAction(icon, 'Back', self.back)
    a.setToolTip('Back to previous view')
    icon=QtGui.QIcon()
    icon.addPixmap(QtGui.QPixmap(":/MPL Toolbar/zoom-next.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
    a=self.addAction(icon, 'Forward', self.forward)
    a.setToolTip('Forward to next view')
    self.addSeparator()
    icon=QtGui.QIcon()
    icon.addPixmap(QtGui.QPixmap(":/MPL Toolbar/transform-move.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
    a=self.addAction(icon, 'Pan', self.pan)
    a.setToolTip('Pan axes with left mouse, zoom with right')
    a.setCheckable(True)
    self._actions['pan']=a
    icon=QtGui.QIcon()
    icon.addPixmap(QtGui.QPixmap(":/MPL Toolbar/zoom-select.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
    a=self.addAction(icon, 'Zoom', self.zoom)
    a.setToolTip('Zoom to rectangle')
    a.setCheckable(True)
    self._actions['zoom']=a
    self.addSeparator()
    icon=QtGui.QIcon()
    icon.addPixmap(QtGui.QPixmap(":/MPL Toolbar/edit-guides.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
    a=self.addAction(icon, 'Subplots', self.configure_subplots)
    a.setToolTip('Configure plot boundaries')

    icon=QtGui.QIcon()
    icon.addPixmap(QtGui.QPixmap(":/MPL Toolbar/document-save.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
    a=self.addAction(icon, 'Save', self.save_figure)
    a.setToolTip('Save the figure')

    icon=QtGui.QIcon()
    icon.addPixmap(QtGui.QPixmap(":/MPL Toolbar/document-print.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
    a=self.addAction(icon, 'Print', self.print_figure)
    a.setToolTip('Print the figure with the default printer')

    icon=QtGui.QIcon()
    icon.addPixmap(QtGui.QPixmap(":/MPL Toolbar/toggle-log.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
    self.addSeparator()
    a=self.addAction(icon, 'Log', self.toggle_log)
    a.setToolTip('Toggle logarithmic scale')


    self.buttons={}

    # Add the x,y location widget at the right side of the toolbar
    # The stretch factor is 1 which means any resizing of the toolbar
    # will resize this label instead of the buttons.
    self.locLabel=QtGui.QLabel("", self)
    self.locLabel.setAlignment(
            QtCore.Qt.AlignRight|QtCore.Qt.AlignTop)
    self.locLabel.setSizePolicy(
        QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding,
                          QtGui.QSizePolicy.Ignored))
    self.labelAction=self.addWidget(self.locLabel)
    if self.coordinates:
      self.labelAction.setVisible(True)
    else:
      self.labelAction.setVisible(False)

    # reference holder for subplots_adjust window
    self.adj_window=None

  if matplotlib.__version__<'1.2':
    def pan(self, *args):
      'Activate the pan/zoom tool. pan with left button, zoom with right'
      # set the pointer icon and button press funcs to the
      # appropriate callbacks
      if self._auto_toggle:
        return
      if self._active=='ZOOM':
        self._auto_toggle=True
        self._actions['zoom'].setChecked(False)
        self._auto_toggle=False

      if self._active=='PAN':
        self._active=None
      else:
        self._active='PAN'
      if self._idPress is not None:
        self._idPress=self.canvas.mpl_disconnect(self._idPress)
        self.mode=''

      if self._idRelease is not None:
        self._idRelease=self.canvas.mpl_disconnect(self._idRelease)
        self.mode=''

      if self._active:
        self._idPress=self.canvas.mpl_connect(
            'button_press_event', self.press_pan)
        self._idRelease=self.canvas.mpl_connect(
            'button_release_event', self.release_pan)
        self.mode='pan/zoom'
        self.canvas.widgetlock(self)
      else:
        self.canvas.widgetlock.release(self)

      for a in self.canvas.figure.get_axes():
        a.set_navigate_mode(self._active)

      self.set_message(self.mode)

    def zoom(self, *args):
      'activate zoom to rect mode'
      if self._auto_toggle:
        return
      if self._active=='PAN':
        self._auto_toggle=True
        self._actions['pan'].setChecked(False)
        self._auto_toggle=False

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

      for a in self.canvas.figure.get_axes():
        a.set_navigate_mode(self._active)

      self.set_message(self.mode)

  def print_figure(self):
    '''
      Save the plot to a temporary png file and show a preview dialog also used for printing.
    '''
    filetypes=self.canvas.get_supported_filetypes_grouped()
    sorted_filetypes=filetypes.items()
    sorted_filetypes.sort()

    filename=os.path.join(tempfile.gettempdir(), u"quicknxs_print.png")
    self.canvas.print_figure(filename, dpi=600)
    imgpix=QtGui.QPixmap(filename)
    os.remove(filename)

    imgobj=QtGui.QLabel()
    imgobj.setPixmap(imgpix)
    imgobj.setMask(imgpix.mask())
    imgobj.setGeometry(0, 0, imgpix.width(), imgpix.height())

    def getPrintData(printer):
      imgobj.render(printer)


    printer=QtGui.QPrinter()
    printer.setPrinterName('mrac4a_printer')
    printer.setPageSize(QtGui.QPrinter.Letter)
    printer.setResolution(600)
    printer.setOrientation(QtGui.QPrinter.Landscape)

    pd=QtGui.QPrintPreviewDialog(printer)
    pd.paintRequested.connect(getPrintData)
    pd.exec_()

  def save_figure(self, *args):
      filetypes=self.canvas.get_supported_filetypes_grouped()
      sorted_filetypes=filetypes.items()
      sorted_filetypes.sort()
      default_filetype=self.canvas.get_default_filetype()

      start="image."+default_filetype
      filters=[]
      for name, exts in sorted_filetypes:
          exts_list=" ".join(['*.%s'%ext for ext in exts])
          filter_='%s (%s)'%(name, exts_list)
          if default_filetype in exts:
            filters.insert(0, filter_)
          else:
            filters.append(filter_)
      filters=';;'.join(filters)

      fname=QtGui.QFileDialog.getSaveFileName(self, u"Choose a filename to save to", start, filters)
      if fname:
          try:
              self.canvas.print_figure(unicode(fname))
          except Exception, e:
              QtGui.QMessageBox.critical(
                  self, "Error saving file", str(e),
                  QtGui.QMessageBox.Ok, QtGui.QMessageBox.NoButton)

  def toggle_log(self, *args):
    ax=self.canvas.ax
    if len(ax.images)==0 and all([c.__class__.__name__!='QuadMesh' for c in ax.collections]):
      logstate=ax.get_yscale()
      if logstate=='linear':
        ax.set_yscale('log')
      else:
        ax.set_yscale('linear')
      self.canvas.draw()
    else:
      imgs=ax.images+[c for c in ax.collections if c.__class__.__name__=='QuadMesh']
      norm=imgs[0].norm
      if norm.__class__ is LogNorm:
        for img in imgs:
          img.set_norm(Normalize(norm.vmin, norm.vmax))
      else:
        for img in imgs:
          img.set_norm(LogNorm(norm.vmin, norm.vmax))
    self.canvas.draw()

'''
The background plotting canvas uses a three object model:
  - A separate thread carries out the plotting work and sends the raw image over a pipe.
  - A QThread runs in the background communicating with the process over a pipe and
    with the GUI via signals.
  - A widget contains the plotting relevant function and sends it to the thread,
    this widget has to implement all functionalities normally provided by the Qt4Add
    backend of matplotlib.
'''
class MplProcess(FigureCanvasAgg, Process):
  '''
  Separate process carrying out plots with matplotlib in memory.
  Communication is done via two pipes. The first receives the
  method to be called and with which arguments, the second
  sends back any results.
  '''
  def __init__(self, pipe_in, pipe_out, width=10, height=12, dpi=100., sharex=None, sharey=None, adjust={}):
    Process.__init__(self)
    self.pipe_in=pipe_in
    self.pipe_out=pipe_out
    self.fig=Figure(figsize=(width, height), dpi=dpi, facecolor='#FFFFFF')
    FigureCanvasAgg.__init__(self, self.fig)
    self.ax=self.fig.add_subplot(111, sharex=sharex, sharey=sharey)
    self.fig.subplots_adjust(left=0.15, bottom=0.1, right=0.95, top=0.95)
    self.xtitle=""
    self.ytitle=""
    self.PlotTitle=""
    self.grid_status=True
    self.xaxis_style='linear'
    self.yaxis_style='linear'
    self.ax.hold(True)
    self._plots=[]
    self.exit_set, self.exit_get=Pipe()

  def run(self):
    while True:
      if not self.pipe_in.poll(0.05):
        if self.exit_get.poll(0.01):
          return
        continue
      action, args, opts=self.pipe_in.recv()
      if action=='exit':
        return
      result=getattr(self, action)(*args, **opts)
      self.pipe_out.send(result)
  
  def join(self, timeout=None):
    # send a signal to process to finish the loop
    self.exit_set.send(True)
    Process.join(self, timeout)

  def getPaintData(self):
    if QtCore.QSysInfo.ByteOrder==QtCore.QSysInfo.LittleEndian:
        stringBuffer=self.renderer._renderer.tostring_bgra()
    else:
        stringBuffer=self.renderer._renderer.tostring_argb()
    return stringBuffer, self.renderer.width, self.renderer.height

  def plot(self, *args, **opts):
    self._plots.append(self.ax.plot(*args, **opts))

  def draw(self):
    FigureCanvasAgg.draw(self)

  def set_size_inches(self, w, h):
    self.fig.set_size_inches(w, h)
  

class MplProcessHolder(QtCore.QThread, QtCore.QObject):
  '''
  Interface between the MplBGCanvas and MplProcess objects. Mostly just runs
  in the background to send method calls to the process and emit signals
  depending on the result.
  '''  
  drawFinished=QtCore.pyqtSignal()
  paintFinished=QtCore.pyqtSignal(object)

  def __init__(self, width=10, height=12, dpi=100., sharex=None, sharey=None, adjust={}):
    QtCore.QThread.__init__(self)
    self.pipe_in, pipe_in=Pipe()
    pipe_out, self.pipe_out=Pipe()
    self.canvas_process=MplProcess(pipe_in, pipe_out, width, height, dpi,
                                   sharex, sharey, adjust={})
    self.stay_alive=True
    self.scheduled_actions=[]

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
      self.scheduled_actions=[]
      for item in actions:
        self.pipe_in.send(item)
      for item in actions:
        result=self.pipe_out.recv()
        if item[0]=='getPaintData':
          self.paintFinished.emit(result)
      
class MplBGCanvas(QtGui.QWidget):
  _running_threads=[]

  def __init__(self, parent=None, width=10, height=12, dpi=100., sharex=None, sharey=None, adjust={}):
    QtGui.QWidget.__init__(self, parent)
    self.dpi=dpi
    self.width=width
    self.height=height
    self.draw_process=MplProcessHolder(width, height, dpi, sharex, sharey, adjust)
    self.draw_process.paintFinished.connect(self.paintFinished)
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
    self.draw_process.scheduled_actions.append(('set_size_inches', (winch, hinch), {}))
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
    self.draw_process.scheduled_actions.append(('draw', (), {}))
    self.draw_process.scheduled_actions.append(('getPaintData', (), {}))

  def plot(self, *args, **opts):
    self.draw_process.scheduled_actions.append(('plot', args, opts))
  

class MplCanvas(FigureCanvas):
  def __init__(self, parent=None, width=3, height=3, dpi=100, sharex=None, sharey=None, adjust={}):
    self.fig=Figure(figsize=(width, height), dpi=dpi, facecolor='#FFFFFF')
    self.ax=self.fig.add_subplot(111, sharex=sharex, sharey=sharey)
    self.fig.subplots_adjust(left=0.15, bottom=0.1, right=0.95, top=0.95)
    self.xtitle=""
    self.ytitle=""
    self.PlotTitle=""
    self.grid_status=True
    self.xaxis_style='linear'
    self.yaxis_style='linear'
    self.format_labels()
    self.ax.hold(True)
    FigureCanvas.__init__(self, self.fig)
    #self.fc = FigureCanvas(self.fig)
    FigureCanvas.setSizePolicy(self,
                              QtGui.QSizePolicy.Expanding,
                              QtGui.QSizePolicy.Expanding)
    FigureCanvas.updateGeometry(self)

  def format_labels(self):
    self.ax.set_title(self.PlotTitle)
#    self.ax.title.set_fontsize(10)
#    self.ax.set_xlabel(self.xtitle, fontsize=9)
#    self.ax.set_ylabel(self.ytitle, fontsize=9)
#    labels_x=self.ax.get_xticklabels()
#    labels_y=self.ax.get_yticklabels()
#
#    for xlabel in labels_x:
#      xlabel.set_fontsize(8)
#    for ylabel in labels_y:
#      ylabel.set_fontsize(8)

  def sizeHint(self):
    w, h=self.get_width_height()
    w=max(w, self.height())
    h=max(h, self.width())
    return QtCore.QSize(w, h)

  def minimumSizeHint(self):
    return QtCore.QSize(40, 40)

  def get_default_filetype(self):
      return 'png'

  def draw(self):
    FigureCanvas.draw(self)


class MPLWidget(QtGui.QWidget):
  cplot=None
  cbar=None

  def __init__(self, parent=None, with_toolbar=True, coordinates=False):
    QtGui.QWidget.__init__(self, parent)
    self.canvas=MplCanvas()
    self.canvas.ax2=None
    self.vbox=QtGui.QVBoxLayout()
    self.vbox.setMargin(1)
    self.vbox.addWidget(self.canvas)
    if with_toolbar:
      self.toolbar=NavigationToolbar(self.canvas, self)
      self.toolbar.coordinates=coordinates
      self.vbox.addWidget(self.toolbar)
    else:
      self.toolbar=None
    self.setLayout(self.vbox)

  def leaveEvent(self, event):
    '''
    Make sure the cursor is reset to it's default when leaving the widget.
    In some cases the zoom cursor does not reset when leaving the plot.
    '''
    if self.toolbar:
      QtGui.QApplication.restoreOverrideCursor()
      self.toolbar._lastCursor=None
    return QtGui.QWidget.leaveEvent(self, event)

  def set_config(self, config):
    self.canvas.fig.subplots_adjust(**config)

  def get_config(self):
    spp=self.canvas.fig.subplotpars
    config=dict(left=spp.left,
                right=spp.right,
                bottom=spp.bottom,
                top=spp.top)
    return config


  def draw(self):
    '''
      Convenience to redraw the graph.
    '''
    self.canvas.draw()

  def plot(self, *args, **opts):
    '''
      Convenience wrapper for self.canvas.ax.plot
    '''
    return self.canvas.ax.plot(*args, **opts)

  def semilogy(self, *args, **opts):
    '''
      Convenience wrapper for self.canvas.ax.semilogy
    '''
    return self.canvas.ax.semilogy(*args, **opts)

  def errorbar(self, *args, **opts):
    '''
      Convenience wrapper for self.canvas.ax.semilogy
    '''
    return self.canvas.ax.errorbar(*args, **opts)

  def pcolormesh(self, datax, datay, dataz, log=False, imin=None, imax=None, update=False, **opts):
    '''
      Convenience wrapper for self.canvas.ax.plot
    '''
    if self.cplot is None or not update:
      if log:
        self.cplot=self.canvas.ax.pcolormesh(datax, datay, dataz, norm=LogNorm(imin, imax), **opts)
      else:
        self.cplot=self.canvas.ax.pcolormesh(datax, datay, dataz, **opts)
    else:
      self.update(datax, datay, dataz)
    return self.cplot

  def imshow(self, data, log=False, imin=None, imax=None, update=True, **opts):
    '''
      Convenience wrapper for self.canvas.ax.plot
    '''
    if self.cplot is None or not update:
      if log:
        self.cplot=self.canvas.ax.imshow(data, norm=LogNorm(imin, imax), **opts)
      else:
        self.cplot=self.canvas.ax.imshow(data, **opts)
    else:
      self.update(data, **opts)
    return self.cplot

  def set_title(self, new_title):
    return self.canvas.ax.title.set_text(new_title)

  def set_xlabel(self, label):
    return self.canvas.ax.set_xlabel(label)

  def set_ylabel(self, label):
    return self.canvas.ax.set_ylabel(label)

  def set_xscale(self, scale):
    try:
      return self.canvas.ax.set_xscale(scale)
    except ValueError:
      pass

  def set_yscale(self, scale):
    try:
      return self.canvas.ax.set_yscale(scale)
    except ValueError:
      pass

  def clear_fig(self):
    self.cplot=None
    self.cbar=None
    self.canvas.fig.clear()
    self.canvas.ax=self.canvas.fig.add_subplot(111, sharex=None, sharey=None)

  def clear(self):
    self.cplot=None
    self.toolbar._views.clear()
    self.toolbar._positions.clear()
    self.canvas.ax.clear()
    if self.canvas.ax2 is not None:
      self.canvas.ax2.clear()

  def update(self, *data, **opts):
    self.cplot.set_data(*data)
    if 'extent' in opts:
      self.cplot.set_extent(opts['extent'])
      oldviews=self.toolbar._views
      if self.toolbar._views:
        # set the new extent as home for the new data
        newviews=Stack()
        newviews.push([tuple(opts['extent'])])
        for item in oldviews[1:]:
          newviews.push(item)
        self.toolbar._views=newviews
      if not oldviews or oldviews[oldviews._pos]==oldviews[0]:
        self.canvas.ax.set_xlim(opts['extent'][0], opts['extent'][1])
        self.canvas.ax.set_ylim(opts['extent'][2], opts['extent'][3])

  def legend(self, *args, **opts):
    return self.canvas.ax.legend(*args, **opts)

  def adjust(self, **adjustment):
    return self.canvas.fig.subplots_adjust(**adjustment)

if __name__=='__main__':
  app=QtGui.QApplication([])
  dia=QtGui.QDialog()
  dia.resize(800, 600)
  hbox=QtGui.QHBoxLayout(dia)
  for i in range(4):
    # start 4 processes with plots
    plot=MplBGCanvas(dia)
    hbox.addWidget(plot)
    plot.plot(range(100))
    plot.draw()
  dia.show()
  exit(app.exec_())
