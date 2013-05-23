# -*- coding: utf-8 -*-
#@PydevCodeAnalysisIgnore

# Form implementation generated from reading ui file 'designer/rawcompare_dialog.ui'
#
# Created: Thu May 23 09:12:17 2013
#      by: PyQt4 UI code generator 4.9.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
  _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
  _fromUtf8 = lambda s: s

class Ui_RawDat(object):
  def setupUi(self, RawDat):
    RawDat.setObjectName(_fromUtf8("RawDat"))
    RawDat.resize(666, 653)
    self.verticalLayout = QtGui.QVBoxLayout(RawDat)
    self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
    self.frame = QtGui.QFrame(RawDat)
    sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(self.frame.sizePolicy().hasHeightForWidth())
    self.frame.setSizePolicy(sizePolicy)
    self.frame.setFrameShape(QtGui.QFrame.StyledPanel)
    self.frame.setFrameShadow(QtGui.QFrame.Raised)
    self.frame.setObjectName(_fromUtf8("frame"))
    self.verticalLayout_2 = QtGui.QVBoxLayout(self.frame)
    self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
    self.plot = MPLWidget(self.frame)
    self.plot.setObjectName(_fromUtf8("plot"))
    self.verticalLayout_2.addWidget(self.plot)
    self.verticalLayout.addWidget(self.frame)
    self.gridLayout = QtGui.QGridLayout()
    self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
    self.showAll = QtGui.QCheckBox(RawDat)
    self.showAll.setObjectName(_fromUtf8("showAll"))
    self.gridLayout.addWidget(self.showAll, 1, 3, 1, 1)
    spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
    self.gridLayout.addItem(spacerItem, 1, 4, 1, 1)
    self.showNorm = QtGui.QCheckBox(RawDat)
    self.showNorm.setChecked(True)
    self.showNorm.setObjectName(_fromUtf8("showNorm"))
    self.gridLayout.addWidget(self.showNorm, 0, 0, 1, 1)
    self.showNormBG = QtGui.QCheckBox(RawDat)
    self.showNormBG.setObjectName(_fromUtf8("showNormBG"))
    self.gridLayout.addWidget(self.showNormBG, 0, 1, 1, 1)
    self.showActive = QtGui.QCheckBox(RawDat)
    self.showActive.setChecked(True)
    self.showActive.setObjectName(_fromUtf8("showActive"))
    self.gridLayout.addWidget(self.showActive, 1, 0, 1, 1)
    self.showBG = QtGui.QCheckBox(RawDat)
    self.showBG.setObjectName(_fromUtf8("showBG"))
    self.gridLayout.addWidget(self.showBG, 1, 1, 1, 1)
    self.verticalLayout.addLayout(self.gridLayout)

    self.retranslateUi(RawDat)
    QtCore.QObject.connect(self.showNorm, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), RawDat.draw_plot)
    QtCore.QObject.connect(self.showNormBG, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), RawDat.draw_plot)
    QtCore.QObject.connect(self.showBG, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), RawDat.draw_plot)
    QtCore.QObject.connect(self.showAll, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), RawDat.draw_plot)
    QtCore.QObject.connect(self.showNorm, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), self.showNormBG.setEnabled)
    QtCore.QObject.connect(self.showActive, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), self.showBG.setEnabled)
    QtCore.QObject.connect(self.showActive, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), self.showAll.setEnabled)
    QtCore.QObject.connect(self.showActive, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), RawDat.draw_plot)
    QtCore.QMetaObject.connectSlotsByName(RawDat)

  def retranslateUi(self, RawDat):
    RawDat.setWindowTitle(QtGui.QApplication.translate("RawDat", "QuickNXS - Raw Data Comparison", None, QtGui.QApplication.UnicodeUTF8))
    self.showAll.setText(QtGui.QApplication.translate("RawDat", "All States", None, QtGui.QApplication.UnicodeUTF8))
    self.showNorm.setText(QtGui.QApplication.translate("RawDat", "Show Direct Beam:", None, QtGui.QApplication.UnicodeUTF8))
    self.showNormBG.setText(QtGui.QApplication.translate("RawDat", "With Background", None, QtGui.QApplication.UnicodeUTF8))
    self.showActive.setText(QtGui.QApplication.translate("RawDat", "Show Active Run", None, QtGui.QApplication.UnicodeUTF8))
    self.showBG.setText(QtGui.QApplication.translate("RawDat", "Width Background", None, QtGui.QApplication.UnicodeUTF8))

from .mplwidget import MPLWidget
