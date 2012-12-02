#-*- coding: utf-8 -*-
'''
  Actions performed for main window signals.
'''

import os
import h5py
from glob import glob
#from time import sleep
from numpy import where, pi, sin, newaxis, isnan, maximum, arange, exp
from scipy.stats.mstats import mquantiles
from cPickle import load, dump
from matplotlib.lines import Line2D
from PyQt4 import QtGui, QtCore
from .main_window import Ui_MainWindow
from .instrument_constants import *
from .mpfit import mpfit

class MainGUI(QtGui.QMainWindow):
  active_folder=u'.'
  active_file=u''
  ref_data=None
  ref_norm=None
  auto_change_active=False
  add_to_ref=[]
  color=None

  def __init__(self, argv=[]):
    QtGui.QMainWindow.__init__(self)
    self.ui=Ui_MainWindow()
    self.ui.setupUi(self)
    self.toggleHide()
    self.readSettings()

    self._path_watcher=QtCore.QFileSystemWatcher(self.active_folder, self)
    if len(argv)>0:
      self.fileOpen(argv[0])
    self.connect_plot_events()
    self._path_watcher.directoryChanged.connect(self.folderModified)

  def connect_plot_events(self):
    '''
      Connect matplotlib mouse events.
    '''
    for plot in [self.ui.xy_pp, self.ui.xy_mp, self.ui.xy_pm, self.ui.xy_mm,
           self.ui.xtof_pp, self.ui.xtof_mp, self.ui.xtof_pm, self.ui.xtof_mm,
           self.ui.xy_overview, self.ui.xtof_overview,
           self.ui.x_project, self.ui.y_project, self.ui.refl]:
      plot.canvas.mpl_connect('motion_notify_event', self.plotMouseEvent)
    self.ui.x_project.canvas.mpl_connect('button_release_event', self.plotPickX)

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
    fdata=h5py.File(filename)
    folder, base=os.path.split(filename)
    if folder!=self.active_folder:
      self.onPathChanged(base, folder)
    self.active_file=base
    channels=fdata.keys()
    xy={}
    xtof={}
    for channel in channels:
      if fdata[channel][u'total_counts'].value[0]==0:
        continue
      norm=fdata[channel]['proton_charge'].value[0]
      xy[channel]=fdata[channel]['bank1']['data_x_y'].value.transpose().astype(float)/norm
      xtof[channel]=fdata[channel]['bank1']['data_x_time_of_flight'].value.astype(float)/norm
    norm=fdata['entry-Off_Off']['proton_charge'].value[0]
    self.fulldata={
         'pc': norm,
         'counts': fdata['entry-Off_Off']['total_counts'].value[0],
         'data': fdata['entry-Off_Off']['bank1']['data'].value.astype(float)/norm, # 3D dataset
         'tof': fdata['entry-Off_Off']['bank1']['time_of_flight'].value,
         'dangle': fdata['entry-Off_Off']['instrument']['bank1']['DANGLE']['value'].value[0],
         'tth': fdata['entry-Off_Off']['instrument']['bank1']['DANGLE']['value'].value[0]-
                fdata['entry-Off_Off']['instrument']['bank1']['DANGLE0']['value'].value[0],
         'ai': fdata['entry-Off_Off']['sample']['SANGLE']['value'].value[0],
         'dp': fdata['entry-Off_Off']['instrument']['bank1']['DIRPIX']['value'].value[0],
                   }
    fdata.close()
    self.xydata=xy
    self.xtofdata=xtof
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

  def plot_overview(self):
    '''
      X vs. Y and X vs. Tof for main channel.
    '''
    xy=self.xydata['entry-Off_Off']
    xtof=self.xtofdata['entry-Off_Off']
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
    plots=[self.ui.xy_pp, self.ui.xy_mp, self.ui.xy_pm, self.ui.xy_mm]
    imin=1e20
    imax=1e-20
    for d in data.values():
      imin=min(imin, d[d>0].min())
      imax=max(imax, d.max())
    self.ui.xy_pp.imshow(data['entry-Off_Off'], log=True, imin=imin, imax=imax,
                         aspect='auto', cmap=self.color)
    if 'entry-On_Off' in data:
      self.ui.frame_xy_mm.show()
      if 'entry-Off_On' in data:
        self.ui.xy_mp.imshow(data['entry-On_Off'], log=True, imin=imin, imax=imax,
                             aspect='auto', cmap=self.color)
        self.ui.xy_pm.imshow(data['entry-Off_On'], log=True, imin=imin, imax=imax,
                             aspect='auto', cmap=self.color)
        self.ui.xy_mm.imshow(data['entry-On_On'], log=True, imin=imin, imax=imax,
                             aspect='auto', cmap=self.color)
        self.ui.xy_pp.set_title(u'(++)')
        self.ui.xy_mm.set_title(u'(--)')
        self.ui.xy_pm.set_title(u'(+-)')
        self.ui.xy_mp.set_title(u'(-+)')
        self.ui.frame_xy_sf.show()
      else:
        self.ui.xy_mm.imshow(data['entry-On_Off'], log=True, imin=imin, imax=imax,
                             aspect='auto', cmap=self.color)
        self.ui.xy_pp.set_title(u'(+)')
        self.ui.xy_mm.set_title(u'(-)')
        self.ui.frame_xy_sf.hide()
    else:
      self.ui.frame_xy_mm.hide()
      self.ui.frame_xy_sf.hide()
    for plot in plots:
      plot.set_xlabel(u'x [pix]')
      plot.set_ylabel(u'y [pix]')
      if plot.cplot is not None:
        plot.cplot.set_clim([imin, imax])
      if plot.cplot is not None and self.ui.show_colorbars.isChecked() and plot.cbar is None:
        plot.cbar=plot.canvas.fig.colorbar(plot.cplot)
      plot.draw()

  def plot_xtof(self):
    '''
      X vs. ToF plots for all channels.
    '''
    data=self.xtofdata
    plots=[self.ui.xtof_pp, self.ui.xtof_mp, self.ui.xtof_pm, self.ui.xtof_mm]
    if self.ui.normalizeXTof.isChecked() and self.ref_norm is not None:
      # normalize all datasets for wavelength distribution
      data_new={}
      for key, ds in data.items():
        data_new[key]=ds.astype(float)/self.ref_norm[newaxis, :]
        data_new[key][isnan(data_new[key])]=0.
      data=data_new
    imin=1e20
    imax=1e-20
    for d in data.values():
      imin=min(imin, d[d>0].min())
      imax=max(imax, d.max())
    self.ui.xtof_pp.imshow(data['entry-Off_Off'], log=True, imin=imin, imax=imax,
                           aspect='auto', cmap=self.color)
    if 'entry-On_Off' in data:
      self.ui.frame_xtof_mm.show()
      if 'entry-Off_On' in data:
        self.ui.xtof_mp.imshow(data['entry-On_Off'], log=True, imin=imin, imax=imax,
                               aspect='auto', cmap=self.color)
        self.ui.xtof_pm.imshow(data['entry-Off_On'], log=True, imin=imin, imax=imax,
                               aspect='auto', cmap=self.color)
        self.ui.xtof_mm.imshow(data['entry-On_On'], log=True, imin=imin, imax=imax,
                               aspect='auto', cmap=self.color)
        self.ui.xtof_pp.set_title(u'(++)')
        self.ui.xtof_mm.set_title(u'(--)')
        self.ui.xtof_pm.set_title(u'(+-)')
        self.ui.xtof_mm.set_title(u'(-+)')
        self.ui.frame_xtof_sf.show()
      else:
        self.ui.xtof_mm.imshow(data['entry-On_Off'], log=True, imin=imin, imax=imax,
                               aspect='auto', cmap=self.color)
        self.ui.xtof_pp.set_title(u'(+)')
        self.ui.xtof_mm.set_title(u'(-)')
        self.ui.frame_xtof_sf.hide()
    else:
      self.ui.frame_xtof_mm.hide()
      self.ui.frame_xtof_sf.hide()
    for plot in plots:
      plot.set_xlabel(u'ToF [Channel]')
      plot.set_ylabel(u'x [pix]')
      if plot.cplot is not None:
        plot.cplot.set_clim([imin, imax])
      if plot.cplot is not None and self.ui.show_colorbars.isChecked() and plot.cbar is None:
        plot.cbar=plot.canvas.fig.colorbar(plot.cplot)
      plot.draw()

  def updateLabels(self):
    d=self.fulldata

    self.ui.datasetName.setText(self.active_file)
    self.ui.datasetPCharge.setText(u"%.3e"%d['pc'])
    self.ui.datasetTotCounts.setText(u"%.4e"%d['counts'])
    self.ui.datasetDangle.setText(u"%.3f"%d['dangle'])
    self.ui.datasetTth.setText(u"%.3f"%d['tth'])
    self.ui.datasetSangle.setText(u"%.3f"%d['ai'])

  def calcReflParams(self):
    '''
      Calculate x and y regions for reflectivity extraction and put them in the
      entry fields.
    '''
    data=self.xydata['entry-Off_Off']
    if self.ui.xprojUseQuantiles.isChecked():
      d2=self.xtofdata['entry-Off_Off']
      xproj=mquantiles(d2, self.ui.xprojQuantiles.value()/100., axis=1).flatten()
    else:
      xproj=data.max(axis=0)
    yproj=data.max(axis=1)

    # calculate approximate peak position
    tth_bank=self.fulldata['tth']*pi/180.
    ai=self.fulldata['ai']*pi/180.
    pix_position=self.fulldata['dp']-(ai*2-tth_bank)/RAD_PER_PIX

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

  def replotProjections(self):
    if self.auto_change_active:
      return
    self.plot_projections(preserve_lim=True)

  def plot_projections(self, preserve_lim=False):
    '''
      Create projections of the data on the x and y axes.
      The x-projection can also be done be means of quantile calculation,
      which means that the ToF intensities are calculation which are
      exceeded by a certain number of points. This can be helpful to better
      separate the specular reflection from bragg-sheets
    '''
    data=self.xydata['entry-Off_Off']
    if self.ui.xprojUseQuantiles.isChecked():
      d2=self.xtofdata['entry-Off_Off']
      xproj=mquantiles(d2, self.ui.xprojQuantiles.value()/100., axis=1)
    else:
      xproj=data.max(axis=0)
    yproj=data.max(axis=1)

    x_peak=self.ui.refXPos.value()
    x_width=self.ui.refXWidth.value()
    y_pos=self.ui.refYPos.value()
    y_width=self.ui.refYWidth.value()
    bg_pos=self.ui.bgCenter.value()
    bg_width=self.ui.bgWidth.value()

    if preserve_lim:
      xxlim=self.ui.x_project.canvas.ax.get_xlim()
      xylim=self.ui.x_project.canvas.ax.get_ylim()
      yxlim=self.ui.y_project.canvas.ax.get_xlim()
      yylim=self.ui.y_project.canvas.ax.get_ylim()
    else:
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
    self.ui.x_project.draw()

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
    self.ui.y_project.draw()
    self.plot_refl()

  def plot_refl(self):
    '''
      Calculate and display the reflectivity from the current dataset
      and any dataset stored. Intensities from direct beam
      measurements can be used for normalization.
    '''
    data=self.fulldata['data']
    tof=self.fulldata['tof']
    tof=(tof[1:]+tof[:-1])/2.
    v=TOF_DISTANCE/tof*1e6 #m/s
    lamda=H_OVER_M_NEUTRON/v*1e10 #A
    x_pos=self.ui.refXPos.value()
    x_width=self.ui.refXWidth.value()
    y_pos=self.ui.refYPos.value()
    y_width=self.ui.refYWidth.value()
    bg_pos=self.ui.bgCenter.value()
    bg_width=self.ui.bgWidth.value()
    reg=map(lambda item: int(round(item)),
            [x_pos-x_width/2., x_pos+x_width/2., y_pos-y_width/2., y_pos+y_width/2.,
             bg_pos-bg_width/2., bg_pos+bg_width/2., ])

    fdata=data[reg[0]:reg[1], reg[2]:reg[3], :]
    bgdata=data[reg[4]:reg[5], reg[2]:reg[3], :]
    pix_offset=self.fulldata['dp']-(reg[0]+reg[1])/2.
    tth_bank=self.fulldata['tth']*pi/180.
    tth=tth_bank+pix_offset*RAD_PER_PIX
    self.ui.datasetAi.setText("%.3f"%(tth/2.*180./pi))
    self.ui.datasetROI.setText("%.4g"%(fdata.sum()*float(self.ui.datasetPCharge.text())))

    if tth>0.001:
      self.ref_x=4.*pi/lamda*sin(tth/2.)
    else:
      tth=1. # just for scaling
      self.ref_x=1./lamda

    R=fdata.sum(axis=0).sum(axis=0)/(reg[3]-reg[2])/(reg[1]-reg[0])
    BG=bgdata.sum(axis=0).sum(axis=0)/(reg[3]-reg[2])/(reg[5]-reg[4])
    self.ref_data=(R-BG)*10**self.ui.refScale.value()/tth # scale by user factor and beam-size
    self.ui.refl.clear()
    try:
      index=self.active_file.split('REF_M_', 1)[1].split('_', 1)[0]
    except:
      index='0'
    if self.ref_norm is not None:
      for settings, x, y in self.add_to_ref:
        self.ui.refl.semilogy(x, y/self.ref_norm, label=str(settings['index']))
      self.ui.refl.semilogy(self.ref_x, self.ref_data/self.ref_norm, label=index)
      self.ui.refl.set_ylabel(u'I$_{Norm}$')
    else:
      self.ui.refl.semilogy(self.ref_x, R, label='R-'+index)
      self.ui.refl.semilogy(self.ref_x, BG, label='BG-'+index)
      self.ui.refl.set_ylabel(u'I$_{Raw}$')
    if tth>0.001:
      self.ui.refl.set_xlabel(u'Q$_z$ [$\\AA^{-1}$]')
    else:
      self.ui.refl.set_xlabel(u'1/$\\lambda$ [$\\AA^{-1}$]')
    self.ui.refl.legend()
    self.ui.refl.draw()

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

  def addRefList(self):
    if self.ref_data is None:
      return
    # collect current settings
    channels=map(lambda item: item.split('entry-')[1], self.xydata.keys())
    channels.sort()
    if self.add_to_ref==[]:
      self.ref_list_channels=channels
    elif self.ref_list_channels!=channels:
      QtGui.QMessageBox.information(self, u'Wrong Channels',
u'''The active dataset has not the same channels 
as the ones already in the list:

%s
!=
%s'''%(channels, self.ref_list_channels),
                                    QtGui.QMessageBox.Close)
      return
    try:
      index=int(self.active_file.split('REF_M_', 1)[1].split('_', 1)[0])
    except:
      index=0
    settings={'file': self.active_file,
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
    self.add_to_ref.append((settings, self.ref_x, self.ref_data))
    self.ui.reductionTable.setRowCount(len(self.add_to_ref))
    idx=len(self.add_to_ref)-1
    self.ui.reductionTable.setItem(idx, 0,
                                   QtGui.QTableWidgetItem(str(index)))
    self.ui.reductionTable.setItem(idx, 1,
                                   QtGui.QTableWidgetItem(str(settings['scale'])))
    self.ui.reductionTable.setItem(idx, 2,
                                   QtGui.QTableWidgetItem(str(settings['x_pos'])))
    self.ui.reductionTable.setItem(idx, 3,
                                   QtGui.QTableWidgetItem(str(settings['x_width'])))
    self.ui.reductionTable.setItem(idx, 4,
                                   QtGui.QTableWidgetItem(str(settings['y_pos'])))
    self.ui.reductionTable.setItem(idx, 5,
                                   QtGui.QTableWidgetItem(str(settings['y_width'])))
    self.ui.reductionTable.setItem(idx, 6,
                                   QtGui.QTableWidgetItem(str(settings['bg_pos'])))
    self.ui.reductionTable.setItem(idx, 7,
                                   QtGui.QTableWidgetItem(str(settings['bg_width'])))
    self.ui.reductionTable.setItem(idx, 8,
                                   QtGui.QTableWidgetItem(os.path.join(settings['path'],
                                                                       settings['file'])))

  def clearRefList(self):
    self.add_to_ref=[]
    self.ui.reductionTable.setRowCount(0)
    self.plot_refl()

  def reduceDatasets(self):
    pass

  def plotMouseEvent(self, event):
    if event.inaxes is None:
      return
    self.ui.statusbar.showMessage(u"x=%15g    y=%15g"%(event.xdata, event.ydata))

  def plotPickX(self, event):
    if self.ui.x_project.toolbar._active is None and event.xdata is not None:
      if event.button==1:
        self.ui.refXPos.setValue(event.xdata)
      elif event.button==3:
        self.ui.refXWidth.setValue(abs(self.ui.refXPos.value()-event.xdata)*2.)

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
        #self.ui.splitter.moveSplitter(obj[2], 0)
      except:
        return
    else:
      pass
      #self.ui.splitter.moveSplitter(self.ui.splitter.getRange(0)[1]/2, 0)

  def closeEvent(self, event):
    '''
      Save window and dock geometry.
    '''
    obj=(self.saveGeometry(), self.saveState(),
         self.ui.splitter.sizes()[0])
    path=os.path.expanduser('~/.quicknxs')
    if not os.path.exists(path):
      os.makedirs(path)
    dump(obj, open(os.path.join(path, 'window.pkl'), 'wb'))
    QtGui.QMainWindow.closeEvent(self, event)

