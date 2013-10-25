# -*- coding: utf-8 -*-
#@PydevCodeAnalysisIgnore

# Form implementation generated from reading ui file 'designer/nxs_widget.ui'
#
# Created: Fri Oct 25 12:46:52 2013
#      by: PyQt4 UI code generator 4.10
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

class Ui_NXSWidget(object):
  def setupUi(self, NXSWidget):
    NXSWidget.setObjectName(_fromUtf8("NXSWidget"))
    NXSWidget.resize(621, 599)
    self.verticalLayout = QtGui.QVBoxLayout(NXSWidget)
    self.verticalLayout.setMargin(0)
    self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
    self.splitter_2 = QtGui.QSplitter(NXSWidget)
    self.splitter_2.setOrientation(QtCore.Qt.Horizontal)
    self.splitter_2.setObjectName(_fromUtf8("splitter_2"))
    self.nodeTree = QtGui.QTreeWidget(self.splitter_2)
    self.nodeTree.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
    self.nodeTree.setProperty("showDropIndicator", False)
    self.nodeTree.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
    self.nodeTree.setObjectName(_fromUtf8("nodeTree"))
    self.nodeTree.headerItem().setText(0, _fromUtf8("1"))
    self.nodeTree.header().setVisible(False)
    self.splitter = QtGui.QSplitter(self.splitter_2)
    self.splitter.setOrientation(QtCore.Qt.Vertical)
    self.splitter.setObjectName(_fromUtf8("splitter"))
    self.nodePlotter = MPLWidget(self.splitter)
    self.nodePlotter.setObjectName(_fromUtf8("nodePlotter"))
    self.nodeInfoWidget = QtGui.QScrollArea(self.splitter)
    self.nodeInfoWidget.setWidgetResizable(True)
    self.nodeInfoWidget.setObjectName(_fromUtf8("nodeInfoWidget"))
    self.scrollAreaWidgetContents = QtGui.QWidget()
    self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 292, 276))
    self.scrollAreaWidgetContents.setObjectName(_fromUtf8("scrollAreaWidgetContents"))
    self.verticalLayout_2 = QtGui.QVBoxLayout(self.scrollAreaWidgetContents)
    self.verticalLayout_2.setMargin(0)
    self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
    self.nodeInfo = QtGui.QTextEdit(self.scrollAreaWidgetContents)
    self.nodeInfo.setReadOnly(True)
    self.nodeInfo.setObjectName(_fromUtf8("nodeInfo"))
    self.verticalLayout_2.addWidget(self.nodeInfo)
    self.nodeInfoWidget.setWidget(self.scrollAreaWidgetContents)
    self.verticalLayout.addWidget(self.splitter_2)

    self.retranslateUi(NXSWidget)
    QtCore.QObject.connect(self.nodeTree, QtCore.SIGNAL(_fromUtf8("currentItemChanged(QTreeWidgetItem*,QTreeWidgetItem*)")), NXSWidget.itemChanged)
    QtCore.QMetaObject.connectSlotsByName(NXSWidget)

  def retranslateUi(self, NXSWidget):
    NXSWidget.setWindowTitle(_translate("NXSWidget", "Form", None))

from .mplwidget import MPLWidget
