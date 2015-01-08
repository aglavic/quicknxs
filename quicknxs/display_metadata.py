# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'designer/display_metadata.ui'
#
# Created: Thu Jan  8 16:48:19 2015
#      by: PyQt4 UI code generator 4.7.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(1178, 979)
        self.verticalLayout_2 = QtGui.QVBoxLayout(Dialog)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.tabWidget = QtGui.QTabWidget(Dialog)
        self.tabWidget.setObjectName("tabWidget")
        self.Metadata = QtGui.QWidget()
        self.Metadata.setObjectName("Metadata")
        self.verticalLayout_3 = QtGui.QVBoxLayout(self.Metadata)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.verticalLayout_4 = QtGui.QVBoxLayout()
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.metadataTable = QtGui.QTableWidget(self.Metadata)
        self.metadataTable.setObjectName("metadataTable")
        self.metadataTable.setColumnCount(3)
        self.metadataTable.setRowCount(0)
        item = QtGui.QTableWidgetItem()
        self.metadataTable.setHorizontalHeaderItem(0, item)
        item = QtGui.QTableWidgetItem()
        self.metadataTable.setHorizontalHeaderItem(1, item)
        item = QtGui.QTableWidgetItem()
        self.metadataTable.setHorizontalHeaderItem(2, item)
        self.verticalLayout_4.addWidget(self.metadataTable)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.exportButton = QtGui.QPushButton(self.Metadata)
        self.exportButton.setEnabled(False)
        self.exportButton.setObjectName("exportButton")
        self.horizontalLayout_2.addWidget(self.exportButton)
        self.verticalLayout_4.addLayout(self.horizontalLayout_2)
        self.verticalLayout_3.addLayout(self.verticalLayout_4)
        self.tabWidget.addTab(self.Metadata, "")
        self.Configure = QtGui.QWidget()
        self.Configure.setObjectName("Configure")
        self.verticalLayout_5 = QtGui.QVBoxLayout(self.Configure)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.configureTable = QtGui.QTableWidget(self.Configure)
        self.configureTable.setAlternatingRowColors(True)
        self.configureTable.setObjectName("configureTable")
        self.configureTable.setColumnCount(4)
        self.configureTable.setRowCount(0)
        item = QtGui.QTableWidgetItem()
        self.configureTable.setHorizontalHeaderItem(0, item)
        item = QtGui.QTableWidgetItem()
        self.configureTable.setHorizontalHeaderItem(1, item)
        item = QtGui.QTableWidgetItem()
        self.configureTable.setHorizontalHeaderItem(2, item)
        item = QtGui.QTableWidgetItem()
        self.configureTable.setHorizontalHeaderItem(3, item)
        self.configureTable.horizontalHeader().setSortIndicatorShown(False)
        self.configureTable.verticalHeader().setSortIndicatorShown(False)
        self.verticalLayout_5.addWidget(self.configureTable)
        self.tabWidget.addTab(self.Configure, "")
        self.verticalLayout_2.addWidget(self.tabWidget)

        self.retranslateUi(Dialog)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QObject.connect(self.tabWidget, QtCore.SIGNAL("currentChanged(int)"), Dialog.userChangedTab)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QtGui.QApplication.translate("Dialog", "Dialog", None, QtGui.QApplication.UnicodeUTF8))
        self.metadataTable.horizontalHeaderItem(0).setText(QtGui.QApplication.translate("Dialog", "Name", None, QtGui.QApplication.UnicodeUTF8))
        self.metadataTable.horizontalHeaderItem(1).setText(QtGui.QApplication.translate("Dialog", "Value", None, QtGui.QApplication.UnicodeUTF8))
        self.metadataTable.horizontalHeaderItem(2).setText(QtGui.QApplication.translate("Dialog", "Units", None, QtGui.QApplication.UnicodeUTF8))
        self.exportButton.setText(QtGui.QApplication.translate("Dialog", "Export ...", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.Metadata), QtGui.QApplication.translate("Dialog", "Metadata", None, QtGui.QApplication.UnicodeUTF8))
        self.configureTable.horizontalHeaderItem(0).setText(QtGui.QApplication.translate("Dialog", "Display ?", None, QtGui.QApplication.UnicodeUTF8))
        self.configureTable.horizontalHeaderItem(1).setText(QtGui.QApplication.translate("Dialog", "Name", None, QtGui.QApplication.UnicodeUTF8))
        self.configureTable.horizontalHeaderItem(2).setText(QtGui.QApplication.translate("Dialog", "Value", None, QtGui.QApplication.UnicodeUTF8))
        self.configureTable.horizontalHeaderItem(3).setText(QtGui.QApplication.translate("Dialog", "Units", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.Configure), QtGui.QApplication.translate("Dialog", "Configure", None, QtGui.QApplication.UnicodeUTF8))

