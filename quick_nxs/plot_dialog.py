# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'designer/plot_dialog.ui'
#
# Created: Tue Dec 11 11:33:58 2012
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
    Dialog.resize(800, 600)
    icon = QtGui.QIcon()
    icon.addPixmap(QtGui.QPixmap(_fromUtf8(":/General/logo.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
    Dialog.setWindowIcon(icon)
    self.verticalLayout = QtGui.QVBoxLayout(Dialog)
    self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
    self.plot = MPLWidget(Dialog)
    sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(self.plot.sizePolicy().hasHeightForWidth())
    self.plot.setSizePolicy(sizePolicy)
    self.plot.setObjectName(_fromUtf8("plot"))
    self.verticalLayout.addWidget(self.plot)

    self.retranslateUi(Dialog)
    QtCore.QMetaObject.connectSlotsByName(Dialog)

  def retranslateUi(self, Dialog):
    Dialog.setWindowTitle(QtGui.QApplication.translate("Dialog", "Plot", None, QtGui.QApplication.UnicodeUTF8))

from mplwidget import MPLWidget
from . import icons_rc
