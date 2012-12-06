#-*- coding: utf-8 -*-
'''
  Actions performed for main window signals.
'''

import os
from glob import glob
#from time import sleep
from numpy import where, pi, newaxis, isnan, maximum, arange, exp, log10
from scipy.stats.mstats import mquantiles
from cPickle import load, dump
from matplotlib.lines import Line2D
from PyQt4 import QtGui, QtCore
from . import data_reduction
from .main_window import Ui_MainWindow
from .plot_dialog import Ui_Dialog as UiPlot
from .gui_utils import ReduceDialog, DelayedTrigger
from .instrument_constants import *
from .mpfit import mpfit

class MainGUI(QtGui.QMainWindow):
  active_folder=u'.'
  active_file=u''
  ref_list_channels=[]
  ref_data=None
  ref_norm=None
  auto_change_active=False
  add_to_ref=[]
  color=None
  open_plots=[] # to keep non modal dialogs open

  def __init__(self, argv=[]):
    QtGui.QMainWindow.__init__(self)
    self.auto_change_active=True
    self.ui=Ui_MainWindow()
    self.ui.setupUi(self)
    self.toggleHide()
    self.readSettings()
    # start a separate thread for delayed actions
    self.trigger=DelayedTrigger()
    self.connect(self.trigger, QtCore.SIGNAL("activate(QString, PyQt_PyObject)"),
                 self.processDelayedTrigger)
    self.trigger.start()

    self._path_watcher=QtCore.QFileSystemWatcher(self.active_folder, self)
    if len(argv)>0:
      self.fileOpen(argv[0])
    self.connect_plot_events()
    self._path_watcher.directoryChanged.connect(self.folderModified)
    self.auto_change_active=False

  def processDelayedTrigger(self, item, args):
    '''
      Calls private method after delay action was
      triggered.
    '''
    getattr(self, str(item))(*args)

  def connect_plot_events(self):
    '''
      Connect matplotlib mouse events.
    '''
    for plot in [self.ui.xy_pp, self.ui.xy_mp, self.ui.xy_pm, self.ui.xy_mm,
           self.ui.xtof_pp, self.ui.xtof_mp, self.ui.xtof_pm, self.ui.xtof_mm,
           self.ui.xy_overview, self.ui.xtof_overview,
           self.ui.x_project, self.ui.y_project, self.ui.refl]:
      plot.canvas.mpl_connect('motion_notify_event', self.plotMouseEvent)
    self.ui.x_project.canvas.mpl_connect('motion_notify_event', self.plotPickX)
    self.ui.x_project.canvas.mpl_connect('button_release_event', self.plotPickX)
    self.ui.y_project.canvas.mpl_connect('motion_notify_event', self.plotPickY)
    self.ui.y_project.canvas.mpl_connect('button_release_event', self.plotPickY)

  def fileOpenDialog(self):
    '''
      Show a dialog to open a new file.
    '''
    filename=QtGui.QFileDialog.getOpenFileName(self, u'Open NXS file...',
                                               directory=self.active_folder,
                                               filter=u'Histo Nexus (*histo.nxs);;All (*.*)')
    if filename!=u'':
      self.fileOpen(unicode(filename))

  def fileOpenList(self):
    '''
      Called when a new file is selected from the file list.
    '''
    item=self.ui.file_list.currentItem()
    name=unicode(item.text())
    mtime=os.path.getmtime(os.path.join(self.active_folder, self.active_file))
    if name!=self.active_file or mtime>self.last_mtime:
      # only reload if filename was actually changed or file was modifiede
      self.fileOpen(os.path.join(self.active_folder, name))

  def nextFile(self):
    item=self.ui.file_list.currentRow()
    self.ui.file_list.setCurrentRow(item+1)

  def prevFile(self):
    item=self.ui.file_list.currentRow()
    self.ui.file_list.setCurrentRow(item-1)

  def fileOpen(self, filename):
    '''
      Open a new datafile and plot the data.
    '''
    folder, base=os.path.split(filename)
    data=data_reduction.read_file(filename)
    if data is None:
      self.ui.currentChannel.setText(u'!!!NO DATA IN FILE %s!!!'%base)
      return
    if folder!=self.active_folder:
      self.onPathChanged(base, folder)
    self.active_file=base
    self.channels=data['channels']
    self.xydata=data['xydata']
    self.xtofdata=data['xtofdata']

    desiredChannel=self.ui.selectedChannel.currentText().split('/')
    self.use_channel=data['channels'][0]
    for channel in self.channels:
      if channel in desiredChannel:
        self.use_channel=channel
        break
    self.fulldata=data[self.use_channel]
    self.updateLabels()
    self.calcReflParams()
    self.plotActiveTab()
    self.plot_projections()
    self.last_mtime=os.path.getmtime(filename)
    self.ui.statusbar.showMessage(u"%s loaded"%(filename), 1500)

  def onPathChanged(self, base, folder):
    '''
      Update the file list and create a watcher to update the list again if a new file was
      created.
    '''
    self._path_watcher.removePath(self.active_folder)
    self.active_folder=folder
    self.updateFileList(base, folder)
    self._path_watcher.addPath(self.active_folder)

  def plotActiveTab(self):
    '''
      Select the appropriate function to plot all visible images.
    '''
    color=str(self.ui.color_selector.currentText())
    if color!=self.color and self.color is not None:
      self.color=color
      plots=[self.ui.xy_pp, self.ui.xy_mp, self.ui.xy_pm, self.ui.xy_mm,
             self.ui.xtof_pp, self.ui.xtof_mp, self.ui.xtof_pm, self.ui.xtof_mm,
             self.ui.xy_overview, self.ui.xtof_overview]
      for plot in plots:
        plot.clear_fig()
    elif self.color is None:
      self.color=color
    if self.ui.plotTab.currentIndex()==0:
      self.plot_overview()
    if self.ui.plotTab.currentIndex()==1:
      self.plot_xy()
    if self.ui.plotTab.currentIndex()==2:
      self.plot_xtof()
    if self.ui.plotTab.currentIndex()==3:
      self.plot_offspec()

  def folderModified(self, flist):
    '''
      Called by the path watcher to update the file list when the folder
      has been modified.
    '''
    self.updateFileList(self.active_file, self.active_folder)

  def updateFileList(self, base, folder):
    '''
      Create a new filelist if the folder has changes.
    '''
    newlist=glob(os.path.join(folder, '*histo.nxs'))
    newlist.sort()
    newlist=map(lambda name: os.path.basename(name), newlist)
    self.ui.file_list.clear()
    for item in newlist:
      listitem=QtGui.QListWidgetItem(item, self.ui.file_list)
      if item==base:
        self.ui.file_list.setCurrentItem(listitem)

  def toggleColorbars(self):
    if not self.auto_change_active:
      plots=[self.ui.xy_pp, self.ui.xy_mp, self.ui.xy_pm, self.ui.xy_mm,
             self.ui.xtof_pp, self.ui.xtof_mp, self.ui.xtof_pm, self.ui.xtof_mm,
             self.ui.xy_overview, self.ui.xtof_overview]
      for plot in plots:
        plot.clear_fig()
      self.plotActiveTab()

  def toggleHide(self):
    plots=[self.ui.frame_xy_mm, self.ui.frame_xy_sf, self.ui.frame_xtof_mm, self.ui.frame_xtof_sf]
    if self.ui.hide_plots.isChecked():
      for plot in plots:
        plot.do_hide=True
    else:
      for plot in plots:
        plot.show()
        plot.do_hide=False

