#-*- coding: utf-8 -*-
'''
  Widget to compare different reflectivities on the fly.
'''

import os
from numpy import *
from PyQt4.QtGui import QWidget, QFileDialog, QTableWidgetItem, QDialog, QVBoxLayout, QColor, QColorDialog
from PyQt4.QtCore import Qt
from .compare_widget import Ui_Form

class CompareWidget(QWidget):
  active_folder='.'
  _refl_color_list=['#0000ff', '#ff0000', '#00ff00', '#8b00ff', '#aaaa00', '#00aaaa']
  changing_table=False

  def __init__(self, parent):
    QWidget.__init__(self, parent)
    self.ui=Ui_Form()
    self.ui.setupUi(self)
    self.ui.compareList.verticalHeader().setMovable(True)
    self.ui.compareList.verticalHeader().sectionMoved.connect(self.draw)
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
      self.ui.compareList.resizeColumnToContents(1)
      self.ui.compareList.resizeColumnToContents(2)
      self.draw()

  def read_file(self, name):
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
    item=QTableWidgetItem(color)
    item.setBackgroundColor(QColor(color))
    item.setTextColor(QColor('#ffffff'))
    item.setFlags(Qt.ItemIsEnabled)
    self.ui.compareList.setItem(idx, 1, item)
    self.ui.compareList.setItem(idx, 2, QTableWidgetItem(plotlabel))
    self.file_paths[label]=os.path.abspath(name)
    self.changing_table=False

  def clear_plot(self):
    self.ui.compareList.setRowCount(0)
    self.draw()

  def draw(self):
    if self.changing_table:
      return
    try:
      self.ui.comparePlot.clear()
      header=self.ui.compareList.verticalHeader()
      for i in range(self.ui.compareList.rowCount()):
        idx=header.logicalIndex(i)
        name=self.file_paths[self.ui.compareList.item(idx, 0).text()]
        label=self.ui.compareList.item(idx, 2).text()
        color=self.ui.compareList.item(idx, 1).text()
        data=loadtxt(name, comments='#', delimiter='\t').transpose()
        self.ui.comparePlot.errorbar(data[0], data[1], data[2], label=label, color=color)
      if self.ui.compareList.rowCount()>0:
        self.ui.comparePlot.legend()
        self.ui.comparePlot.canvas.ax.set_yscale('log')
        self.ui.comparePlot.set_xlabel(u'Q$_z$ [Å$^{-1}$]')
        self.ui.comparePlot.set_ylabel(u'R')
      self.ui.comparePlot.draw()
    except:
      pass

  def edit_cell(self, row, column):
    if column==1:
      color_item=self.ui.compareList.item(row, column)
      color=QColor(color_item.text())
      result=QColorDialog.getColor(initial=color, parent=self)
      if result.isValid():
        color_item.setText(result.name())
        color_item.setBackgroundColor(result)

class CompareDialog(QDialog):
  '''
  A simple dialog window with a CompareWidget.
  '''

  def __init__(self, *args, **kwargs):
    QDialog.__init__(self, *args, **kwargs)
    self.setWindowTitle("QuickNXS reflectiviy compare")
    self.cw=CompareWidget(self)
    vbox=QVBoxLayout(self)
    vbox.addWidget(self.cw)
    self.setLayout(vbox)
    self.layout()
