# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'designer/database_widget.ui'
#
# Created by: PyQt5 UI code generator 5.7
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_DatabaseWidget(object):
  def setupUi(self, DatabaseWidget):
    DatabaseWidget.setObjectName("DatabaseWidget")
    DatabaseWidget.resize(800, 300)
    self.verticalLayout = QtWidgets.QVBoxLayout(DatabaseWidget)
    self.verticalLayout.setContentsMargins(0, 0, 0, 0)
    self.verticalLayout.setObjectName("verticalLayout")
    self.gridLayout = QtWidgets.QGridLayout()
    self.gridLayout.setObjectName("gridLayout")
    self.label_3 = QtWidgets.QLabel(DatabaseWidget)
    self.label_3.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
    self.label_3.setObjectName("label_3")
    self.gridLayout.addWidget(self.label_3, 1, 0, 1, 1)
    self.searchEntry = QtWidgets.QLineEdit(DatabaseWidget)
    self.searchEntry.setObjectName("searchEntry")
    self.gridLayout.addWidget(self.searchEntry, 0, 1, 1, 1)
    self.label = QtWidgets.QLabel(DatabaseWidget)
    self.label.setObjectName("label")
    self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
    self.label_2 = QtWidgets.QLabel(DatabaseWidget)
    self.label_2.setObjectName("label_2")
    self.gridLayout.addWidget(self.label_2, 0, 2, 1, 1)
    self.searchColumn = QtWidgets.QComboBox(DatabaseWidget)
    self.searchColumn.setObjectName("searchColumn")
    self.searchColumn.addItem("")
    self.searchColumn.setItemText(0, "")
    self.gridLayout.addWidget(self.searchColumn, 0, 3, 1, 2)
    self.filters = FilterWidget(DatabaseWidget)
    self.filters.setObjectName("filters")
    self.gridLayout.addWidget(self.filters, 1, 1, 1, 4)
    self.verticalLayout.addLayout(self.gridLayout)
    self.resultsTable = HiddenResizeTableWidget(DatabaseWidget)
    self.resultsTable.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
    self.resultsTable.setTabKeyNavigation(False)
    self.resultsTable.setAlternatingRowColors(True)
    self.resultsTable.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
    self.resultsTable.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
    self.resultsTable.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
    self.resultsTable.setObjectName("resultsTable")
    self.resultsTable.setColumnCount(0)
    self.resultsTable.setRowCount(0)
    self.resultsTable.verticalHeader().setVisible(False)
    self.verticalLayout.addWidget(self.resultsTable)
    self.horizontalLayout = QtWidgets.QHBoxLayout()
    self.horizontalLayout.setObjectName("horizontalLayout")
    self.label_4 = QtWidgets.QLabel(DatabaseWidget)
    self.label_4.setObjectName("label_4")
    self.horizontalLayout.addWidget(self.label_4)
    self.maxResults = QtWidgets.QSpinBox(DatabaseWidget)
    self.maxResults.setMinimum(5)
    self.maxResults.setMaximum(1000)
    self.maxResults.setSingleStep(5)
    self.maxResults.setProperty("value", 10)
    self.maxResults.setObjectName("maxResults")
    self.horizontalLayout.addWidget(self.maxResults)
    self.resultLabel = QtWidgets.QLabel(DatabaseWidget)
    self.resultLabel.setObjectName("resultLabel")
    self.horizontalLayout.addWidget(self.resultLabel)
    spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
    self.horizontalLayout.addItem(spacerItem)
    self.pushButton = QtWidgets.QPushButton(DatabaseWidget)
    self.pushButton.setDefault(True)
    self.pushButton.setObjectName("pushButton")
    self.horizontalLayout.addWidget(self.pushButton)
    self.verticalLayout.addLayout(self.horizontalLayout)

    self.retranslateUi(DatabaseWidget)
    self.searchEntry.returnPressed.connect(DatabaseWidget.applyFilters)
    self.searchColumn.currentIndexChanged['int'].connect(DatabaseWidget.applyFilters)
    self.resultsTable.doubleClicked['QModelIndex'].connect(DatabaseWidget.loadDataset)
    self.maxResults.valueChanged['int'].connect(DatabaseWidget.applyFilters)
    self.filters.filtersChanged.connect(DatabaseWidget.applyFilters)
    self.pushButton.pressed.connect(DatabaseWidget.applyFilters)
    QtCore.QMetaObject.connectSlotsByName(DatabaseWidget)

  def retranslateUi(self, DatabaseWidget):
    _translate = QtCore.QCoreApplication.translate
    DatabaseWidget.setWindowTitle(_translate("DatabaseWidget", "Form"))
    self.label_3.setText(_translate("DatabaseWidget", "\n"
"Filters:"))
    self.label.setText(_translate("DatabaseWidget", "Search"))
    self.label_2.setText(_translate("DatabaseWidget", "Column"))
    self.label_4.setText(_translate("DatabaseWidget", "Max. Results"))
    self.resultLabel.setText(_translate("DatabaseWidget", "Results: 0/0"))
    self.pushButton.setText(_translate("DatabaseWidget", "Refresh"))

from .help_widgets import FilterWidget, HiddenResizeTableWidget
