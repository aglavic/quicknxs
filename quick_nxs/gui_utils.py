#-*- coding: utf-8 -*-
'''
  doc
'''

import os
from PyQt4.QtGui import QDialog, QFileDialog
from PyQt4.QtCore import QThread, SIGNAL
from time import sleep, time
from numpy import vstack, savetxt
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
      ofname=os.path.join(unicode(self.ui.directoryEntry.text()),
                          unicode(self.ui.fileNameEntry.text()))
      indices.sort()
      ind_str="+".join(map(str, indices))
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