#  tline=None
  def plot_overview(self):
    '''
      X vs. Y and X vs. Tof for main channel.
    '''
    cindex=self.channels.index(self.use_channel)
    xy=self.xydata[cindex]
    xtof=self.xtofdata[cindex]
    if self.ui.normalizeXTof.isChecked() and self.ref_norm is not None:
      # normalize ToF dataset for wavelength distribution
      xtof=xtof.astype(float)/self.ref_norm[newaxis, :]
      xtof[isnan(xtof)]=0.
    xy_imin=xy[xy>0].min()
    xy_imax=xy.max()
    tof_imin=xtof[xtof>0].min()
    tof_imax=xtof.max()
    self.ui.xy_overview.imshow(xy, log=True, aspect='auto', cmap=self.color)
    self.ui.xtof_overview.imshow(xtof, log=True, aspect='auto', cmap=self.color)
    self.ui.xy_overview.set_xlabel(u'x [pix]')
    self.ui.xy_overview.set_ylabel(u'y [pix]')
    self.ui.xy_overview.cplot.set_clim([xy_imin, xy_imax])
    self.ui.xtof_overview.set_xlabel(u'ToF [channel]')
    self.ui.xtof_overview.set_ylabel(u'x [pix]')
    self.ui.xtof_overview.cplot.set_clim([tof_imin, tof_imax])
