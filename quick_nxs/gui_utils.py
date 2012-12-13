#-*- coding: utf-8 -*-
'''
  doc
'''

import os
import subprocess
from PyQt4.QtGui import QDialog, QFileDialog, QVBoxLayout, QLabel, QProgressBar, QApplication
from PyQt4.QtCore import QThread, SIGNAL
from time import sleep, time
#from numpy import maximum
from matplotlib.lines import Line2D
from matplotlib.patches import Ellipse
from .plot_dialog import Ui_Dialog as UiPlot
from .reduce_dialog import Ui_Dialog as UiReduction
from .smooth_dialog import Ui_Dialog as UiSmooth
from .data_reduction import *
from .output_templates import *

class ReduceDialog(QDialog):

  def __init__(self, parent, channels, norm, settings):
    QDialog.__init__(self, parent)
    self.ui=UiReduction()
    self.ui.setupUi(self)
    self.norm=norm
    self.channels=list(channels) # make sure we don't alter the original list
    self.settings=settings
    self.ui.directoryEntry.setText(settings[0][0]['path'])
    if len(channels)==1:
      self.ui.exportDownDown.setEnabled(False)
      self.ui.exportDownUp.setEnabled(False)
      self.ui.exportUpDown.setEnabled(False)
    elif len(channels)<4:
      self.ui.exportDownUp.setEnabled(False)
      self.ui.exportUpDown.setEnabled(False)

  def exec_(self):
    '''
      Run the dialog and perform reflectivity extraction.
    '''
    if QDialog.exec_(self):
      # remove channels not selected
      if not self.ui.exportDownUp.isChecked():
        self.rm_channel(['-+'])
      if not self.ui.exportUpDown.isChecked():
        self.rm_channel(['-+'])
      if not self.ui.exportDownDown.isChecked():
        self.rm_channel(['-', '--'])
      if not self.ui.exportUpUp.isChecked():
        self.rm_channel(['x', '+', '++'])
      # calculate and collect reflectivities
      self.output_data={}
      self.read_data()
      self.indices.sort()
      self.ind_str="+".join(map(str, self.indices))

      if self.ui.exportSpecular.isChecked():
        self.extract_reflectivity()
      if self.ui.exportOffSpecular.isChecked() or self.ui.exportOffSpecularSmoothed.isChecked():
        self.extract_offspecular()
      if self.ui.exportOffSpecularSmoothed.isChecked():
        self.smooth_offspec()
        if not self.ui.exportOffSpecular.isChecked():
          del(self.output_data['OffSpec'])

      self.export_data()
      if self.ui.gnuplot.isChecked():
        for title, output_data in self.output_data.items():
          self.create_gnuplot_script(self.ind_str, output_data, title)
      if self.ui.plot.isChecked():
        for title, output_data in self.output_data.items():
          self.plot_result(self.ind_str, output_data, title)
      return True
    else:
      return False

  def read_data(self):
    '''
      Read the raw data of all files. This means that for multiple
      extraction routines the data is only read once.
    '''
    self.indices=[]
    self.raw_data={}
    for settings, ignore, ignore, ignore in self.settings:
      fname=os.path.join(settings['path'], settings['file'])
      settings['filename']=fname
      settings['P0']=settings['range'][0]
      settings['PN']=settings['range'][1]
      index=settings['index']
      self.raw_data[index]=read_file(fname)
      self.indices.append(index)

  def extract_reflectivity(self):
    '''
      Extract the specular reflectivity for all datasets.
    '''
    output_data=dict([(channel, []) for channel in self.channels])
    output_data['column_units']=['A^-1', 'a.u.', 'a.u.', 'rad']
    output_data['column_names']=['Qz', 'R', 'dR', 'ai']

    for settings, ignore, ignore, ignore in self.settings:
      index=settings['index']
      fdata=self.raw_data[index]
      P0=len(fdata[channel]['tof'])-settings['range'][0]-1
      PN=settings['range'][1]
      if settings['lambda_center'] in self.norm:
        norm=self.norm[settings['lambda_center']]['data']
      else:
        norm=1.
      for channel in self.channels:
        Qz, R, dR, ai, _I, _BG, _Iraw=calc_reflectivity(
                      fdata[channel]['data'],
                      fdata[channel]['tof'],
                                settings)
        rdata=vstack([Qz[PN:P0], (R/fdata[channel]['pc']/norm)[PN:P0],
                (dR/fdata[channel]['pc']/norm)[PN:P0], 0.*Qz[PN:P0]+ai]).transpose()
        output_data[channel].append(rdata)
    for channel in self.channels:
      d=vstack(output_data[channel])
      # sort dataset for alpha i and Qz
      order=argsort(d.view([('Qz', float), ('R', float),
                            ('dR', float), ('ai', float)
                            ]), order=['Qz', 'ai'], axis=0)
      d=d[order.flatten(), :]
      # remove zero counts
      d=d[d[:, 1]>0, :]
      # remove overlap by taking the higher incident angle values
      keep=[]
      for i in range(d.shape[0]-2):
        if d[i, 0]<d[i+1:, 0].min():
          keep.append(i)
      d=d[keep, :]

      output_data[channel]=d
    self.output_data['Specular']=output_data

  def extract_offspecular(self):
    '''
      Extract the specular reflectivity for all datasets.
    '''
    output_data=dict([(channel, []) for channel in self.channels])
    output_data['column_units']=['A^-1', 'A^-1', 'A^-1', 'A^-1', 'A^-1', 'a.u.', 'a.u.']
    output_data['column_names']=['Qx', 'Qz', 'ki_z', 'kf_z', 'ki_zMkf_z', 'I', 'dI']


    for settings, ignore, ignore, ignore in self.settings:
      index=settings['index']
      fdata=self.raw_data[index]
      P0=len(fdata[channel]['tof'])-settings['range'][0]-1
      PN=settings['range'][1]
      if settings['lambda_center'] in self.norm:
        norm=self.norm[settings['lambda_center']]['data']
      else:
        norm=1.
      for channel in self.channels:
        Qx, Qz, ki_z, kf_z, I, dI=calc_offspec(
                      fdata[channel]['data'],
                      fdata[channel]['tof'],
                                settings)
        I/=norm[newaxis, :]*fdata[channel]['pc']
        dI/=norm[newaxis, :]*fdata[channel]['pc']

        rdata=array([Qx[:, PN:P0], Qz[:, PN:P0], ki_z[:, PN:P0], kf_z[:, PN:P0],
                      ki_z[:, PN:P0]-kf_z[:, PN:P0], I[:, PN:P0], dI[:, PN:P0]],
                    copy=False).transpose((1, 2, 0))
        output_data[channel].append(rdata)
    self.output_data['OffSpec']=output_data

  def smooth_offspec(self):
    data=self.output_data['OffSpec'][self.channels[0]]
    dia=SmoothDialog(self.parent(), data)
    if not dia.exec_():
      dia.destroy()
      return
    settings=dia.getOptions()
    dia.destroy()
    output_data={}
    pbinfo="Smoothing Channel "
    pb=ProgressDialog(self.parent(), title="Smoothing",
                      info_start=pbinfo+self.channels[0],
                      maximum=100*len(self.channels))
    pb.show()
    for i, channel in enumerate(self.channels):
      pb.info.setText(pbinfo+channel)
      pb.add=100*i
      data=hstack(self.output_data['OffSpec'][channel])
      if settings['xy_column']==0:
        x=data[:, :, 4].flatten()
        y=data[:, :, 1].flatten()
        output_data['column_units']=['A^-1', 'A^-1', 'a.u.']
        output_data['column_names']=['ki_zMkf_z', 'Qz', 'I']
      elif settings['xy_column']==1:
        x=data[:, :, 0].flatten()
        y=data[:, :, 1].flatten()
        output_data['column_units']=['A^-1', 'A^-1', 'a.u.']
        output_data['column_names']=['Qx', 'Qz', 'I']
      else:
        x=data[:, :, 2].flatten()
        y=data[:, :, 3].flatten()
        output_data['column_units']=['A^-1', 'A^-1', 'a.u.']
        output_data['column_names']=['ki_z', 'kf_z', 'I']
      I=data[:, :, 5].flatten()
      x, y, I=smooth_data(settings, x, y, I, callback=pb.progress)
      output_data[channel]=[array([x, y, I]).transpose((1, 2, 0))]
    self.output_data['OffSpecSmooth']=output_data
    pb.destroy()

  def export_data(self):
    '''
      Write all datasets to the selected format output.
    '''
    ofname=os.path.join(unicode(self.ui.directoryEntry.text()),
                        unicode(self.ui.fileNameEntry.text()))
    plines=''
    for  settings, ignore, ignore, ignore in self.settings:
      plines+='# '+FILE_HEADER_PARAMS%settings
      plines+='\n'
    plines=plines[:-1] # remove last newline
    for key, output_data in self.output_data.items():
      if self.ui.multiAscii.isChecked():
        for channel in self.channels:
          value=output_data[channel]
          output=ofname.replace('{item}', key).replace('{channel}', channel)\
                       .replace('{type}', 'dat').replace('{numbers}', self.ind_str)
          of=open(output, 'w')
          # write the file header
          of.write(FILE_HEADER%{
                                'datatype': key,
                                'indices': self.ind_str,
                                'params_lines': plines,
                                'column_units': "\t".join(output_data['column_units']),
                                'column_names':  "\t".join(output_data['column_names']),
                                'channels': channel,
                                })
          # write the data
          if type(value) is not list:
            savetxt(of, value, delimiter='\t')
          else:
            for filemap in value:
              # separate first dimension steps by empty line
              for scan in filemap:
                savetxt(of, scan, delimiter='\t')
                of.write('\n')
            of.write('\n\n')
      if self.ui.combinedAscii.isChecked():
        output=ofname.replace('{item}', key).replace('{channel}', 'all')\
                     .replace('{type}', 'dat').replace('{numbers}', self.ind_str)
        of=open(output, 'w')
        # write the file header
        of.write(FILE_HEADER%{
                              'datatype': key,
                              'indices': self.ind_str,
                              'params_lines': plines,
                              'column_units': "\t".join(output_data['column_units']),
                              'column_names':  "\t".join(output_data['column_names']),
                              'channels': ", ".join(self.channels),
                              })
        # write all channel data separated by three empty lines and one comment
        for channel in self.channels:
          of.write('# Start of channel %s\n'%channel)
          value=output_data[channel]
          if type(value) is not list:
            savetxt(of, value, delimiter='\t')
          else:
            for filemap in value:
              # separate first dimension steps by empty line
              for scan in filemap:
                savetxt(of, scan, delimiter='\t')
                of.write('\n')
            of.write('\n\n')
          of.write('# End of channel %s\n\n\n'%channel)
        of.close()
    if self.ui.matlab.isChecked():
      from scipy.io import savemat
      for key, output_data in self.output_data.items():
        dictdata=self.dictize_data(output_data)
        output=ofname.replace('{item}', key).replace('{channel}', 'all')\
                       .replace('{type}', 'mat').replace('{numbers}', self.ind_str)
        savemat(output, dictdata, oned_as='column')
    if self.ui.numpy.isChecked():
      for key, output_data in self.output_data.items():
        dictdata=self.dictize_data(output_data)
        output=ofname.replace('{item}', key).replace('{channel}', 'all')\
                       .replace('{type}', 'npz').replace('{numbers}', self.ind_str)
        savez(output, **dictdata)

  def dictize_data(self, output_data):
    '''
      Create a dictionary for export of data for e.g. Matlab files.
    '''
    output={}
    output["columns"]=output_data['column_names']
    for channel in self.channels:
      data=output_data[channel]
      if type(data) is not list:
        output[DICTIZE_CHANNELS[channel]]=data
      else:
        for i, plotmap in enumerate(data):
          output[DICTIZE_CHANNELS[channel]+"_"+str(i)]=plotmap
    return output

  def create_gnuplot_script(self, ind_str, output_data, title):
    ofname_full=os.path.join(unicode(self.ui.directoryEntry.text()),
                        unicode(self.ui.fileNameEntry.text()))
    output=ofname_full.replace('{item}', title).replace('{channel}', 'all')\
                 .replace('{type}', 'gp').replace('{numbers}', self.ind_str)
    ofname=unicode(self.ui.fileNameEntry.text())
    if type(output_data[self.channels[0]]) is not list:
      params=dict(
                  output=ofname.replace('{item}', title).replace('{channel}', 'all')\
                         .replace('{type}', 'png').replace('{numbers}', self.ind_str),
                  xlabel=u"Q_z [Å^{-1}]",
                  ylabel=u"R [a.u.]",
                  title=ind_str+' - '+title,
                  )
      plotlines=[]
      for channel in self.channels:
        filename=ofname.replace('{item}', title).replace('{channel}', channel)\
                     .replace('{type}', 'dat').replace('{numbers}', self.ind_str)
        plotlines.append(GP_LINE%(filename, channel))
      params['plot_lines']=GP_SEP.join(plotlines)
      script=GP_TEMPLATE%params
      open(output, 'w').write(script.encode('utf8'))
    else:
      pass
    try:
      subprocess.call(['gnuplot', output], cwd=self.ui.directoryEntry.text(),
                      shell=False)
    except:
      pass

  def plot_result(self, ind_str, output_data, title):
    if type(output_data[self.channels[0]]) is not list:
      # plot the results in a new window
      dialog=QDialog()
      ui=UiPlot()
      ui.setupUi(dialog)
      for channel in self.channels:
        data=output_data[channel]
        ui.plot.errorbar(data[:, 0], data[:, 1], yerr=data[:, 2], label=channel)
      ui.plot.legend()
      ui.plot.set_xlabel(u'Q$_z$ [Å$^{-1}$]')
      ui.plot.set_ylabel(u'R [a.u.]')
      ui.plot.set_yscale('log')
      ui.plot.set_title(ind_str+' - '+title)
      ui.plot.show()
      dialog.show()
      self.parent().open_plots.append(dialog)
    else:
      if title=='OffSpec':
        x, y, z=4, 1, 5
        xl=u'k$_{i,z}$-k$_{f,z}$ [Å$^{-1}$]'
        yl=u'Q$_z$ [Å$^{-1}$]'
      else:
        x, y, z=0, 1, 2
        xl=u'%s [Å$^{-1}$]'%output_data['column_names'][0]
        yl=u'%s [Å$^{-1}$]'%output_data['column_names'][1]
      for channel in self.channels:
        # plot the results in a new window
        dialog=QDialog()
        ui=UiPlot()
        ui.setupUi(dialog)
        for data in output_data[channel]:
          ui.plot.pcolormesh(data[:, :, x], data[:, :, y], maximum(1e-6, data[:, :, z]), log=True,
                             imin=1e-6, imax=None, label=channel, cmap='default')
        ui.plot.canvas.fig.colorbar(ui.plot.cplot)
        ui.plot.set_xlabel(xl)
        ui.plot.set_ylabel(yl)
        ui.plot.set_title(ind_str+' - '+title+' - (%s)'%channel)
        ui.plot.show()
        dialog.show()
        self.parent().open_plots.append(dialog)

  def rm_channel(self, names):
    for name in names:
      if name in self.channels:
        self.channels.remove(name)
        return

  def changeDir(self):
    oldd=self.ui.directoryEntry.text()
    newd=QFileDialog.getExistingDirectory(parent=self, caption=u'Select new folder',
                                          directory=oldd)
    if newd is not None:
      self.ui.directoryEntry.setText(newd)

