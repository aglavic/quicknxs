#-*- coding: utf-8 -*-
'''
A dialog to browse through the sample database created by the autorefl script.
'''

import tempfile
import os
import atexit
from PyQt5.QtWidgets import QDialog, QWidget, QVBoxLayout, QTableWidgetItem
from PyQt5.QtCore import pyqtSignal

from .config import instrument as config
from . import database
from .database_widget import Ui_DatabaseWidget
from logging import debug

# temporary files for the database storage as only staff has write access
tmp_db=tempfile.mkdtemp("_quicknxs_database")
def clear_tmp():
  for filename in os.listdir(tmp_db):
    os.remove(os.path.join(tmp_db, filename))
  os.rmdir(tmp_db)
atexit.register(clear_tmp)

class DatabaseWidget(QWidget):
  last_result=None
  datasetSelected=pyqtSignal(unicode)

  def __init__(self, *args, **opts):
    QWidget.__init__(self, *args, **opts)
    if not config.database_file==tmp_db:
      self.copy_db()
    self.ui=Ui_DatabaseWidget()
    self.ui.setupUi(self)
    self.db=database.DatabaseHandler()
    self.buildTable()
    self.applyFilters()

  def copy_db(self):
    '''
    Copy the database to a temporary directory to make sure we have write access.
    '''
    debug('Copy buzhug database to temporary folder:')
    for filename in os.listdir(config.database_file):
      to_=os.path.join(tmp_db, filename)
      from_=os.path.join(config.database_file, filename)
      debug(u'%s -> %s'%(from_, to_))
      open(to_, 'wb').write(open(from_, 'rb').read())
    config.temp.database_file=tmp_db

  def buildTable(self):
    tbl=self.ui.resultsTable

    columns=[f[0] for f in self.db.fields]

    tbl.setColumnCount(len(columns))
    tbl.setHorizontalHeaderLabels(columns)

    for column in columns:
      self.ui.searchColumn.addItem(column)

    self.ui.filters.setColumns(self.db.fields)


  def applyFilters(self):
    tbl=self.ui.resultsTable

    tbl.setRowCount(0)

    filter_str, parameters=self.ui.filters.getFilters()
    selection=self.db(filter_str, **parameters)
    selection=selection.sort_by('+file_id')
    
    if self.ui.searchColumn.currentText()!='':
      column=str(self.ui.searchColumn.currentText())
      search_str=unicode(self.ui.searchEntry.text()).encode('utf8')
      selection=[r for r in selection if search_str in str(eval('r.'+column))]
    
    numitems=min(len(selection), self.ui.maxResults.value())
    tbl.setRowCount(numitems)

    columns=[f[0] for f in self.db.fields]

    for i, _record in enumerate(selection[-numitems:]):
      for j, column in enumerate(columns):
        value=eval('_record.'+column)
        if type(value) is str:
          tbl.setItem(i, j, QTableWidgetItem(unicode(value, 'utf8', 'ignore')))
        elif type(value) is float:
          tbl.setItem(i, j, QTableWidgetItem('%.6g'%value))
        else:
          tbl.setItem(i, j, QTableWidgetItem(unicode(value)))
    self.last_result=selection[-numitems:]

    self.ui.resultLabel.setText('Results: %i/%i'%(numitems, len(selection)))
    tbl.resizeColumnsToContents()

  def loadDataset(self):
    idx=self.ui.resultsTable.currentRow()
    self.datasetSelected.emit(self.last_result[idx].file_path)

class DatabaseDialog(QDialog):
  datasetSelected=pyqtSignal(unicode)

  def __init__(self, *args, **opts):
    QDialog.__init__(self, *args, **opts)
    self.resize(800, 300)
    self.setWindowTitle('QuickNXS - Run Database Search...')
    layout=QVBoxLayout(self)
    self.db_widget=DatabaseWidget(self)
    layout.addWidget(self.db_widget)
    self.db_widget.datasetSelected.connect(self.datasetSelected.emit)

