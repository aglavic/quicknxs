# -*- coding: utf-8 -*-
#@PydevCodeAnalysisIgnore

# Form implementation generated from reading ui file 'designer/quicklog_window.ui'
#
# Created: Wed Feb 18 15:54:22 2015
#      by: PyQt4 UI code generator 4.10.4
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

class Ui_MainWindow(object):
  def setupUi(self, MainWindow):
    MainWindow.setObjectName(_fromUtf8("MainWindow"))
    MainWindow.resize(800, 600)
    icon = QtGui.QIcon.fromTheme(_fromUtf8("system-help"))
    MainWindow.setWindowIcon(icon)
    self.centralwidget = QtGui.QWidget(MainWindow)
    self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
    self.verticalLayout = QtGui.QVBoxLayout(self.centralwidget)
    self.verticalLayout.setSpacing(1)
    self.verticalLayout.setMargin(0)
    self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
    self.horizontalLayout = QtGui.QHBoxLayout()
    self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
    self.follow = QtGui.QCheckBox(self.centralwidget)
    self.follow.setChecked(True)
    self.follow.setObjectName(_fromUtf8("follow"))
    self.horizontalLayout.addWidget(self.follow)
    self.label = QtGui.QLabel(self.centralwidget)
    self.label.setObjectName(_fromUtf8("label"))
    self.horizontalLayout.addWidget(self.label)
    self.minSeverity = QtGui.QComboBox(self.centralwidget)
    self.minSeverity.setObjectName(_fromUtf8("minSeverity"))
    self.minSeverity.addItem(_fromUtf8(""))
    self.minSeverity.addItem(_fromUtf8(""))
    self.minSeverity.addItem(_fromUtf8(""))
    self.minSeverity.addItem(_fromUtf8(""))
    self.minSeverity.addItem(_fromUtf8(""))
    self.horizontalLayout.addWidget(self.minSeverity)
    self.filterThreadLabel = QtGui.QLabel(self.centralwidget)
    self.filterThreadLabel.setObjectName(_fromUtf8("filterThreadLabel"))
    self.horizontalLayout.addWidget(self.filterThreadLabel)
    self.filterThread = QtGui.QComboBox(self.centralwidget)
    self.filterThread.setObjectName(_fromUtf8("filterThread"))
    self.filterThread.addItem(_fromUtf8(""))
    self.horizontalLayout.addWidget(self.filterThread)
    self.verticalLayout.addLayout(self.horizontalLayout)
    self.logTree = QtGui.QTreeWidget(self.centralwidget)
    self.logTree.setObjectName(_fromUtf8("logTree"))
    self.verticalLayout.addWidget(self.logTree)
    MainWindow.setCentralWidget(self.centralwidget)
    self.menubar = QtGui.QMenuBar(MainWindow)
    self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 25))
    self.menubar.setObjectName(_fromUtf8("menubar"))
    self.menuFile = QtGui.QMenu(self.menubar)
    self.menuFile.setObjectName(_fromUtf8("menuFile"))
    MainWindow.setMenuBar(self.menubar)
    self.actionOpen = QtGui.QAction(MainWindow)
    self.actionOpen.setObjectName(_fromUtf8("actionOpen"))
    self.actionReload = QtGui.QAction(MainWindow)
    self.actionReload.setObjectName(_fromUtf8("actionReload"))
    self.menuFile.addAction(self.actionOpen)
    self.menuFile.addAction(self.actionReload)
    self.menubar.addAction(self.menuFile.menuAction())

    self.retranslateUi(MainWindow)
    QtCore.QObject.connect(self.minSeverity, QtCore.SIGNAL(_fromUtf8("currentIndexChanged(int)")), MainWindow.updateLog)
    QtCore.QObject.connect(self.filterThread, QtCore.SIGNAL(_fromUtf8("currentIndexChanged(int)")), MainWindow.updateLog)
    QtCore.QObject.connect(self.actionOpen, QtCore.SIGNAL(_fromUtf8("triggered()")), MainWindow.openFile)
    QtCore.QObject.connect(self.actionReload, QtCore.SIGNAL(_fromUtf8("triggered()")), MainWindow.reloadFile)
    QtCore.QMetaObject.connectSlotsByName(MainWindow)

  def retranslateUi(self, MainWindow):
    MainWindow.setWindowTitle(_translate("MainWindow", "QuickLog", None))
    self.follow.setText(_translate("MainWindow", "Follow", None))
    self.label.setText(_translate("MainWindow", "Filter Severity Below", None))
    self.minSeverity.setItemText(0, _translate("MainWindow", "DEBUG", None))
    self.minSeverity.setItemText(1, _translate("MainWindow", "INFO", None))
    self.minSeverity.setItemText(2, _translate("MainWindow", "WARNING", None))
    self.minSeverity.setItemText(3, _translate("MainWindow", "ERROR", None))
    self.minSeverity.setItemText(4, _translate("MainWindow", "FATAL", None))
    self.filterThreadLabel.setText(_translate("MainWindow", "Filter Thread", None))
    self.filterThread.setItemText(0, _translate("MainWindow", "All", None))
    self.logTree.setSortingEnabled(True)
    self.logTree.headerItem().setText(0, _translate("MainWindow", "Severity", None))
    self.logTree.headerItem().setText(1, _translate("MainWindow", "Time", None))
    self.logTree.headerItem().setText(2, _translate("MainWindow", "Content", None))
    self.logTree.headerItem().setText(3, _translate("MainWindow", "Source", None))
    self.logTree.headerItem().setText(4, _translate("MainWindow", "Line", None))
    self.logTree.headerItem().setText(5, _translate("MainWindow", "Method", None))
    self.menuFile.setTitle(_translate("MainWindow", "File", None))
    self.actionOpen.setText(_translate("MainWindow", "Open...", None))
    self.actionReload.setText(_translate("MainWindow", "Reload", None))
    self.actionReload.setShortcut(_translate("MainWindow", "F5", None))

