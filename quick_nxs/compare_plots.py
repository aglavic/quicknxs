#-*- coding: utf-8 -*-
'''
  Widget to compare different reflectivities on the fly.
'''

import os
from numpy import *
from PyQt4.QtGui import QWidget, QFileDialog, QTableWidgetItem
from PyQt4.QtCore import Qt
from .compare_widget import Ui_Form

class CompareWidget(QWidget):
  active_folder='.'
  _refl_color_list=['blue', 'red', 'green', 'purple', '#aaaa00', 'cyan']
  changing_table=False

  def __init__(self, parent):
    QWidget.__init__(self, parent)
    self.ui=Ui_Form()
    self.ui.setupUi(self)
    self.ui.compareList.horizontalHeader().sortIndicatorChanged.connect(self.draw)
    self.file_paths={}

  def open_file(self):
    filter_=u'Reflectivity (*.dat);;All (*.*)'
    names=QFileDialog.getOpenFileNames(self, u'Open reflectivity file...',
                                               directory=self.active_folder,
                                               filter=filter_)
    if names:
      self.active_folder=os.path.abspath(os.path.dirname(names[0]))
      for name in names:
        self.read_file(name)
      self.draw()

  def read_file(self, name):
    self.ui.compareList.setSortingEnabled(False)
    label=os.path.basename(name)
    idx=self.ui.compareList.rowCount()
    color=self._refl_color_list[idx%len(self._refl_color_list)]
    self.changing_table=True
    self.ui.compareList.setRowCount(idx+1)
    item=QTableWidgetItem(label)
    item.setFlags(Qt.ItemIsEnabled)
    try:
      plotlabel=label.split("REF_M_", 1)[1]
      plotlabel=plotlabel.split("_Specular")[0]+"  "+plotlabel.split("Specular_")[1].split('.')[0]
    except:
      plotlabel=label
    self.ui.compareList.setItem(idx, 0, item)
    self.ui.compareList.setItem(idx, 1, QTableWidgetItem(color))
    self.ui.compareList.setItem(idx, 2, QTableWidgetItem(plotlabel))
    self.file_paths[label]=os.path.abspath(name)
    self.changing_table=False
    self.ui.compareList.setSortingEnabled(True)


  def clear_plot(self):
    self.ui.compareList.setRowCount(0)
    self.draw()

  def draw(self):
    if self.changing_table:
      return
    try:
      self.ui.comparePlot.clear()
      for i in range(self.ui.compareList.rowCount()):
        name=self.file_paths[self.ui.compareList.item(i, 0).text()]
        label=self.ui.compareList.item(i, 2).text()
        color=self.ui.compareList.item(i, 1).text()
        data=loadtxt(name, comments='#', delimiter='\t').transpose()
        self.ui.comparePlot.errorbar(data[0], data[1], data[2], label=label, color=color)
      if self.ui.compareList.rowCount()>0:
        self.ui.comparePlot.legend()
        self.ui.comparePlot.canvas.ax.set_yscale('log')
      self.ui.comparePlot.draw()
    except:
      pass
