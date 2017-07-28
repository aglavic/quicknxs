# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'designer/rawcompare_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.7
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_RawDat(object):
  def setupUi(self, RawDat):
    RawDat.setObjectName("RawDat")
    RawDat.resize(666, 653)
    self.verticalLayout = QtWidgets.QVBoxLayout(RawDat)
    self.verticalLayout.setObjectName("verticalLayout")
    self.frame = QtWidgets.QFrame(RawDat)
    sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(self.frame.sizePolicy().hasHeightForWidth())
    self.frame.setSizePolicy(sizePolicy)
    self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
    self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
    self.frame.setObjectName("frame")
    self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.frame)
    self.verticalLayout_2.setObjectName("verticalLayout_2")
    self.plot = MPLWidget(self.frame)
    self.plot.setObjectName("plot")
    self.verticalLayout_2.addWidget(self.plot)
    self.verticalLayout.addWidget(self.frame)
    self.gridLayout = QtWidgets.QGridLayout()
    self.gridLayout.setObjectName("gridLayout")
    self.showAll = QtWidgets.QCheckBox(RawDat)
    self.showAll.setObjectName("showAll")
    self.gridLayout.addWidget(self.showAll, 1, 3, 1, 1)
    spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
    self.gridLayout.addItem(spacerItem, 1, 4, 1, 1)
    self.showNorm = QtWidgets.QCheckBox(RawDat)
    self.showNorm.setChecked(True)
    self.showNorm.setObjectName("showNorm")
    self.gridLayout.addWidget(self.showNorm, 0, 0, 1, 1)
    self.showNormBG = QtWidgets.QCheckBox(RawDat)
    self.showNormBG.setObjectName("showNormBG")
    self.gridLayout.addWidget(self.showNormBG, 0, 1, 1, 1)
    self.showActive = QtWidgets.QCheckBox(RawDat)
    self.showActive.setChecked(True)
    self.showActive.setObjectName("showActive")
    self.gridLayout.addWidget(self.showActive, 1, 0, 1, 1)
    self.showBG = QtWidgets.QCheckBox(RawDat)
    self.showBG.setObjectName("showBG")
    self.gridLayout.addWidget(self.showBG, 1, 1, 1, 1)
    self.verticalLayout.addLayout(self.gridLayout)

    self.retranslateUi(RawDat)
    self.showNorm.toggled['bool'].connect(RawDat.draw_plot)
    self.showNormBG.toggled['bool'].connect(RawDat.draw_plot)
    self.showBG.toggled['bool'].connect(RawDat.draw_plot)
    self.showAll.toggled['bool'].connect(RawDat.draw_plot)
    self.showNorm.toggled['bool'].connect(self.showNormBG.setEnabled)
    self.showActive.toggled['bool'].connect(self.showBG.setEnabled)
    self.showActive.toggled['bool'].connect(self.showAll.setEnabled)
    self.showActive.toggled['bool'].connect(RawDat.draw_plot)
    QtCore.QMetaObject.connectSlotsByName(RawDat)

  def retranslateUi(self, RawDat):
    _translate = QtCore.QCoreApplication.translate
    RawDat.setWindowTitle(_translate("RawDat", "QuickNXS - Raw Data Comparison"))
    self.showAll.setText(_translate("RawDat", "All States"))
    self.showNorm.setText(_translate("RawDat", "Show Direct Beam:"))
    self.showNormBG.setText(_translate("RawDat", "With Background"))
    self.showActive.setText(_translate("RawDat", "Show Active Run"))
    self.showBG.setText(_translate("RawDat", "Width Background"))

from .mplwidget import MPLWidget
