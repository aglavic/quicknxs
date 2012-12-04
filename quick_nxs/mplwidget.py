#!/usr/bin/env python
from PyQt4 import QtCore, QtGui
import matplotlib

font={
      #'family' : 'sans',
      #  'weight' : 'normal',
        'size': 6}

matplotlib.rc('font', **font)

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4 import NavigationToolbar2QT as NavigationToolbar
from matplotlib.colors import LogNorm
from matplotlib.figure import Figure

class MplCanvas(FigureCanvas):
  def __init__(self, parent=None, width=10, height=12, dpi=100, sharex=None, sharey=None, adjust={}):
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
    self.ax.title.set_fontsize(10)
    self.ax.set_xlabel(self.xtitle, fontsize=9)
    self.ax.set_ylabel(self.ytitle, fontsize=9)
    labels_x=self.ax.get_xticklabels()
    labels_y=self.ax.get_yticklabels()

    for xlabel in labels_x:
      xlabel.set_fontsize(8)
    for ylabel in labels_y:
      ylabel.set_fontsize(8)
      ylabel.set_color('b')

  def sizeHint(self):
    w, h=self.get_width_height()
    return QtCore.QSize(w, h)

  def minimumSizeHint(self):
    return QtCore.QSize(10, 10)


class MPLWidget(QtGui.QWidget):
  cplot=None
  cbar=None

  def __init__(self, parent=None, with_toolbar=True):
    QtGui.QWidget.__init__(self, parent)
    self.canvas=MplCanvas()
    self.canvas.ax2=None
    self.vbox=QtGui.QVBoxLayout()
    self.vbox.addWidget(self.canvas)
    if with_toolbar:
      self.toolbar=NavigationToolbar(self.canvas, self)
      self.vbox.addWidget(self.toolbar)
    self.setLayout(self.vbox)

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
      self.update(data)
    return self.cplot

  def set_title(self, new_title):
    return self.canvas.ax.title.set_text(new_title)

  def set_xlabel(self, label):
    return self.canvas.ax.set_xlabel(label)

  def set_ylabel(self, label):
    return self.canvas.ax.set_ylabel(label)

  def set_xscale(self, scale):
    return self.canvas.ax.set_xscale(scale)

  def set_yscale(self, scale):
    return self.canvas.ax.set_yscale(scale)

  def clear_fig(self):
    self.cplot=None
    self.cbar=None
    self.canvas.fig.clear()
    self.canvas.ax=self.canvas.fig.add_subplot(111, sharex=None, sharey=None)

  def clear(self):
    self.cplot=None
    self.canvas.ax.clear()
    if self.canvas.ax2 is not None:
      self.canvas.ax2.clear()

  def update(self, *data):
    self.cplot.set_data(*data)

  def legend(self, *args, **opts):
    return self.canvas.ax.legend(*args, **opts)

  def adjust(self, **adjustment):
    return self.canvas.fig.subplots_adjust(**adjustment)
