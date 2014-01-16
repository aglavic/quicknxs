#-*- coding: utf-8 -*-
'''
Dialogs connected to the main GUI for separate display of specific plots.
'''


from PyQt4.QtGui import QDialog, QVBoxLayout
from numpy import array, argsort
from .mplwidget import MPLWidget
from .qreduce import NXSData, NXSMultiData, Reflectivity

class ReductionPreviewDialog(QDialog):
  '''
  A simple plot dialog which connects to the ... signal from the main gui to
  plot the reduced reflectivity of all states.
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
        ymax=max(ymax, yj.max())
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
    return QDialog.closeEvent(self, *args, **kwargs)
