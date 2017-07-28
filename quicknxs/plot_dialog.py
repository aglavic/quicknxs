# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'designer/plot_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.7
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
  def setupUi(self, Dialog):
    Dialog.setObjectName("Dialog")
    Dialog.resize(800, 600)
    icon = QtGui.QIcon()
    icon.addPixmap(QtGui.QPixmap(":/General/logo.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
    Dialog.setWindowIcon(icon)
    self.horizontalLayout = QtWidgets.QHBoxLayout(Dialog)
    self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
    self.horizontalLayout.setObjectName("horizontalLayout")
    self.plot = MPLWidget(Dialog)
    sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(self.plot.sizePolicy().hasHeightForWidth())
    self.plot.setSizePolicy(sizePolicy)
    self.plot.setObjectName("plot")
    self.horizontalLayout.addWidget(self.plot)
    self.verticalLayout = QtWidgets.QVBoxLayout()
    self.verticalLayout.setObjectName("verticalLayout")
    self.ImaxLabel = QtWidgets.QLabel(Dialog)
    self.ImaxLabel.setAlignment(QtCore.Qt.AlignCenter)
    self.ImaxLabel.setObjectName("ImaxLabel")
    self.verticalLayout.addWidget(self.ImaxLabel)
    self.Imax = QtWidgets.QDoubleSpinBox(Dialog)
    self.Imax.setMinimum(-30.0)
    self.Imax.setMaximum(30.0)
    self.Imax.setSingleStep(0.1)
    self.Imax.setObjectName("Imax")
    self.verticalLayout.addWidget(self.Imax)
    spacerItem = QtWidgets.QSpacerItem(0, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
    self.verticalLayout.addItem(spacerItem)
    self.applyButton = QtWidgets.QPushButton(Dialog)
    self.applyButton.setObjectName("applyButton")
    self.verticalLayout.addWidget(self.applyButton)
    spacerItem1 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
    self.verticalLayout.addItem(spacerItem1)
    self.IminLabel = QtWidgets.QLabel(Dialog)
    self.IminLabel.setAlignment(QtCore.Qt.AlignCenter)
    self.IminLabel.setObjectName("IminLabel")
    self.verticalLayout.addWidget(self.IminLabel)
    self.Imin = QtWidgets.QDoubleSpinBox(Dialog)
    self.Imin.setMinimum(-30.0)
    self.Imin.setMaximum(30.0)
    self.Imin.setSingleStep(0.1)
    self.Imin.setProperty("value", -6.0)
    self.Imin.setObjectName("Imin")
    self.verticalLayout.addWidget(self.Imin)
    self.clipButton = QtWidgets.QPushButton(Dialog)
    self.clipButton.setObjectName("clipButton")
    self.verticalLayout.addWidget(self.clipButton)
    self.horizontalLayout.addLayout(self.verticalLayout)

    self.retranslateUi(Dialog)
    self.Imin.valueChanged['double'].connect(Dialog.redrawColorscale)
    self.Imax.valueChanged['double'].connect(Dialog.redrawColorscale)
    self.clipButton.pressed.connect(Dialog.clipData)
    self.applyButton.pressed.connect(Dialog.applyScaling)
    QtCore.QMetaObject.connectSlotsByName(Dialog)

  def retranslateUi(self, Dialog):
    _translate = QtCore.QCoreApplication.translate
    Dialog.setWindowTitle(_translate("Dialog", "Plot"))
    self.ImaxLabel.setText(_translate("Dialog", "Max\n"
"10^"))
    self.applyButton.setText(_translate("Dialog", "Apply\n"
"scales\n"
"to\n"
"all"))
    self.IminLabel.setText(_translate("Dialog", "Min\n"
"10^"))
    self.clipButton.setText(_translate("Dialog", "Clip"))

from .mplwidget import MPLWidget
from . import icons_rc
