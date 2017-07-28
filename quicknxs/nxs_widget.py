# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'designer/nxs_widget.ui'
#
# Created by: PyQt5 UI code generator 5.7
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_NXSWidget(object):
  def setupUi(self, NXSWidget):
    NXSWidget.setObjectName("NXSWidget")
    NXSWidget.resize(621, 599)
    self.verticalLayout = QtWidgets.QVBoxLayout(NXSWidget)
    self.verticalLayout.setContentsMargins(0, 0, 0, 0)
    self.verticalLayout.setObjectName("verticalLayout")
    self.splitter_2 = QtWidgets.QSplitter(NXSWidget)
    self.splitter_2.setOrientation(QtCore.Qt.Horizontal)
    self.splitter_2.setObjectName("splitter_2")
    self.nodeTree = QtWidgets.QTreeWidget(self.splitter_2)
    self.nodeTree.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
    self.nodeTree.setProperty("showDropIndicator", False)
    self.nodeTree.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
    self.nodeTree.setObjectName("nodeTree")
    self.nodeTree.headerItem().setText(0, "1")
    self.nodeTree.header().setVisible(False)
    self.splitter = QtWidgets.QSplitter(self.splitter_2)
    self.splitter.setOrientation(QtCore.Qt.Vertical)
    self.splitter.setObjectName("splitter")
    self.nodePlotter = MPLWidget(self.splitter)
    self.nodePlotter.setObjectName("nodePlotter")
    self.nodeInfoWidget = QtWidgets.QScrollArea(self.splitter)
    self.nodeInfoWidget.setWidgetResizable(True)
    self.nodeInfoWidget.setObjectName("nodeInfoWidget")
    self.scrollAreaWidgetContents = QtWidgets.QWidget()
    self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 292, 276))
    self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
    self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents)
    self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
    self.verticalLayout_2.setObjectName("verticalLayout_2")
    self.nodeInfo = QtWidgets.QTextEdit(self.scrollAreaWidgetContents)
    self.nodeInfo.setReadOnly(True)
    self.nodeInfo.setObjectName("nodeInfo")
    self.verticalLayout_2.addWidget(self.nodeInfo)
    self.nodeInfoWidget.setWidget(self.scrollAreaWidgetContents)
    self.verticalLayout.addWidget(self.splitter_2)

    self.retranslateUi(NXSWidget)
    self.nodeTree.currentItemChanged['QTreeWidgetItem*','QTreeWidgetItem*'].connect(NXSWidget.itemChanged)
    QtCore.QMetaObject.connectSlotsByName(NXSWidget)

  def retranslateUi(self, NXSWidget):
    _translate = QtCore.QCoreApplication.translate
    NXSWidget.setWindowTitle(_translate("NXSWidget", "Form"))

from .mplwidget import MPLWidget