class SmoothDialog(QDialog):
  '''
    Dialog to define smoothing parameters.
  '''
  drawing=False

  def __init__(self, parent, data):
    QDialog.__init__(self, parent)
    self.ui=UiSmooth()
    self.ui.setupUi(self)
    self.data=data
    self.ui.plot.canvas.mpl_connect('motion_notify_event', self.plotSelect)
    self.ui.plot.canvas.mpl_connect('button_press_event', self.plotSelect)
    self.drawPlot()

  def drawPlot(self):
    '''
      Plot the unsmoothed data.
    '''
    self.drawing=True
    data=self.data
    plot=self.ui.plot
    plot.clear()
    Qzmax=0.001
    for item in data:
      Qx=item[:, :, 0]
      Qz=item[:, :, 1]
      ki_z=item[:, :, 2]
      kf_z=item[:, :, 3]
      I=item[:, :, 5]

      Qzmax=max(ki_z.max()*2., Qzmax)
      if self.ui.kizmkfzVSqz.isChecked():
        plot.pcolormesh((ki_z-kf_z), Qz, I, log=True,
                        imin=1e-6, imax=1., shading='gouraud')
      elif self.ui.qxVSqz.isChecked():
        plot.pcolormesh(Qx, Qz, I, log=True,
                        imin=1e-6, imax=1., shading='gouraud')
      else:
        plot.pcolormesh(ki_z, kf_z, I, log=True,
                        imin=1e-6, imax=1., shading='gouraud')
    if self.ui.kizmkfzVSqz.isChecked():
      plot.canvas.ax.set_xlim([-0.035, 0.035])
      plot.canvas.ax.set_ylim([0., Qzmax*1.01])
      plot.set_xlabel(u'k$_{i,z}$-k$_{f,z}$ [$\\AA^{-1}$]')
      plot.set_ylabel(u'Q$_z$ [$\\AA^{-1}$]')
      x1=-0.03
      x2=0.03
      y1=0.
      y2=Qzmax
      sigma_pos=(0., Qzmax/3.)
      sigma_ang=0.
      self.ui.sigmasCoupled.setChecked(True)
      self.ui.sigmaY.setEnabled(False)
      self.ui.sigmaX.setValue(0.0005)
      self.ui.sigmaY.setValue(0.0005)
    elif self.ui.qxVSqz.isChecked():
      plot.canvas.ax.set_xlim([-0.0005, 0.0005])
      plot.canvas.ax.set_ylim([0., Qzmax*1.01])
      plot.set_xlabel(u'Q$_x$ [$\\AA^{-1}$]')
      plot.set_ylabel(u'Q$_z$ [$\\AA^{-1}$]')
      x1=-0.0002
      x2=0.0002
      y1=0.
      y2=Qzmax
      sigma_pos=(0., Qzmax/3.)
      sigma_ang=0.
      self.ui.sigmasCoupled.setChecked(False)
      self.ui.sigmaY.setEnabled(True)
      self.ui.sigmaX.setValue(0.00001)
      self.ui.sigmaY.setValue(0.0005)
    else:
      plot.canvas.ax.set_xlim([0., Qzmax/2.*1.01])
      plot.canvas.ax.set_ylim([0., Qzmax/2.*1.01])
      plot.set_xlabel(u'k$_{i,z}$ [$\\AA^{-1}$]')
      plot.set_ylabel(u'k$_{f,z}$ [$\\AA^{-1}$]')
      x1=0.0
      x2=Qzmax/2.
      y1=0.
      y2=Qzmax/2.
      sigma_pos=(Qzmax/4., Qzmax/4.)
      sigma_ang=0.#-45.
      self.ui.sigmasCoupled.setChecked(True)
      self.ui.sigmaX.setValue(0.0005)
      self.ui.sigmaY.setValue(0.0005)
    if plot.cplot is not None:
      plot.cplot.set_clim([1e-6, 1.])
    self.rect_region=Line2D([x1, x1, x2, x2, x1], [y1, y2, y2, y1, y1])
    self.sigma_1=Ellipse(sigma_pos, self.ui.sigmaX.value()*2, self.ui.sigmaY.value()*2,
                            sigma_ang, fill=False)
    self.sigma_2=Ellipse(sigma_pos, self.ui.sigmaX.value()*4, self.ui.sigmaY.value()*4,
                            sigma_ang, fill=False)
    self.sigma_3=Ellipse(sigma_pos, self.ui.sigmaX.value()*6, self.ui.sigmaY.value()*6,
                            sigma_ang, fill=False)
    plot.canvas.ax.add_line(self.rect_region)
    plot.canvas.ax.add_artist(self.sigma_1)
    plot.canvas.ax.add_artist(self.sigma_2)
    plot.canvas.ax.add_artist(self.sigma_3)
    plot.draw()
    # set parameter values
    self.ui.gridXmin.setValue(x1)
    self.ui.gridXmax.setValue(x2)
    self.ui.gridYmin.setValue(y1)
    self.ui.gridYmax.setValue(y2)
    self.updateGrid()
    self.drawing=False

  def updateSettings(self):
    if self.drawing:
      return
    self.drawing=True
    if self.ui.sigmasCoupled.isChecked():
      self.ui.sigmaY.setValue(self.ui.sigmaX.value())
    self.updateGrid()
    # redraw indicators
    x1=self.ui.gridXmin.value()
    x2=self.ui.gridXmax.value()
    y1=self.ui.gridYmin.value()
    y2=self.ui.gridYmax.value()
    self.rect_region.set_data([x1, x1, x2, x2, x1], [y1, y2, y2, y1, y1])
    self.sigma_1.width=2*self.ui.sigmaX.value()
    self.sigma_1.height=2*self.ui.sigmaY.value()
    self.sigma_2.width=4*self.ui.sigmaX.value()
    self.sigma_2.height=4*self.ui.sigmaY.value()
    self.sigma_3.width=6*self.ui.sigmaX.value()
    self.sigma_3.height=6*self.ui.sigmaY.value()
    self.ui.plot.draw()
    self.drawing=False

  def updateGrid(self):
    if self.ui.gridSizeCoupled.isChecked():
      sx=self.ui.sigmaX.value()
      sy=self.ui.sigmaY.value()
      x1=self.ui.gridXmin.value()
      x2=self.ui.gridXmax.value()
      y1=self.ui.gridYmin.value()
      y2=self.ui.gridYmax.value()
      self.ui.gridSizeX.setValue(int((x2-x1)/sx*1.41))
      self.ui.gridSizeY.setValue(int((y2-y1)/sy*1.41))

  def plotSelect(self, event):
    '''
      Plot for y-projection has been clicked.
    '''
    if event.button==1 and self.ui.plot.toolbar._active is None and \
        event.xdata is not None:
      x=event.xdata
      y=event.ydata
      x1=self.ui.gridXmin.value()
      x2=self.ui.gridXmax.value()
      y1=self.ui.gridYmin.value()
      y2=self.ui.gridYmax.value()
      if x<x1 or abs(x-x1)<abs(x-x2):
        x1=x
      else:
        x2=x
      if y<y1 or abs(y-y1)<abs(y-y2):
        y1=y
      else:
        y2=y
      self.drawing=True
      self.ui.gridXmin.setValue(x1)
      self.ui.gridXmax.setValue(x2)
      self.ui.gridYmin.setValue(y1)
      self.ui.gridYmax.setValue(y2)
      self.drawing=False
      self.updateSettings()

  def getOptions(self):
    output={}
    x1=self.ui.gridXmin.value()
    x2=self.ui.gridXmax.value()
    y1=self.ui.gridYmin.value()
    y2=self.ui.gridYmax.value()
    output['region']=[x1, x2, y1, y2]
    width=self.ui.sigmaX.value()
    height=self.ui.sigmaY.value()
    output['sigma']=(width, height)
    gx=self.ui.gridSizeX.value()
    gy=self.ui.gridSizeY.value()
    output['grid']=(gx, gy)
    output['xy_column']=1*self.ui.qxVSqz.isChecked()+2*self.ui.kizVSkfz.isChecked()
    return output

