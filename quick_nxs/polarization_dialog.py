# -*- coding: utf-8 -*-
#@PydevCodeAnalysisIgnore

# Form implementation generated from reading ui file 'designer/polarization_dialog.ui'
#
# Created: Thu May  9 10:27:33 2013
#      by: PyQt4 UI code generator 4.9.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
  _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
  _fromUtf8 = lambda s: s

class Ui_Dialog(object):
  def setupUi(self, Dialog):
    Dialog.setObjectName(_fromUtf8("Dialog"))
    Dialog.resize(776, 710)
    self.horizontalLayout_2 = QtGui.QHBoxLayout(Dialog)
    self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
    self.splitter_2 = QtGui.QSplitter(Dialog)
    self.splitter_2.setOrientation(QtCore.Qt.Horizontal)
    self.splitter_2.setObjectName(_fromUtf8("splitter_2"))
    self.splitter = QtGui.QSplitter(self.splitter_2)
    self.splitter.setOrientation(QtCore.Qt.Vertical)
    self.splitter.setObjectName(_fromUtf8("splitter"))
    self.groupBox = QtGui.QGroupBox(self.splitter)
    sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Expanding)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(10)
    sizePolicy.setHeightForWidth(self.groupBox.sizePolicy().hasHeightForWidth())
    self.groupBox.setSizePolicy(sizePolicy)
    self.groupBox.setObjectName(_fromUtf8("groupBox"))
    self.verticalLayout = QtGui.QVBoxLayout(self.groupBox)
    self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
    self.flippingRatios = MPLWidget(self.groupBox)
    sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
    sizePolicy.setHorizontalStretch(1)
    sizePolicy.setVerticalStretch(2)
    sizePolicy.setHeightForWidth(self.flippingRatios.sizePolicy().hasHeightForWidth())
    self.flippingRatios.setSizePolicy(sizePolicy)
    self.flippingRatios.setObjectName(_fromUtf8("flippingRatios"))
    self.verticalLayout.addWidget(self.flippingRatios)
    self.horizontalLayout = QtGui.QHBoxLayout()
    self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
    self.label_2 = QtGui.QLabel(self.groupBox)
    sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
    self.label_2.setSizePolicy(sizePolicy)
    self.label_2.setAlignment(QtCore.Qt.AlignCenter)
    self.label_2.setObjectName(_fromUtf8("label_2"))
    self.horizontalLayout.addWidget(self.label_2)
    self.label_3 = QtGui.QLabel(self.groupBox)
    sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(self.label_3.sizePolicy().hasHeightForWidth())
    self.label_3.setSizePolicy(sizePolicy)
    self.label_3.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
    self.label_3.setObjectName(_fromUtf8("label_3"))
    self.horizontalLayout.addWidget(self.label_3)
    self.FR1 = QtGui.QLabel(self.groupBox)
    sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(self.FR1.sizePolicy().hasHeightForWidth())
    self.FR1.setSizePolicy(sizePolicy)
    self.FR1.setObjectName(_fromUtf8("FR1"))
    self.horizontalLayout.addWidget(self.FR1)
    self.label_5 = QtGui.QLabel(self.groupBox)
    sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(self.label_5.sizePolicy().hasHeightForWidth())
    self.label_5.setSizePolicy(sizePolicy)
    self.label_5.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
    self.label_5.setObjectName(_fromUtf8("label_5"))
    self.horizontalLayout.addWidget(self.label_5)
    self.FR2 = QtGui.QLabel(self.groupBox)
    sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(self.FR2.sizePolicy().hasHeightForWidth())
    self.FR2.setSizePolicy(sizePolicy)
    self.FR2.setObjectName(_fromUtf8("FR2"))
    self.horizontalLayout.addWidget(self.FR2)
    self.verticalLayout.addLayout(self.horizontalLayout)
    self.groupBox1 = QtGui.QGroupBox(self.splitter)
    sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Expanding)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(1)
    sizePolicy.setHeightForWidth(self.groupBox1.sizePolicy().hasHeightForWidth())
    self.groupBox1.setSizePolicy(sizePolicy)
    self.groupBox1.setObjectName(_fromUtf8("groupBox1"))
    self.verticalLayout_2 = QtGui.QVBoxLayout(self.groupBox1)
    self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
    self.horizontalLayout_3 = QtGui.QHBoxLayout()
    self.horizontalLayout_3.setObjectName(_fromUtf8("horizontalLayout_3"))
    self.pushButton_2 = QtGui.QPushButton(self.groupBox1)
    self.pushButton_2.setObjectName(_fromUtf8("pushButton_2"))
    self.horizontalLayout_3.addWidget(self.pushButton_2)
    self.pushButton = QtGui.QPushButton(self.groupBox1)
    self.pushButton.setObjectName(_fromUtf8("pushButton"))
    self.horizontalLayout_3.addWidget(self.pushButton)
    self.verticalLayout_2.addLayout(self.horizontalLayout_3)
    self.wlTable = QtGui.QTableWidget(self.groupBox1)
    sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(1)
    sizePolicy.setHeightForWidth(self.wlTable.sizePolicy().hasHeightForWidth())
    self.wlTable.setSizePolicy(sizePolicy)
    self.wlTable.setObjectName(_fromUtf8("wlTable"))
    self.wlTable.setColumnCount(3)
    self.wlTable.setRowCount(0)
    item = QtGui.QTableWidgetItem()
    self.wlTable.setHorizontalHeaderItem(0, item)
    item = QtGui.QTableWidgetItem()
    self.wlTable.setHorizontalHeaderItem(1, item)
    item = QtGui.QTableWidgetItem()
    self.wlTable.setHorizontalHeaderItem(2, item)
    self.verticalLayout_2.addWidget(self.wlTable)
    self.horizontalLayout_4 = QtGui.QHBoxLayout()
    self.horizontalLayout_4.setObjectName(_fromUtf8("horizontalLayout_4"))
    self.pushButton_4 = QtGui.QPushButton(self.groupBox1)
    self.pushButton_4.setObjectName(_fromUtf8("pushButton_4"))
    self.horizontalLayout_4.addWidget(self.pushButton_4)
    self.pushButton_3 = QtGui.QPushButton(self.groupBox1)
    self.pushButton_3.setObjectName(_fromUtf8("pushButton_3"))
    self.horizontalLayout_4.addWidget(self.pushButton_3)
    self.verticalLayout_2.addLayout(self.horizontalLayout_4)
    self.xTable = QtGui.QTableWidget(self.groupBox1)
    sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(1)
    sizePolicy.setHeightForWidth(self.xTable.sizePolicy().hasHeightForWidth())
    self.xTable.setSizePolicy(sizePolicy)
    self.xTable.setObjectName(_fromUtf8("xTable"))
    self.xTable.setColumnCount(2)
    self.xTable.setRowCount(0)
    item = QtGui.QTableWidgetItem()
    self.xTable.setHorizontalHeaderItem(0, item)
    item = QtGui.QTableWidgetItem()
    self.xTable.setHorizontalHeaderItem(1, item)
    self.verticalLayout_2.addWidget(self.xTable)
    self.groupBox_2 = QtGui.QGroupBox(self.splitter_2)
    self.groupBox_2.setObjectName(_fromUtf8("groupBox_2"))
    self.verticalLayout_3 = QtGui.QVBoxLayout(self.groupBox_2)
    self.verticalLayout_3.setObjectName(_fromUtf8("verticalLayout_3"))
    self.label = QtGui.QLabel(self.groupBox_2)
    sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
    self.label.setSizePolicy(sizePolicy)
    self.label.setAlignment(QtCore.Qt.AlignCenter)
    self.label.setObjectName(_fromUtf8("label"))
    self.verticalLayout_3.addWidget(self.label)
    self.wavelengthPol = MPLWidget(self.groupBox_2)
    self.wavelengthPol.setObjectName(_fromUtf8("wavelengthPol"))
    self.verticalLayout_3.addWidget(self.wavelengthPol)
    self.label_4 = QtGui.QLabel(self.groupBox_2)
    sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(self.label_4.sizePolicy().hasHeightForWidth())
    self.label_4.setSizePolicy(sizePolicy)
    self.label_4.setAlignment(QtCore.Qt.AlignCenter)
    self.label_4.setObjectName(_fromUtf8("label_4"))
    self.verticalLayout_3.addWidget(self.label_4)
    self.detectorPol = MPLWidget(self.groupBox_2)
    self.detectorPol.setObjectName(_fromUtf8("detectorPol"))
    self.verticalLayout_3.addWidget(self.detectorPol)
    self.horizontalLayout_2.addWidget(self.splitter_2)

    self.retranslateUi(Dialog)
    QtCore.QObject.connect(self.pushButton_2, QtCore.SIGNAL(_fromUtf8("pressed()")), Dialog.addWL)
    QtCore.QObject.connect(self.pushButton, QtCore.SIGNAL(_fromUtf8("pressed()")), Dialog.clearWL)
    QtCore.QObject.connect(self.pushButton_4, QtCore.SIGNAL(_fromUtf8("pressed()")), Dialog.addX)
    QtCore.QObject.connect(self.pushButton_3, QtCore.SIGNAL(_fromUtf8("pressed()")), Dialog.clearX)
    QtCore.QObject.connect(self.wlTable, QtCore.SIGNAL(_fromUtf8("cellChanged(int,int)")), Dialog.update_fr)
    QtCore.QMetaObject.connectSlotsByName(Dialog)

  def retranslateUi(self, Dialog):
    Dialog.setWindowTitle(QtGui.QApplication.translate("Dialog", "Dialog", None, QtGui.QApplication.UnicodeUTF8))
    self.groupBox.setTitle(QtGui.QApplication.translate("Dialog", "Flipping Ratios (Current Run)", None, QtGui.QApplication.UnicodeUTF8))
    self.label_2.setText(QtGui.QApplication.translate("Dialog", "Integrated:", None, QtGui.QApplication.UnicodeUTF8))
    self.label_3.setText(QtGui.QApplication.translate("Dialog", "SF1", None, QtGui.QApplication.UnicodeUTF8))
    self.FR1.setText(QtGui.QApplication.translate("Dialog", "0", None, QtGui.QApplication.UnicodeUTF8))
    self.label_5.setText(QtGui.QApplication.translate("Dialog", "SF2", None, QtGui.QApplication.UnicodeUTF8))
    self.FR2.setText(QtGui.QApplication.translate("Dialog", "0", None, QtGui.QApplication.UnicodeUTF8))
    self.groupBox1.setTitle(QtGui.QApplication.translate("Dialog", "Contributing Datasets", None, QtGui.QApplication.UnicodeUTF8))
    self.pushButton_2.setText(QtGui.QApplication.translate("Dialog", "Add", None, QtGui.QApplication.UnicodeUTF8))
    self.pushButton.setText(QtGui.QApplication.translate("Dialog", "Clear", None, QtGui.QApplication.UnicodeUTF8))
    item = self.wlTable.horizontalHeaderItem(0)
    item.setText(QtGui.QApplication.translate("Dialog", "Run No.", None, QtGui.QApplication.UnicodeUTF8))
    item = self.wlTable.horizontalHeaderItem(1)
    item.setText(QtGui.QApplication.translate("Dialog", "λ-min", None, QtGui.QApplication.UnicodeUTF8))
    item = self.wlTable.horizontalHeaderItem(2)
    item.setText(QtGui.QApplication.translate("Dialog", "λ-max", None, QtGui.QApplication.UnicodeUTF8))
    self.pushButton_4.setText(QtGui.QApplication.translate("Dialog", "Add", None, QtGui.QApplication.UnicodeUTF8))
    self.pushButton_3.setText(QtGui.QApplication.translate("Dialog", "Clear", None, QtGui.QApplication.UnicodeUTF8))
    item = self.xTable.horizontalHeaderItem(0)
    item.setText(QtGui.QApplication.translate("Dialog", "Run No.", None, QtGui.QApplication.UnicodeUTF8))
    item = self.xTable.horizontalHeaderItem(1)
    item.setText(QtGui.QApplication.translate("Dialog", "PixX", None, QtGui.QApplication.UnicodeUTF8))
    self.groupBox_2.setTitle(QtGui.QApplication.translate("Dialog", "Polarization Parameters", None, QtGui.QApplication.UnicodeUTF8))
    self.label.setText(QtGui.QApplication.translate("Dialog", "Wavelength Dependance", None, QtGui.QApplication.UnicodeUTF8))
    self.label_4.setText(QtGui.QApplication.translate("Dialog", "Detector Position Dependance", None, QtGui.QApplication.UnicodeUTF8))

from .mplwidget import MPLWidget