#    if self.tline is None:
#      self.tline=Line2D([20, 20], [0, 300], color='red')
#      self.ui.xy_overview.canvas.ax.add_line(self.tline)
    if self.ui.show_colorbars.isChecked() and self.ui.xy_overview.cbar is None:
      self.ui.xy_overview.cbar=self.ui.xy_overview.canvas.fig.colorbar(self.ui.xy_overview.cplot)
      self.ui.xtof_overview.cbar=self.ui.xtof_overview.canvas.fig.colorbar(self.ui.xtof_overview.cplot)
    self.ui.xy_overview.draw()
    self.ui.xtof_overview.draw()

  def plot_xy(self):
    '''
      X vs. Y plots for all channels.
    '''
    data=self.xydata
    plots=[self.ui.xy_pp, self.ui.xy_mm, self.ui.xy_mp, self.ui.xy_pm]
    imin=1e20
    imax=1e-20
    for d in data:
      imin=min(imin, d[d>0].min())
      imax=max(imax, d.max())

    if len(data)>1:
      self.ui.frame_xy_mm.show()
      if len(data)==4:
        self.ui.frame_xy_sf.show()
      else:
        self.ui.frame_xy_sf.hide()
    else:
      self.ui.frame_xy_mm.hide()
      self.ui.frame_xy_sf.hide()

    for i, datai in enumerate(data):
      plots[i].imshow(datai, log=True, imin=imin, imax=imax,
                           aspect='auto', cmap=self.color)
      plots[i].set_title(self.channels[i])
      plots[i].set_xlabel(u'x [pix]')
      plots[i].set_ylabel(u'y [pix]')
      if plots[i].cplot is not None:
        plots[i].cplot.set_clim([imin, imax])
      if plots[i].cplot is not None and self.ui.show_colorbars.isChecked() and plots[i].cbar is None:
        plots[i].cbar=plots[i].canvas.fig.colorbar(plots[i].cplot)
      plots[i].draw()

  def plot_xtof(self):
    '''
      X vs. ToF plots for all channels.
    '''
    data=self.xtofdata
    plots=[self.ui.xtof_pp, self.ui.xtof_mm, self.ui.xtof_mp, self.ui.xtof_pm]
    if self.ui.normalizeXTof.isChecked() and self.ref_norm is not None:
      # normalize all datasets for wavelength distribution
      data_new=[]
      for ds in data:
        data_new.append(ds.astype(float)/self.ref_norm[newaxis, :])
        data_new[-1][isnan(data_new[-1])]=0.
      data=data_new
    imin=1e20
    imax=1e-20
    for d in data:
      imin=min(imin, d[d>0].min())
      imax=max(imax, d.max())
    if len(data)>1:
      self.ui.frame_xtof_mm.show()
      if len(data)==4:
        self.ui.frame_xtof_sf.show()
      else:
        self.ui.frame_xtof_sf.hide()
    else:
      self.ui.frame_xtof_mm.hide()
      self.ui.frame_xtof_sf.hide()
    for i, datai in enumerate(data):
      plots[i].imshow(datai, log=True, imin=imin, imax=imax,
                           aspect='auto', cmap=self.color)
      plots[i].set_title(self.channels[i])
      plots[i].set_xlabel(u'ToF [Channel]')
      plots[i].set_ylabel(u'x [pix]')
      if plots[i].cplot is not None:
        plots[i].cplot.set_clim([imin, imax])
      if plots[i].cplot is not None and self.ui.show_colorbars.isChecked() and plots[i].cbar is None:
        plots[i].cbar=plots[i].canvas.fig.colorbar(plots[i].cplot)
      plots[i].draw()

  def updateLabels(self):
    d=self.fulldata

    try:
      tth=(d['dangle']-float(self.ui.dangle0Overwrite.text()))
    except ValueError:
      tth=d['tth']
    self.ui.datasetName.setText(self.active_file)
    self.ui.datasetPCharge.setText(u"%.3e"%d['pc'])
    self.ui.datasetTotCounts.setText(u"%.4e"%d['counts'])
    self.ui.datasetDangle.setText(u"%.3f"%d['dangle'])
    self.ui.datasetTth.setText(u"%.3f"%tth)
    self.ui.datasetSangle.setText(u"%.3f"%d['ai'])
    self.ui.datasetDirectPixel.setText(u"%.1f"%d['dp'])
    self.ui.currentChannel.setText('Current Channel:   (%s)'%self.use_channel)

  def calcReflParams(self):
    '''
      Calculate x and y regions for reflectivity extraction and put them in the
      entry fields.
    '''
    cindex=self.channels.index(self.use_channel)
    data=self.xydata[cindex]
    if self.ui.xprojUseQuantiles.isChecked():
      d2=self.xtofdata[cindex]
      xproj=mquantiles(d2, self.ui.xprojQuantiles.value()/100., axis=1).flatten()
    else:
      xproj=data.mean(axis=0)
    yproj=data.mean(axis=1)

    # calculate approximate peak position
    try:
      tth_bank=(self.fulldata['dangle']-float(self.ui.dangle0Overwrite.text()))*pi/180.
    except ValueError:
      tth_bank=self.fulldata['tth']*pi/180.
    ai=self.fulldata['ai']*pi/180.
    if self.ui.directPixelOverwrite.value()>=0:
      dp=self.ui.directPixelOverwrite.value()
    else:
      dp=self.fulldata['dp']
    pix_position=dp-(ai*2-tth_bank)/RAD_PER_PIX

    # find the first peak which is above 10% of the maximum
    x_peaks=where((xproj[3:-1]<=xproj[2:-2])&(xproj[1:-3]<=xproj[2:-2])
                 &(xproj[4:]<=xproj[2:-2])&(xproj[:-4]<=xproj[2:-2])
                 &(xproj[2:-2]>=xproj.max()/10.))[0]+2
    delta_pix=abs(pix_position-x_peaks)
    x_peak=x_peaks[delta_pix==delta_pix.min()][0]
    # refine gaussian to this peak position
    x_width=self.ui.refXWidth.value()
    x_peak=self.refineGauss(xproj, x_peak, x_width)

    # find the central peak reagion with intensities larger than 10% of maximum
    y_bg=mquantiles(yproj, 0.5)[0]
    self.y_bg=y_bg
    y_peak_region=where((yproj-y_bg)>yproj.max()/10.)[0]
    yregion=(y_peak_region[0], y_peak_region[-1])
    self.auto_change_active=True
    self.ui.refXPos.setValue(x_peak)
    self.ui.refYPos.setValue((yregion[0]+yregion[1]+1.)/2.)
    self.ui.refYWidth.setValue(yregion[1]+1-yregion[0])
    self.ui.bgCenter.setValue((DETECTOR_X_REGION[0]+100.)/2.)
    self.ui.bgWidth.setValue((100-DETECTOR_X_REGION[0]))
    self.auto_change_active=False

  def refineGauss(self, data, pos, width):
    p0=[data[int(pos)], pos, width]
    res=mpfit(self.gauss_residuals, p0, functkw={'data':data}, nprint=0)
    #print pos, res.params[1], res.niter
    return res.params[1]

  def gauss_residuals(self, p, fjac=None, data=None, width=1):
    xdata=arange(data.shape[0])
    I0=p[0]
    x0=p[1]
    sigma=p[2]/5.
    G=exp(-0.5*((xdata-x0)/sigma)**2)
    return 0, data-I0*G

  def changeRegionValues(self):
    if self.auto_change_active:
      return
    lines=self.proj_lines
    x_peak=self.ui.refXPos.value()
    x_width=self.ui.refXWidth.value()
    y_pos=self.ui.refYPos.value()
    y_width=self.ui.refYWidth.value()
    bg_pos=self.ui.bgCenter.value()
    bg_width=self.ui.bgWidth.value()

    lines[0].set_xdata([x_peak-x_width/2., x_peak-x_width/2.])
    lines[1].set_xdata([x_peak, x_peak])
    lines[2].set_xdata([x_peak+x_width/2., x_peak+x_width/2.])
    lines[3].set_xdata([bg_pos-bg_width/2., bg_pos-bg_width/2.])
    lines[4].set_xdata([bg_pos+bg_width/2., bg_pos+bg_width/2.])
    lines[5].set_xdata([y_pos-y_width/2., y_pos-y_width/2.])
    lines[6].set_xdata([y_pos+y_width/2., y_pos+y_width/2.])
    self.ui.x_project.draw()
    self.ui.y_project.draw()
    self.trigger('plot_refl')

  def replotProjections(self):
    self.plot_projections(preserve_lim=True)

  def plot_projections(self, preserve_lim=False):
    self.trigger('_plot_projections', preserve_lim)

  def _plot_projections(self, preserve_lim):
    '''
      Create projections of the data on the x and y axes.
      The x-projection can also be done be means of quantile calculation,
      which means that the ToF intensities are calculation which are
      exceeded by a certain number of points. This can be helpful to better
      separate the specular reflection from bragg-sheets
    '''
    cindex=self.channels.index(self.use_channel)
    data=self.xydata[cindex]
    if self.ui.xprojUseQuantiles.isChecked():
      d2=self.xtofdata[cindex]
      xproj=mquantiles(d2, self.ui.xprojQuantiles.value()/100., axis=1)
    else:
      xproj=data.mean(axis=0)
    yproj=data.mean(axis=1)

    x_peak=self.ui.refXPos.value()
    x_width=self.ui.refXWidth.value()
    y_pos=self.ui.refYPos.value()
    y_width=self.ui.refYWidth.value()
    bg_pos=self.ui.bgCenter.value()
    bg_width=self.ui.bgWidth.value()

    if preserve_lim:
      xview=self.ui.x_project.canvas.ax.axis()
      yview=self.ui.y_project.canvas.ax.axis()
    xxlim=(0, len(xproj)-1)
    xylim=(xproj[xproj>0].min(), xproj.max()*2)
    yxlim=(0, len(yproj)-1)
    yylim=(yproj[yproj>0].min(), yproj.max()*2)
    self.ui.x_project.clear()
    self.ui.y_project.clear()

    self.ui.x_project.semilogy(xproj, color='blue')[0]
    self.ui.x_project.set_xlabel(u'x [pix]')
    self.ui.x_project.set_ylabel(u'I$_{max}$')
    self.ui.x_project.canvas.ax.set_xlim(xxlim)
    self.ui.x_project.canvas.ax.set_ylim(xylim)
    xpos=Line2D([x_peak, x_peak], [xylim[0], xylim[1]], color='black')
    xleft=Line2D([x_peak-x_width/2., x_peak-x_width/2.], [xylim[0], xylim[1]], color='red')
    xright=Line2D([x_peak+x_width/2., x_peak+x_width/2.], [xylim[0], xylim[1]], color='red')
    self.ui.x_project.canvas.ax.add_line(xpos)
    self.ui.x_project.canvas.ax.add_line(xleft)
    self.ui.x_project.canvas.ax.add_line(xright)
    xleft_bg=Line2D([bg_pos-bg_width/2., bg_pos-bg_width/2.], [xylim[0], xylim[1]], color='green')
    xright_bg=Line2D([bg_pos+bg_width/2., bg_pos+bg_width/2.], [xylim[0], xylim[1]], color='green')
    self.ui.x_project.canvas.ax.add_line(xleft_bg)
    self.ui.x_project.canvas.ax.add_line(xright_bg)

    self.ui.y_project.semilogy(yproj, color='blue')[0]
    self.ui.y_project.set_xlabel(u'y [pix]')
    self.ui.y_project.set_ylabel(u'I$_{max}$')
    self.ui.y_project.canvas.ax.set_xlim(yxlim)
    self.ui.y_project.canvas.ax.set_ylim(yylim)
    yreg_left=Line2D([y_pos-y_width/2., y_pos-y_width/2.], [yylim[0], yylim[1]], color='red')
    yreg_right=Line2D([y_pos+y_width/2., y_pos+y_width/2.], [yylim[0], yylim[1]], color='red')
    self.ui.y_project.canvas.ax.add_line(yreg_left)
    self.ui.y_project.canvas.ax.add_line(yreg_right)
    y_bg=Line2D([0, yxlim[1]], [self.y_bg, self.y_bg], color='green')
    self.ui.y_project.canvas.ax.add_line(y_bg)
    if preserve_lim:
      self.ui.x_project.canvas.ax.axis(xview)
      self.ui.y_project.canvas.ax.axis(yview)
    self.ui.x_project.draw()
    self.ui.y_project.draw()
    self.proj_lines=(xleft, xpos, xright, xleft_bg, xright_bg, yreg_left, yreg_right)
    self.plot_refl()

  def plot_refl(self, preserve_lim=False):
    '''
      Calculate and display the reflectivity from the current dataset
      and any dataset stored. Intensities from direct beam
      measurements can be used for normalization.
    '''
    data=self.fulldata['data']
    tof_edges=self.fulldata['tof']
    if self.ui.directPixelOverwrite.value()>=0:
      dp=self.ui.directPixelOverwrite.value()
    else:
      dp=self.fulldata['dp']
    try:
      tth=(self.fulldata['dangle']-float(self.ui.dangle0Overwrite.text()))*pi/180.
    except ValueError:
      tth=self.fulldata['tth']*pi/180.
    settings=dict(
                x_pos=self.ui.refXPos.value(),
                x_width=self.ui.refXWidth.value(),
                y_pos=self.ui.refYPos.value(),
                y_width=self.ui.refYWidth.value(),
                bg_pos=self.ui.bgCenter.value(),
                bg_width=self.ui.bgWidth.value(),
                dp=dp,
                tth=tth,
                scale=10**self.ui.refScale.value(),
                beam_width=self.fulldata['beam_width'],
                  )

    P0=31-self.ui.rangeStart.value()
    PN=30-self.ui.rangeEnd.value()
    if self.ui.fanReflectivity.isChecked():
      if self.ref_norm is None:
        QtGui.QMessageBox.information(self, 'No normalization',
                 'You need an active normalization to extract Fan-Reflectivity')
        self.ui.fanReflectivity.setChecked(False)
        return
      Qz, R, dR, ai, I, BG, Iraw=data_reduction.calc_fan_reflectivity(data, tof_edges, settings,
                                                                      self.ref_norm, P0, PN)
    else:
      Qz, R, dR, ai, I, BG, Iraw=data_reduction.calc_reflectivity(data, tof_edges, settings)
    self.ui.datasetAi.setText("%.3f"%(ai*180./pi))
    self.ui.datasetROI.setText("%.4g"%(Iraw.sum()))

    self.ref_x=Qz

    self.ref_data=R/self.fulldata['pc'] # normalize to proton charge
    self.dref=dR/self.fulldata['pc'] # normalize to proton charge

    if preserve_lim:
      view=self.ui.refl.canvas.ax.axis()

    self.ui.refl.clear()
    try:
      index=self.active_file.split('REF_M_', 1)[1].split('_', 1)[0]
    except:
      index='0'
    if self.ref_norm is not None:
      self.ui.refl.set_yscale('log')
      for settings, x, y, dy in self.add_to_ref:
        #self.ui.refl.semilogy(x, y/self.ref_norm, label=str(settings['index']))
        P0i=31-settings['range'][0]
        PNi=30-settings['range'][1]
        self.ui.refl.errorbar(x[PNi:P0i], (y/self.ref_norm)[PNi:P0i],
                              yerr=dy[PNi:P0i], label=str(settings['index']))
      #self.ui.refl.semilogy(self.ref_x, self.ref_data/self.ref_norm, label=index)
      self.ui.refl.errorbar(self.ref_x[PN:P0], (self.ref_data/self.ref_norm)[PN:P0],
                            yerr=(self.dref/self.ref_norm)[PN:P0], label=index)
      self.ui.refl.set_ylabel(u'I$_{Norm}$')
    else:
      self.ui.refl.semilogy(self.ref_x, I, label='I-'+index)
      self.ui.refl.semilogy(self.ref_x, BG, label='BG-'+index)
      self.ui.refl.set_ylabel(u'I$_{Raw}$')
    if ai>0.001:
      self.ui.refl.set_xlabel(u'Q$_z$ [$\\AA^{-1}$]')
    else:
      self.ui.refl.set_xlabel(u'1/$\\lambda$ [$\\AA^{-1}$]')
    self.ui.refl.legend()
    if preserve_lim:
      self.ui.refl.canvas.ax.axis(view)
    self.ui.refl.draw()

  def plot_offspec(self):
    if self.ref_norm is None:
      return
    self.ui.offspec.clear()
    for item in self.add_to_ref:
      fname=os.path.join(item[0]['path'], item[0]['file'])
      data=data_reduction.read_file(fname)
      selected_data=data[data['channels'][0]]
      data=selected_data['data']
      tof_edges=selected_data['tof']
      settings=item[0]
      _Qx, Qz, ki_z, kf_z, I=data_reduction.calc_offspec(data, tof_edges, settings)
      I/=self.ref_norm[newaxis, :]*selected_data['pc']
      self.ui.offspec.pcolormesh(ki_z-kf_z, Qz, I, log=True)
