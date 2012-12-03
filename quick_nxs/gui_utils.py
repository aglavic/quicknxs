#-*- coding: utf-8 -*-
'''
  doc
'''

import os
from PyQt4.QtGui import QDialog
from numpy import vstack, savetxt, argsort
from .reduce_dialog import Ui_Dialog as Ui_Resource_Dialog
from .data_reduction import *

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
      output_data=dict([(channel, []) for channel in self.channels])
      indices=[]
      for settings, ignore, ignore, ignore in self.settings:
        fname=os.path.join(settings['path'], settings['file'])
        fdata=read_file(fname)
        indices.append(settings['index'])
        for channel in self.channels:
          Qz, R, dR, ai, _I, _BG, _Iraw=calc_reflectivity(
                        fdata[channel]['data'],
                        fdata[channel]['tof'],
                                  settings)
          rdata=vstack([Qz, R/fdata[channel]['pc']/self.norm,
                        dR/fdata[channel]['pc']/self.norm, 0.*Qz+ai]).transpose()
          output_data[channel].append(rdata)
      for channel in self.channels:
        d=vstack(output_data[channel])
        # sort dataset for alpha i and Qz
        order=argsort(d.view([('Qz', float), ('R', float),
                              ('dR', float), ('ai', float)
                              ]), order=['ai', 'Qz'], axis=0)
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
      ofname=os.path.join(unicode(self.ui.directoryEntry.text()),
                          unicode(self.ui.fileNameEntry.text()))
      indices.sort()
      ind_str='['+"+".join(map(str, indices))+']'
      for channel, value in output_data.items():
        output=ofname.replace('{item}', 'Specular').replace('{channel}', channel)\
                     .replace('{type}', 'dat').replace('{numbers}', ind_str)
        savetxt(output, value, delimiter='\t')
      return ind_str, self.channels, output_data
    else:
      return None

  def rm_channel(self, names):
    for name in names:
      if name in self.channels:
        self.channels.remove(name)
        return
