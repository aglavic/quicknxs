#-*- coding: utf-8 -*-
'''
  A dialog to select normalization and reflectivity files
  for the application within an automatic extraction algorithm.
'''

import os
from PyQt4.QtGui import QApplication, QDialog, QFileSystemModel
from .autoreduction_dialog import Ui_AutoReductionDialog

class AutoReductionDialog(QDialog):

  def __init__(self, parent=None,
               base_folder=os.path.expanduser('~'),
               active_folder=None):
    QDialog.__init__(self, parent)
    self.ui=Ui_AutoReductionDialog()
    self.dirmodel=QFileSystemModel()
    self.ui.setupUi(self)

    rootindex=self.dirmodel.setRootPath(base_folder)
    self.ui.directoryView.setModel(self.dirmodel)
    self.ui.directoryView.setRootIndex(rootindex)
    if active_folder:
      subindex=self.dirmodel.index(active_folder)
      self.ui.directoryView.expand(subindex)
    self.ui.directoryView.hideColumn(1)
    self.ui.directoryView.hideColumn(2)
    self.norm_files=[]
    self.ref_files=[]

  def resizeDirview(self):
    self.ui.directoryView.resizeColumnToContents(0)

  def getFiles(self):
    selection=self.ui.directoryView.selectedIndexes()
    selected_files=set(map(self.dirmodel.filePath, selection))
    return filter(os.path.isfile, selected_files)

  def addNorm(self):
    selected_files=self.getFiles()
    old_files=self.norm_files
    self.norm_files=[]
    self.ui.normalizations.clear()
    for filename in sorted(set(selected_files+old_files)):
      self.norm_files.append(filename)
      self.ui.normalizations.addItem(os.path.basename(filename))

  def delNorm(self):
    selection=map(self.ui.normalizations.row, self.ui.normalizations.selectedItems())
    for i in reversed(selection):
      self.norm_files.pop(i)
      self.ui.normalizations.takeItem(i)

  def addRef(self):
    selected_files=self.getFiles()
    old_files=self.ref_files
    self.ref_files=[]
    self.ui.reflectivities.clear()
    for filename in sorted(set(selected_files+old_files)):
      self.ref_files.append(filename)
      self.ui.reflectivities.addItem(os.path.basename(filename))

  def delRef(self):
    selection=map(self.ui.reflectivities.row, self.ui.reflectivities.selectedItems())
    for i in reversed(selection):
      self.ref_files.pop(i)
      self.ui.reflectivities.takeItem(i)

  def exec_(self, *args, **kwargs):
    self.show()
    QApplication.instance().processEvents()
    self.resizeDirview()
    self.ui.splitter_2.setSizes([self.width()*0.7, self.width()*0.3])
    self.ui.splitter.setSizes([self.height()*0.4, self.height()*0.6])

    result=QDialog.exec_(self, *args, **kwargs)
    if result and (len(self.norm_files)>0 and len(self.ref_files)>0):
      return self.norm_files, self.ref_files
    return None

def _run(argv=[]):
  app=QApplication(argv)
  dialog=AutoReductionDialog(None)
  dialog.show()
  return app.exec_()