#      self.ui.offspec.pcolormesh(ki_z, kf_z, I, log=True)
    self.ui.offspec.draw()


  def setNorm(self):
    if self.ref_data is None:
      return
    if self.ref_norm is None:
      self.ref_norm=maximum(self.ref_data, self.ref_data[self.ref_data>0].min())
      # collect current settings
      try:
        index=int(self.active_file.split('REF_M_', 1)[1].split('_', 1)[0])
      except:
        index=0
      self.ref_norm_settings={'file': self.active_file,
                              'path': self.active_folder,
                              'index': index,

                              'x_pos': self.ui.refXPos.value(),
                              'x_width': self.ui.refXWidth.value(),
                              'y_pos': self.ui.refYPos.value(),
                              'y_width': self.ui.refYWidth.value(),
                              'bg_pos': self.ui.bgCenter.value(),
                              'bg_width': self.ui.bgWidth.value(),
                              'scale': 10**self.ui.refScale.value(),
                              }
      self.ui.normalizationLabel.setText(self.active_file)
    else:
      self.ref_norm=None
      self.ui.normalizationLabel.setText('None')
    self.plot_refl()

  def normalizeTotalReflection(self):
    '''
      Extract the scaling factor from the reflectivity curve.
    '''
    if self.ref_x.min()>0.02 or self.ref_norm is None:
      QtGui.QMessageBox.information(self, 'Select other dataset',
            'Please select a dataset with total reflection plateau\nand normalization.')
      return
    first=31-self.ui.rangeStart.value()
    y=self.ref_data[:first]/self.ref_norm[:first]
    x=self.ref_x[:first][y>0]
    dy=self.dref[:first][y>0]/self.ref_norm[:first][y>0]
    y=y[y>0]
    # Start from low Q and search for the critical edge
    for i in range(len(y)-5, 0,-1):
      wmean=(y[i:]/dy[i:]).sum()/(1./dy[i:]).sum()
      yi=y[i-1]
      if yi<wmean*0.9:
        break
    self.ui.refScale.setValue(self.ui.refScale.value()+log10(1./wmean)) #change the scaling factor
    # show a line in the plot corresponding to the extraction region
    totref=Line2D([x.min(), x[i]], [1., 1.], color='red')
    self.ui.refl.canvas.ax.add_line(totref)
    self.ui.refl.draw()

  def addRefList(self):
    if self.ref_data is None:
      return
    # collect current settings
    channels=self.channels
    if self.add_to_ref==[]:
      self.ref_list_channels=list(channels)
    elif self.ref_list_channels!=channels:
      QtGui.QMessageBox.information(self, u'Wrong Channels',
u'''The active dataset has not the same channels 
as the ones already in the list:

%s  ≠  %s'''%(u" / ".join(channels), u' / '.join(self.ref_list_channels)),
                                    QtGui.QMessageBox.Close)
      return
    try:
      index=int(self.active_file.split('REF_M_', 1)[1].split('_', 1)[0])
    except:
      index=0
    if self.ui.directPixelOverwrite.value()>=0:
      dp=self.ui.directPixelOverwrite.value()
    else:
      dp=self.fulldata['dp']
    try:
      tth=(self.fulldata['dangle']-float(self.ui.dangle0Overwrite.text()))*pi/180.
    except ValueError:
      tth=self.fulldata['tth']*pi/180.
    settings={'file': self.active_file,
              'path': self.active_folder,
              'index': index,

              'dp': dp,
              'tth': tth,
              'x_pos': self.ui.refXPos.value(),
              'x_width': self.ui.refXWidth.value(),
              'y_pos': self.ui.refYPos.value(),
              'y_width': self.ui.refYWidth.value(),
              'bg_pos': self.ui.bgCenter.value(),
              'bg_width': self.ui.bgWidth.value(),
              'range': [self.ui.rangeStart.value(), self.ui.rangeEnd.value()],
              'scale': 10**self.ui.refScale.value(),
              'beam_width': self.fulldata['beam_width'],
              }
    self.add_to_ref.append([settings, self.ref_x, self.ref_data, self.dref])
    self.ui.reductionTable.setRowCount(len(self.add_to_ref))
    idx=len(self.add_to_ref)-1
    self.auto_change_active=True
    self.ui.reductionTable.setItem(idx, 0,
                                   QtGui.QTableWidgetItem(str(index)))
    self.ui.reductionTable.setItem(idx, 1,
                                   QtGui.QTableWidgetItem(str(settings['scale'])))
    self.ui.reductionTable.setItem(idx, 2,
                                   QtGui.QTableWidgetItem(str(settings['range'][0])))
    self.ui.reductionTable.setItem(idx, 3,
                                   QtGui.QTableWidgetItem(str(settings['range'][1])))
    self.ui.reductionTable.setItem(idx, 4,
                                   QtGui.QTableWidgetItem(str(settings['x_pos'])))
    self.ui.reductionTable.setItem(idx, 5,
                                   QtGui.QTableWidgetItem(str(settings['x_width'])))
    self.ui.reductionTable.setItem(idx, 6,
                                   QtGui.QTableWidgetItem(str(settings['y_pos'])))
    self.ui.reductionTable.setItem(idx, 7,
                                   QtGui.QTableWidgetItem(str(settings['y_width'])))
    self.ui.reductionTable.setItem(idx, 8,
                                   QtGui.QTableWidgetItem(str(settings['bg_pos'])))
    self.ui.reductionTable.setItem(idx, 9,
                                   QtGui.QTableWidgetItem(str(settings['bg_width'])))
    self.ui.reductionTable.setItem(idx, 10,
                                   QtGui.QTableWidgetItem(os.path.join(settings['path'],
                                                                       settings['file'])))
    self.ui.reductionTable.setItem(idx, 11,
                                   QtGui.QTableWidgetItem(str(settings['dp'])))
    self.ui.reductionTable.setItem(idx, 12,
                                   QtGui.QTableWidgetItem(str(settings['tth']*180./pi)))
    self.auto_change_active=False

  def reductionTableChanged(self, item):
    '''
      Perform action upon change in data reduction list.
    '''
    if self.auto_change_active:
      return
    entry=item.row()
    column=item.column()
    settings=self.add_to_ref[entry][0]
    # reset options that can't be changed
    if column==0:
      item.setText(str(settings['index']))
      return
    elif column==10:
      item.setText(os.path.join(settings['path'], settings['file']))
      return
    # update settings from selected option
    elif column in [1, 4, 5, 6, 7, 8, 9, 11]:
      key=[None, 'scale', None, None,
           'x_pos', 'x_width',
           'y_pos', 'y_width',
           'bg_pos', 'bg_width',
           None, 'dp'][column]
      try:
        settings[key]=float(item.text())
      except ValueError:
        item.setText(str(settings[key]))
      else:
        Qz, R, dR=self.recalculateReflectivity(settings)
        self.add_to_ref[entry][1:]=[Qz, R, dR]
    elif column==2:
      try:
        settings['range'][0]=int(item.text())
      except ValueError:
        item.setText(str(settings['range'][0]))
    elif column==3:
      try:
        settings['range'][1]=int(item.text())
      except ValueError:
        item.setText(str(settings['range'][1]))
    elif column==12:
      try:
        settings['tth']=float(item.text())*pi/180.
      except ValueError:
        item.setText(str(settings['tth']*180./pi))
      else:
        Qz, R, dR=self.recalculateReflectivity(settings)
        self.add_to_ref[entry][1:]=[Qz, R, dR]
    self.plot_refl(preserve_lim=True)

  def recalculateReflectivity(self, settings):
    '''
      Use parameters to calculate and return the reflectivity
      of one file.
    '''
    filename=os.path.join(settings['path'], settings['file'])
    data=data_reduction.read_file(filename)
    fulldata=data[self.use_channel]
    data=fulldata['data']
    tof_edges=fulldata['tof']
    Qz, R, dR, _ai, _I, _BG, _Iraw=data_reduction.calc_reflectivity(data, tof_edges, settings)
    return Qz, R/fulldata['pc'], dR/fulldata['pc']

  def changeActiveChannel(self):
    '''
      The overview and reflectivity channel was changed. This
      recalculates already extracted reflectivities.
    '''
    desiredChannel=self.ui.selectedChannel.currentText().split('/')
    for channel in self.ref_list_channels:
      if channel in desiredChannel:
        self.use_channel=channel
        break
    if self.use_channel in self.ref_list_channels:
      for items in self.add_to_ref:
        Qz, R, dR=self.recalculateReflectivity(items[0])
        items[1:]=[Qz, R, dR]
    self.fileOpen(os.path.join(self.active_folder, self.active_file))

  def clearRefList(self):
    self.add_to_ref=[]
    self.ui.reductionTable.setRowCount(0)
    self.plot_refl()

  def removeRefList(self):
    index=self.ui.reductionTable.currentRow()
    if index<0:
      return
    self.add_to_ref.pop(index)
    self.ui.reductionTable.removeRow(index)
    #self.ui.reductionTable.setRowCount(0)
    self.plot_refl()

  def overwriteDirectBeam(self):
    self.auto_change_active=True
    self.ui.directPixelOverwrite.setValue(self.ui.refXPos.value())
    self.ui.dangle0Overwrite.setText("%g"%self.fulldata['dangle'])
    self.auto_change_active=False
    self.overwriteChanged()

  def overwriteChanged(self):
    if not self.auto_change_active:
      self.updateLabels()
      self.calcReflParams()
      self.plot_projections(preserve_lim=True)

  def reduceDatasets(self):
    if len(self.add_to_ref)==0:
      QtGui.QMessageBox.information(self, u'Select a dataset',
                                    u'Please select at least\none dataset to reduce.',
                                    QtGui.QMessageBox.Close)
      return
    if self.ref_norm is None:
      QtGui.QMessageBox.information(self, u'Select normlaization',
                                    u'You cannot extract data without normalization.',
                                    QtGui.QMessageBox.Close)
      return
    dialog=ReduceDialog(self, self.ref_list_channels,
                        self.ref_norm, self.add_to_ref)
    result=dialog.exec_()
    dialog.destroy()
    if result is None:
      return
    ind_str, channels, output_data=result
    # plot the results in a new window
    dialog=QtGui.QDialog()
    ui=UiPlot()
    ui.setupUi(dialog)
    for channel in channels:
      data=output_data[channel]
      ui.plot.errorbar(data[:, 0], data[:, 1], yerr=data[:, 2], label=channel)
    ui.plot.legend()
    ui.plot.set_xlabel(u'Q$_z$ [Å$^{-1}$]')
    ui.plot.set_ylabel(u'R [a.u.]')
    ui.plot.set_yscale('log')
    ui.plot.set_title(ind_str)
    ui.plot.show()
    dialog.show()
    self.open_plots.append(dialog)

  def plotMouseEvent(self, event):
    if event.inaxes is None:
      return
    self.ui.statusbar.showMessage(u"x=%15g    y=%15g"%(event.xdata, event.ydata))

  def plotPickX(self, event):
    if event.button is not None and self.ui.x_project.toolbar._active is None and \
        event.xdata is not None:
      if event.button==1:
        xcen=self.ui.refXPos.value()
        bgc=self.ui.bgCenter.value()
        bgw=self.ui.bgWidth.value()
        bgl=bgc-bgw/2.
        bgr=bgc+bgw/2.
        if event.xdata<bgr and abs(event.xdata-bgl)<abs(event.xdata-bgr):
          # left of right background bar and closer to left one
          bgl=event.xdata
          bgc=(bgr+bgl)/2.
          bgw=(bgr-bgl)
          self.auto_change_active=True
          self.ui.bgCenter.setValue(bgc)
          self.auto_change_active=False
          self.ui.bgWidth.setValue(bgw)
        elif event.xdata<bgr or abs(event.xdata-bgr)<abs(event.xdata-xcen):
          # left of right background bar or closer to right background than peak
          bgr=event.xdata
          bgc=(bgr+bgl)/2.
          bgw=(bgr-bgl)
          self.auto_change_active=True
          self.ui.bgCenter.setValue(bgc)
          self.auto_change_active=False
          self.ui.bgWidth.setValue(bgw)
        else:
          self.ui.refXPos.setValue(event.xdata)
      elif event.button==3:
        self.ui.refXWidth.setValue(abs(self.ui.refXPos.value()-event.xdata)*2.)

  def plotPickY(self, event):
    if event.button==1 and self.ui.x_project.toolbar._active is None and \
        event.xdata is not None:
      ypos=self.ui.refYPos.value()
      yw=self.ui.refYWidth.value()
      yl=ypos-yw/2.
      yr=ypos+yw/2.
      if abs(event.xdata-yl)<abs(event.xdata-yr):
        yl=event.xdata
      else:
        yr=event.xdata
      ypos=(yr+yl)/2.
      yw=(yr-yl)
      self.auto_change_active=True
      self.ui.refYPos.setValue(ypos)
      self.auto_change_active=False
      self.ui.refYWidth.setValue(yw)

  def readSettings(self):
    '''
      Restore window and dock geometry.
    '''
    path=os.path.join(os.path.expanduser('~/.quicknxs'), 'window.pkl')
    if os.path.exists(path):
      try:
        obj=load(open(path, 'rb'))
        self.restoreGeometry(obj[0])
        self.restoreState(obj[1])
        self.ui.splitter.setSizes(obj[2])
        self.ui.color_selector.setCurrentIndex(obj[3])
        self.ui.show_colorbars.setChecked(obj[4])
        self.ui.normalizeXTof.setChecked(obj[5])
        for i, fig in enumerate([
                                self.ui.xy_overview,
                                self.ui.xtof_overview,
                                self.ui.refl,
                                self.ui.x_project,
                                self.ui.y_project,
                                ]):
          fig.set_config(obj[6][i])
      except:
        return
    else:
      pass
      #self.ui.splitter.moveSplitter(self.ui.splitter.getRange(0)[1]/2, 0)

  def closeEvent(self, event):
    '''
      Save window and dock geometry.
    '''
    # join delay thread
    self.trigger.stay_alive=False
    self.trigger.wait()
    # store geometry and setting parameters
    figure_params=[]
    for fig in [
                self.ui.xy_overview,
                self.ui.xtof_overview,
                self.ui.refl,
                self.ui.x_project,
                self.ui.y_project,
                ]:
      figure_params.append(fig.get_config())
    obj=(self.saveGeometry(), self.saveState(),
         self.ui.splitter.sizes(),
         self.ui.color_selector.currentIndex(),
         self.ui.show_colorbars.isChecked(),
         self.ui.normalizeXTof.isChecked(),
         figure_params,
         )
    path=os.path.expanduser('~/.quicknxs')
    if not os.path.exists(path):
      os.makedirs(path)
    dump(obj, open(os.path.join(path, 'window.pkl'), 'wb'))
    QtGui.QMainWindow.closeEvent(self, event)