class ProgressDialog(QDialog):

  def __init__(self, parent, title='', info_start='', maximum=100, add=0):
    QDialog.__init__(self, parent)
    self.add=add
    self.setWindowTitle(title)
    vbox=QVBoxLayout()
    self.info=QLabel(self)
    vbox.addWidget(self.info)
    self.info.setText(info_start)
    self.progressBar=QProgressBar()
    self.progressBar.setMaximum(maximum)
    self.progressBar.setMinimum(0)
    vbox.addWidget(self.progressBar)
    self.setLayout(vbox)

  def progress(self, value):
    param=value*100+self.add
    self.progressBar.setValue(param)
    app=QApplication.instance()
    app.processEvents()

class DelayedTrigger(QThread):
  '''
    A loop that carries out tasks after a short delay.
    If the tasks are triggered again later, the first
    ones are ignored and the delay is reset.
    
    This allows the GUI to be more responsive when changing
    parameters for e.g. a plot that takes longer time to
    draw.
  '''
  parent=None
  stay_alive=True
  refresh=0.01
  delay=0.25
  actions={}

  def __init__(self):
    QThread.__init__(self)

  def run(self):
    while self.stay_alive:
      for name, items in self.actions.items():
        ti, args=items
        if time()-ti>self.delay:
          self.emit(SIGNAL('activate(QString, PyQt_PyObject)'), name, args)
          del(self.actions[name])
      sleep(self.refresh)

  def __call__(self, action, *args):
    self.actions[action]=(time(), args)
