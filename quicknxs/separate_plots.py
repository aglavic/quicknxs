#-*- coding: utf-8 -*-
'''
Dialogs connected to the main GUI for separate display of specific plots.
'''


from PyQt5.QtWidgets import QDialog, QVBoxLayout
from numpy import array, argsort, arange
from matplotlib.gridspec import GridSpec
from .mplwidget import MPLWidget
from .qreduce import NXSData, NXSMultiData, Reflectivity

class ReductionPreviewDialog(QDialog):
  '''
  A simple plot dialog which connects to the initiateReflectivityPlot signal from the
  main gui to plot the reduced reflectivity of all states.
  '''

  def __init__(self, parent, *args, **opts):
    QDialog.__init__(self, parent, *args, **opts)
    self.setWindowTitle('Reflectivity Reduction Preview')
    self.vbox=QVBoxLayout(self)
    self.plot=MPLWidget(self, True)
    self.vbox.addWidget(self.plot)

    self.parent_window=parent
    parent.initiateReflectivityPlot.connect(self.plot_preview)
    self.plot_preview()

  def plot_preview(self):
    parent=self.parent_window
    self.plot.clear()
    channels=parent.ref_list_channels
    achannel=parent.active_channel
    if len(parent.reduction_list)==0:
      self.plot.draw()
      return

    ymin=1e10
    ymax=0.
    Q=[[] for _c in channels]
    y=[[] for _c in channels]
    dy=[[] for _c in channels]
    for refli in parent.reduction_list:
      P0i=len(refli.Q)-refli.options['P0']
      PNi=refli.options['PN']
      # reload dataset to get all states
      if type(refli.origin) is list:
        filenames=[origin[0] for origin in refli.origin]
        data=NXSMultiData(filenames, **refli.read_options)
      else:
        filename, _channel=refli.origin
        data=NXSData(filename, **refli.read_options)
      # get reflecitivy data for all states
      for j, c in enumerate(channels):
        if c==achannel:
          reflj=refli
        else:
          reflj=Reflectivity(data[j], **refli.options)
        Qj=reflj.Q[PNi:P0i]
        yj=reflj.R[PNi:P0i]
        dyj=reflj.dR[PNi:P0i]
        try:
          ymin=min(ymin, yj[yj>0].min())
        except ValueError:
          pass
        try:
          ymax=max(ymax, yj.max())
        except ValueError:
          pass
        Q[j]+=Qj.tolist()
        y[j]+=yj.tolist()
        dy[j]+=dyj.tolist()

    for j, c in enumerate(channels):
      # sort and plot points
      Qj, yj, dyj=array(Q[j]), array(y[j]), array(dy[j])
      srt=argsort(Qj)
      Qj, yj, dyj=Qj[srt], yj[srt], dyj[srt]
      self.plot.errorbar(Qj, yj, yerr=dyj, label=c, color=parent._refl_color_list[j])

    self.plot.legend()
    self.plot.set_yscale('log')
    self.plot.set_ylabel(u'I')
    self.plot.canvas.ax.set_ylim((ymin*0.9, ymax*1.1))
    self.plot.set_xlabel(u'Q$_z$ [Å$^{-1}$]')

    self.plot.draw()

  def closeEvent(self, *args, **kwargs):
    self.parent_window.initiateReflectivityPlot.disconnect(self.plot_preview)
    self.close()
    #return QDialog.closeEvent(self, *args, **kwargs)

class ProjectionPlotDialog(QDialog):
  '''
  Dialog to show a map graph together with projections on it's x and y axes.
  '''
  xline=None
  yline=None

  def __init__(self, parent, *args, **opts):
    QDialog.__init__(self, parent, *args, **opts)
    self.setWindowTitle('Projection Plot')
    self.vbox=QVBoxLayout(self)
    self.plot=MPLWidget(self, True)
    self.vbox.addWidget(self.plot)

    self.parent_window=parent
    self.create_axes()
    for action in self.plot.toolbar.actions():
      if str(action.iconText())=='Log':
        action.triggered.connect(self.toggle_log)

  def create_axes(self):
    '''
    Create all subplots with a large area for the color map and left and below it
    two smaller plots for the projections. The plot axes tough each other and
    are connected, so that zooming in one plot does the same in the other.
    '''
    plot=self.plot
    plot.cplot=None
    plot.cbar=None
    plot.canvas.fig.clear()
    gs=GridSpec(4,4, wspace=0., hspace=0.)
    fig=plot.canvas.fig
    plot.canvas.ax=fig.add_subplot(gs[:3, 1:])
    self.ax_map=plot.canvas.ax
    self.ax_y=fig.add_subplot(gs[:3, 0], sharey=self.ax_map)
    self.ax_x=fig.add_subplot(gs[3, 1:], sharex=self.ax_map)
    # make sure lables are on the right side of each subplot
    self.ax_map.xaxis.tick_top()
    self.ax_map.yaxis.tick_right()
    self.ax_y.xaxis.tick_top()
  
  def draw(self):
    self.plot.draw()

  def imshow(self, data, log=False, imin=None, imax=None, update=True, **opts):
    '''
    Draw a colormap of the given dataset and create projections on x and y axes.
    '''
    self.plot.imshow(data, log, imin, imax, update, **opts)
    if update and self.xline is not None:
      self.xline.set_data(arange(data.shape[1]), data.sum(axis=0))
      self.yline.set_data(data.sum(axis=1), arange(data.shape[0]))
    else:
      self.xline=self.ax_x.plot(arange(data.shape[1]), data.sum(axis=0))[0]
      self.yline=self.ax_y.plot(data.sum(axis=1), arange(data.shape[0]))[0]
    if log:
      self.ax_x.set_yscale('log')
      self.ax_y.set_xscale('log')
 
  def toggle_log(self, *args):
    '''
    Toggle the logarithmic axes of the projection plots.
    '''
    logstate=self.ax_x.get_yscale()
    if logstate=='linear':
      self.ax_x.set_yscale('log')
      self.ax_y.set_xscale('log')
    else:
      self.ax_x.set_yscale('linear')
      self.ax_y.set_xscale('linear')
    self.draw()
