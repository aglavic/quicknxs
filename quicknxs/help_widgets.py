#-*- coding: utf-8 -*-
'''
  Small widget modifications to be easier to work with.
'''

import re
from PyQt4.QtGui import QSpinBox, QWidget, QHBoxLayout, QLabel, QPushButton, QIcon, QTableWidget
from PyQt4.QtCore import pyqtSlot, pyqtSignal
from .filter_widget import Ui_FilterWidget

class LimitingSpinBox(QSpinBox):
  '''
  A QSpinBox with additional slots changing maximum and minimum value
  to be connected to other widgets.
  '''

  @pyqtSlot(int)
  def setMaxValue(self, value):
    self.setMaximum(value)

  @pyqtSlot(int)
  def setMinValue(self, value):
    self.setMinimum(value)

class FilterWidget(QWidget):
  '''
  Widget used in the DatabaseWidget to specify a set of filters applied to the search.
  
  When adding a filter the ActiveFilter widget is used to store and display the
  options. 
  FilterWidget.getFilters() is then used in the databaseWidget to collect
  the information in a filtering string and a set of filter parameters as
  needed by the buzhug database select method for filtering.
  '''
  filtersChanged=pyqtSignal()
  active_filters=None
  columns=None

  def __init__(self, *args, **opts):
    QWidget.__init__(self, *args, **opts)
    self.active_filters=[]
    self.ui=Ui_FilterWidget()
    self.ui.setupUi(self)

  def setColumns(self, columns):
    self.ui.filterColumn.clear()
    self.columns=columns
    for column, ignore in columns:
      self.ui.filterColumn.addItem(column)
    self.toggleColumn(0)

  def getFilters(self):
    if self.active_filters:
      fstrs=[]
      odict={}
      for i, f in enumerate(self.active_filters):
        fstrs.append(f.text%('o%i'%i))
        odict['o%i'%i]=f.value
      return ' and '.join(fstrs), odict
    else:
      return 'True', {}

  def addFilter(self):
    colname, ctype=self.columns[self.ui.filterColumn.currentIndex()]
    text=colname

    if not self.checkEntry():
      return
    value=ctype(unicode(self.ui.filterEntry.text()))

    # Go through the cases given by the type of entry and the user selection
    # for the comparison operators to be used.
    if ctype in [float, int]:
      cindex=self.ui.numberCompare.currentIndex()
      if cindex==0 or cindex==5 and ctype is int:
        text+='==%s'
      elif cindex==1:
        text+='<%s'
      elif cindex==2:
        text+='>%s'
      elif cindex==3:
        text+='<=%s'
      elif cindex==4:
        text+='>=%s'
      else:
        # approximately equal
        new_filter=ActiveFilter(self.ui.activeFilters, text+'>=%s', value*0.999)
        new_filter.button.pressed.connect(self.removeFilter)
        self.ui.activeFilters.layout().addWidget(new_filter)
        self.active_filters.append(new_filter)
        text+='<=%s'
        value=value*1.001
    else:
      cindex=self.ui.strCompare.currentIndex()
      if cindex==0:
        text+='==%s'
      elif cindex==1:
        text='%s.match('+text+')'
        value=re.compile('.*'+value+'.*')
      else:
        text='%s.match('+text+')'
        value=re.compile(value)

    new_filter=ActiveFilter(self.ui.activeFilters, text, value)
    new_filter.button.pressed.connect(self.removeFilter)
    self.ui.activeFilters.layout().addWidget(new_filter)
    self.active_filters.append(new_filter)

    self.ui.filterEntry.setText('')
    self.filtersChanged.emit()

  def checkEntry(self):
    '''
    Test if the current entry is valid for 
    '''
    ctype=self.columns[self.ui.filterColumn.currentIndex()][1]
    txt=unicode(self.ui.filterEntry.text())
    if txt.strip()=='':
      return False
      self.ui.filterEntry.setStyleSheet('QLineEdit{background: white;}')

    try:
      ctype(txt)
    except ValueError:
      self.ui.filterEntry.setStyleSheet('QLineEdit{background: #ffaaaa;}')
      return False
    else:
      self.ui.filterEntry.setStyleSheet('QLineEdit{background: white;}')
      return True

  def removeFilter(self):
    del_filter=self.sender().parent()
    idx=self.active_filters.index(del_filter)
    self.active_filters.pop(idx)
    self.ui.activeFilters.layout().takeAt(idx+1)
    del_filter.deleteLater()
    self.filtersChanged.emit()

  def toggleColumn(self, column):
    '''
    Hide or show comboboxes corresponding to the data type of the selected column.
    '''
    if self.columns[column][1] in [str, unicode]:
      self.ui.strCompare.show()
      self.ui.numberCompare.hide()
    else:
      self.ui.strCompare.hide()
      self.ui.numberCompare.show()
    self.checkEntry()

class ActiveFilter(QWidget):
  '''
  A Widget with a label and delete button that stores one filter for the FilterWidget.
  '''

  def __init__(self, parent, text, value):
    QWidget.__init__(self, parent)

    self.text=text
    self.value=value

    hbox=QHBoxLayout(self)
    hbox.setMargin(0)

    hbox.addWidget(QLabel(text%value))

    self.button=QPushButton(QIcon.fromTheme('edit-delete'), '', self)
    hbox.addWidget(self.button)


class HiddenResizeTableWidget(QTableWidget):
  '''
  A QTabbleWidget that allows to use resizeColumnsToContents() for hidden cells as well.
  '''

  def sizeHintForColumn(self, column):
    fm=self.fontMetrics()
    max_width=max([fm.width(self.item(i, column).text())+10 for i in range(self.rowCount())])
    return max_width
