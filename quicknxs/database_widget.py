# -*- coding: utf-8 -*-
#@PydevCodeAnalysisIgnore

# Form implementation generated from reading ui file 'designer/database_widget.ui'
#
# Created: Tue Jun 10 08:52:25 2014
#      by: PyQt4 UI code generator 4.10.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
  _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
  def _fromUtf8(s):
    return s

try:
  _encoding = QtGui.QApplication.UnicodeUTF8
  def _translate(context, text, disambig):
    return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
  def _translate(context, text, disambig):
    return QtGui.QApplication.translate(context, text, disambig)

class Ui_DatabaseWidget(object):
  def setupUi(self, DatabaseWidget):
    DatabaseWidget.setObjectName(_fromUtf8("DatabaseWidget"))
    DatabaseWidget.resize(800, 300)
    self.verticalLayout = QtGui.QVBoxLayout(DatabaseWidget)
    self.verticalLayout.setMargin(0)
    self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
    self.gridLayout = QtGui.QGridLayout()
    self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
    self.label_3 = QtGui.QLabel(DatabaseWidget)
    self.label_3.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
    self.label_3.setObjectName(_fromUtf8("label_3"))
    self.gridLayout.addWidget(self.label_3, 1, 0, 1, 1)
    self.searchEntry = QtGui.QLineEdit(DatabaseWidget)
    self.searchEntry.setObjectName(_fromUtf8("searchEntry"))
    self.gridLayout.addWidget(self.searchEntry, 0, 1, 1, 1)
    self.label = QtGui.QLabel(DatabaseWidget)
    self.label.setObjectName(_fromUtf8("label"))
    self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
    self.label_2 = QtGui.QLabel(DatabaseWidget)
    self.label_2.setObjectName(_fromUtf8("label_2"))
    self.gridLayout.addWidget(self.label_2, 0, 2, 1, 1)
    self.searchColumn = QtGui.QComboBox(DatabaseWidget)
    self.searchColumn.setObjectName(_fromUtf8("searchColumn"))
    self.searchColumn.addItem(_fromUtf8(""))
    self.searchColumn.setItemText(0, _fromUtf8(""))
    self.gridLayout.addWidget(self.searchColumn, 0, 3, 1, 2)
    self.filters = FilterWidget(DatabaseWidget)
    self.filters.setObjectName(_fromUtf8("filters"))
    self.gridLayout.addWidget(self.filters, 1, 1, 1, 4)
    self.verticalLayout.addLayout(self.gridLayout)
    self.resultsTable = HiddenResizeTableWidget(DatabaseWidget)
    self.resultsTable.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
    self.resultsTable.setTabKeyNavigation(False)
    self.resultsTable.setAlternatingRowColors(True)
    self.resultsTable.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
    self.resultsTable.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
    self.resultsTable.setHorizontalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
    self.resultsTable.setObjectName(_fromUtf8("resultsTable"))
    self.resultsTable.setColumnCount(0)
    self.resultsTable.setRowCount(0)
    self.resultsTable.verticalHeader().setVisible(False)
    self.verticalLayout.addWidget(self.resultsTable)
    self.horizontalLayout = QtGui.QHBoxLayout()
    self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
    self.label_4 = QtGui.QLabel(DatabaseWidget)
    self.label_4.setObjectName(_fromUtf8("label_4"))
    self.horizontalLayout.addWidget(self.label_4)
    self.maxResults = QtGui.QSpinBox(DatabaseWidget)
    self.maxResults.setMinimum(5)
    self.maxResults.setMaximum(1000)
    self.maxResults.setSingleStep(5)
    self.maxResults.setProperty("value", 10)
    self.maxResults.setObjectName(_fromUtf8("maxResults"))
    self.horizontalLayout.addWidget(self.maxResults)
    self.resultLabel = QtGui.QLabel(DatabaseWidget)
    self.resultLabel.setObjectName(_fromUtf8("resultLabel"))
    self.horizontalLayout.addWidget(self.resultLabel)
    spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
    self.horizontalLayout.addItem(spacerItem)
    self.pushButton = QtGui.QPushButton(DatabaseWidget)
    self.pushButton.setDefault(True)
    self.pushButton.setObjectName(_fromUtf8("pushButton"))
    self.horizontalLayout.addWidget(self.pushButton)
    self.verticalLayout.addLayout(self.horizontalLayout)

    self.retranslateUi(DatabaseWidget)
    QtCore.QObject.connect(self.searchEntry, QtCore.SIGNAL(_fromUtf8("returnPressed()")), DatabaseWidget.applyFilters)
    QtCore.QObject.connect(self.searchColumn, QtCore.SIGNAL(_fromUtf8("currentIndexChanged(int)")), DatabaseWidget.applyFilters)
    QtCore.QObject.connect(self.resultsTable, QtCore.SIGNAL(_fromUtf8("doubleClicked(QModelIndex)")), DatabaseWidget.loadDataset)
    QtCore.QObject.connect(self.maxResults, QtCore.SIGNAL(_fromUtf8("valueChanged(int)")), DatabaseWidget.applyFilters)
    QtCore.QObject.connect(self.filters, QtCore.SIGNAL(_fromUtf8("filtersChanged()")), DatabaseWidget.applyFilters)
    QtCore.QObject.connect(self.pushButton, QtCore.SIGNAL(_fromUtf8("pressed()")), DatabaseWidget.applyFilters)
    QtCore.QMetaObject.connectSlotsByName(DatabaseWidget)

  def retranslateUi(self, DatabaseWidget):
    DatabaseWidget.setWindowTitle(_translate("DatabaseWidget", "Form", None))
    self.label_3.setText(_translate("DatabaseWidget", "\n"
"Filters:", None))
    self.label.setText(_translate("DatabaseWidget", "Search", None))
    self.label_2.setText(_translate("DatabaseWidget", "Column", None))
    self.label_4.setText(_translate("DatabaseWidget", "Max. Results", None))
    self.resultLabel.setText(_translate("DatabaseWidget", "Results: 0/0", None))
    self.pushButton.setText(_translate("DatabaseWidget", "Refresh", None))

from .help_widgets import HiddenResizeTableWidget, FilterWidget
