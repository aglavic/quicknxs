#-*- coding: utf-8 -*-
'''
  doc
'''

import os
from PyQt4.QtGui import QDialog, QFileDialog
from PyQt4.QtCore import QThread, SIGNAL
from time import sleep, time
from numpy import vstack, savetxt, savez, array
from .plot_dialog import Ui_Dialog as UiPlot
from .reduce_dialog import Ui_Dialog as Ui_Resource_Dialog
from .data_reduction import *
from .output_templates import *

class ReduceDialog(QDialog):

  def __init__(self, parent, channels, norm, settings):
    QDialog.__init__(self, parent)
    self.ui=Ui_Resource_Dialog()
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
      if self.ui.exportOffSpecular.isChecked():
        self.extract_offspecular()

      self.export_data()
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
      P0=31-settings['range'][0]
      PN=30-settings['range'][1]
      for channel in self.channels:
        Qz, R, dR, ai, _I, _BG, _Iraw=calc_reflectivity(
                      fdata[channel]['data'],
                      fdata[channel]['tof'],
                                settings)
        rdata=vstack([Qz[PN:P0], (R/fdata[channel]['pc']/self.norm)[PN:P0],
                (dR/fdata[channel]['pc']/self.norm)[PN:P0], 0.*Qz[PN:P0]+ai]).transpose()
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
      P0=31-settings['range'][0]
      PN=30-settings['range'][1]
      for channel in self.channels:
        Qx, Qz, ki_z, kf_z, I, dI=calc_offspec(
                      fdata[channel]['data'],
                      fdata[channel]['tof'],
                                settings)
        I/=self.norm[newaxis, :]*fdata[channel]['pc']
        dI/=self.norm[newaxis, :]*fdata[channel]['pc']

        rdata=array([Qx[:, PN:P0], Qz[:, PN:P0], ki_z[:, PN:P0], kf_z[:, PN:P0],
                      ki_z[:, PN:P0]-kf_z[:, PN:P0], I[:, PN:P0], dI[:, PN:P0]],
                    copy=False).transpose((1, 2, 0))
        output_data[channel].append(rdata)
    self.output_data['OffSpec']=output_data

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

  def plot_result(self, ind_str, output_data, title):
    # plot the results in a new window
    dialog=QDialog()
    ui=UiPlot()
    ui.setupUi(dialog)
    for channel in self.channels:
      data=output_data[channel]
      if type(data) is not list:
        ui.plot.errorbar(data[:, 0], data[:, 1], yerr=data[:, 2], label=channel)
      else:
        return
    ui.plot.legend()
    ui.plot.set_xlabel(u'Q$_z$ [Å$^{-1}$]')
    ui.plot.set_ylabel(u'R [a.u.]')
    ui.plot.set_yscale('log')
    ui.plot.set_title(ind_str+' - '+title)
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
