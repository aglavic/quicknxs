# -*- coding: utf-8 -*-
#@PydevCodeAnalysisIgnore

# Form implementation generated from reading ui file 'designer/point_picker_dialog.ui'
#
# Created: Mon Jan 13 11:59:33 2014
#      by: PyQt4 UI code generator 4.10.3
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

class Ui_Dialog(object):
  def setupUi(self, Dialog):
    Dialog.setObjectName(_fromUtf8("Dialog"))
    Dialog.resize(803, 578)
    self.verticalLayout = QtGui.QVBoxLayout(Dialog)
    self.verticalLayout.setMargin(0)
    self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
    self.splitter = QtGui.QSplitter(Dialog)
    self.splitter.setOrientation(QtCore.Qt.Horizontal)
    self.splitter.setObjectName(_fromUtf8("splitter"))
    self.pointTable = QtGui.QTableWidget(self.splitter)
    sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(self.pointTable.sizePolicy().hasHeightForWidth())
    self.pointTable.setSizePolicy(sizePolicy)
    self.pointTable.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
    self.pointTable.setProperty("showDropIndicator", False)
    self.pointTable.setAlternatingRowColors(True)
    self.pointTable.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)
    self.pointTable.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
    self.pointTable.setShowGrid(False)
    self.pointTable.setWordWrap(False)
    self.pointTable.setObjectName(_fromUtf8("pointTable"))
    self.pointTable.setColumnCount(3)
    self.pointTable.setRowCount(2)
    item = QtGui.QTableWidgetItem()
    self.pointTable.setVerticalHeaderItem(0, item)
    item = QtGui.QTableWidgetItem()
    self.pointTable.setVerticalHeaderItem(1, item)
    item = QtGui.QTableWidgetItem()
    self.pointTable.setHorizontalHeaderItem(0, item)
    item = QtGui.QTableWidgetItem()
    self.pointTable.setHorizontalHeaderItem(1, item)
    item = QtGui.QTableWidgetItem()
    self.pointTable.setHorizontalHeaderItem(2, item)
    item = QtGui.QTableWidgetItem()
    self.pointTable.setItem(0, 0, item)
    item = QtGui.QTableWidgetItem()
    self.pointTable.setItem(0, 1, item)
    item = QtGui.QTableWidgetItem()
    self.pointTable.setItem(0, 2, item)
    item = QtGui.QTableWidgetItem()
    self.pointTable.setItem(1, 0, item)
    item = QtGui.QTableWidgetItem()
    self.pointTable.setItem(1, 1, item)
    item = QtGui.QTableWidgetItem()
    self.pointTable.setItem(1, 2, item)
    self.pointTable.horizontalHeader().setDefaultSectionSize(50)
    self.widget = QtGui.QWidget(self.splitter)
    sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(self.widget.sizePolicy().hasHeightForWidth())
    self.widget.setSizePolicy(sizePolicy)
    self.widget.setObjectName(_fromUtf8("widget"))
    self.verticalLayout_2 = QtGui.QVBoxLayout(self.widget)
    self.verticalLayout_2.setMargin(0)
    self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
    self.frame = QtGui.QFrame(self.widget)
    sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(self.frame.sizePolicy().hasHeightForWidth())
    self.frame.setSizePolicy(sizePolicy)
    self.frame.setFrameShape(QtGui.QFrame.StyledPanel)
    self.frame.setFrameShadow(QtGui.QFrame.Raised)
    self.frame.setObjectName(_fromUtf8("frame"))
    self.verticalLayout_3 = QtGui.QVBoxLayout(self.frame)
    self.verticalLayout_3.setObjectName(_fromUtf8("verticalLayout_3"))
    self.plot = MPLWidget(self.frame)
    sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(self.plot.sizePolicy().hasHeightForWidth())
    self.plot.setSizePolicy(sizePolicy)
    self.plot.setObjectName(_fromUtf8("plot"))
    self.verticalLayout_3.addWidget(self.plot)
    self.verticalLayout_2.addWidget(self.frame)
    self.buttonBox = QtGui.QDialogButtonBox(self.widget)
    sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(self.buttonBox.sizePolicy().hasHeightForWidth())
    self.buttonBox.setSizePolicy(sizePolicy)
    self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
    self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
    self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
    self.verticalLayout_2.addWidget(self.buttonBox)
    self.verticalLayout.addWidget(self.splitter)

    self.retranslateUi(Dialog)
    QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), Dialog.accept)
    QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), Dialog.reject)
    QtCore.QObject.connect(self.pointTable, QtCore.SIGNAL(_fromUtf8("itemSelectionChanged()")), Dialog.selectionChanged)
    QtCore.QMetaObject.connectSlotsByName(Dialog)

  def retranslateUi(self, Dialog):
    Dialog.setWindowTitle(_translate("Dialog", "Point Picker", None))
    item = self.pointTable.verticalHeaderItem(0)
    item.setText(_translate("Dialog", "1", None))
    item = self.pointTable.verticalHeaderItem(1)
    item.setText(_translate("Dialog", "2", None))
    item = self.pointTable.horizontalHeaderItem(0)
    item.setText(_translate("Dialog", "αi", None))
    item = self.pointTable.horizontalHeaderItem(1)
    item.setText(_translate("Dialog", "Qz", None))
    item = self.pointTable.horizontalHeaderItem(2)
    item.setText(_translate("Dialog", "R", None))
    __sortingEnabled = self.pointTable.isSortingEnabled()
    self.pointTable.setSortingEnabled(False)
    item = self.pointTable.item(0, 0)
    item.setText(_translate("Dialog", "0,5", None))
    item = self.pointTable.item(0, 1)
    item.setText(_translate("Dialog", "0,05", None))
    item = self.pointTable.item(0, 2)
    item.setText(_translate("Dialog", "10", None))
    item = self.pointTable.item(1, 0)
    item.setText(_translate("Dialog", "1,", None))
    item = self.pointTable.item(1, 1)
    item.setText(_translate("Dialog", "0,1", None))
    item = self.pointTable.item(1, 2)
    item.setText(_translate("Dialog", "20", None))
    self.pointTable.setSortingEnabled(__sortingEnabled)

from .mplwidget import MPLWidget
