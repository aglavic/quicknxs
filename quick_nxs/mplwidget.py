#!/usr/bin/env python
import os
import subprocess
import tempfile
from PyQt4 import QtCore, QtGui
import matplotlib.cm
import matplotlib.colors

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
matplotlib.rc('font', **font)
matplotlib.rc('savefig', **savefig)
cmap=matplotlib.colors.LinearSegmentedColormap.from_list('default',
                  ['#0000ff', '#00ff00', '#ffff00', '#ff0000', '#ff00ff', '#000000'], N=256)
matplotlib.cm.register_cmap('default', cmap=cmap)

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4 import NavigationToolbar2QT
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
  def _init_toolbar(self):
    self.basedir=os.path.join(matplotlib.rcParams[ 'datapath' ], 'images')

    a=self.addAction(self._icon('home.png'), 'Home', self.home)
    a.setToolTip('Reset original view')
    a=self.addAction(self._icon('back.png'), 'Back', self.back)
    a.setToolTip('Back to previous view')
    a=self.addAction(self._icon('forward.png'), 'Forward', self.forward)
    a.setToolTip('Forward to next view')
    self.addSeparator()
    a=self.addAction(self._icon('move.png'), 'Pan', self.pan)
    a.setToolTip('Pan axes with left mouse, zoom with right')
    a=self.addAction(self._icon('zoom_to_rect.png'), 'Zoom', self.zoom)
    a.setToolTip('Zoom to rectangle')
    self.addSeparator()
    a=self.addAction(self._icon('subplots.png'), 'Subplots',
            self.configure_subplots)
    a.setToolTip('Configure plot boundaries')

    a=self.addAction(QtGui.QIcon.fromTheme('document-save',
                     self._icon('filesave.png')), 'Save',
            self.save_figure)
    a.setToolTip('Save the figure')

    a=self.addAction(QtGui.QIcon.fromTheme('document-print'), 'Print',
            self.print_figure)
    a.setToolTip('Print the figure with the default printer')

    self.addSeparator()
    a=self.addAction(QtGui.QIcon.fromTheme('go-up'), 'Log',
            self.toggle_log)
    a.setToolTip('Toggle logarithmic scale')


    self.buttons={}

    # Add the x,y location widget at the right side of the toolbar
    # The stretch factor is 1 which means any resizing of the toolbar
    # will resize this label instead of the buttons.
    if self.coordinates:
        self.locLabel=QtGui.QLabel("", self)
        self.locLabel.setAlignment(
                QtCore.Qt.AlignRight|QtCore.Qt.AlignTop)
        self.locLabel.setSizePolicy(
            QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding,
                              QtGui.QSizePolicy.Ignored))
        labelAction=self.addWidget(self.locLabel)
        labelAction.setVisible(True)

    # reference holder for subplots_adjust window
    self.adj_window=None

  def print_figure(self):
    '''
      Save the plot to a temporary pdf file and print it using the
      unix lpr command.
    '''
    filetypes=self.canvas.get_supported_filetypes_grouped()
    sorted_filetypes=filetypes.items()
    sorted_filetypes.sort()

    filename=os.path.join(tempfile.gettempdir(), u"quicknxs_print.pdf")
    self.canvas.print_figure(filename, dpi=600)
    # print to default printer
    proc=subprocess.Popen([u"lpr", u"-T", u"QuickNXS Plot", u'-o', u'landscape', u'-o', u'media=Letter', filename],
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    result=proc.communicate()[0]
    if proc.returncode:
      QtGui.QMessageBox.warning(self, 'Plot Error',
                                'Plot could not be printed, output of print command:\n\n%s'%result,
                                buttons=QtGui.QMessageBox.Close)
    else:
      QtGui.QMessageBox.information(self, 'Plot Printed',
                                    'Plot successfully send to default printer!',
                                    buttons=QtGui.QMessageBox.Close)

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
    if len(ax.lines)>0:
      logstate=ax.get_yscale()
      if logstate=='linear':
        ax.set_yscale('log')
      else:
        ax.set_yscale('linear')
      self.canvas.draw()
    else:
      img=ax.images[0]
      norm=img.norm
      if norm.__class__ is LogNorm:
        img.set_norm(Normalize(norm.vmin, norm.vmax))
      else:
        img.set_norm(LogNorm(norm.vmin, norm.vmax))
    self.canvas.draw()

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


class MPLWidget(QtGui.QWidget):
  cplot=None
  cbar=None

  def __init__(self, parent=None, with_toolbar=True, coordinates=False):
    QtGui.QWidget.__init__(self, parent)
    self.canvas=MplCanvas()
    self.canvas.ax2=None
    self.vbox=QtGui.QVBoxLayout()
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
      self.update(data)
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
    self.canvas.ax.clear()
    if self.canvas.ax2 is not None:
      self.canvas.ax2.clear()

  def update(self, *data):
    self.cplot.set_data(*data)

  def legend(self, *args, **opts):
    return self.canvas.ax.legend(*args, **opts)

  def adjust(self, **adjustment):
    return self.canvas.fig.subplots_adjust(**adjustment)
