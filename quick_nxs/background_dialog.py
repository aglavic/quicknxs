# -*- coding: utf-8 -*-
#@PydevCodeAnalysisIgnore

# Form implementation generated from reading ui file 'designer/background_dialog.ui'
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
    Dialog.resize(490, 658)
    self.horizontalLayout = QtGui.QHBoxLayout(Dialog)
    self.horizontalLayout.setMargin(0)
    self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
    self.splitter = QtGui.QSplitter(Dialog)
    self.splitter.setOrientation(QtCore.Qt.Vertical)
    self.splitter.setObjectName(_fromUtf8("splitter"))
    self.xTof = MPLWidget(self.splitter)
    sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Expanding)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(1)
    sizePolicy.setHeightForWidth(self.xTof.sizePolicy().hasHeightForWidth())
    self.xTof.setSizePolicy(sizePolicy)
    self.xTof.setObjectName(_fromUtf8("xTof"))
    self.BG = MPLWidget(self.splitter)
    sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Expanding)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(1)
    sizePolicy.setHeightForWidth(self.BG.sizePolicy().hasHeightForWidth())
    self.BG.setSizePolicy(sizePolicy)
    self.BG.setObjectName(_fromUtf8("BG"))
    self.frame = QtGui.QFrame(self.splitter)
    self.frame.setFrameShape(QtGui.QFrame.StyledPanel)
    self.frame.setFrameShadow(QtGui.QFrame.Raised)
    self.frame.setObjectName(_fromUtf8("frame"))
    self.verticalLayout = QtGui.QVBoxLayout(self.frame)
    self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
    self.widget_2 = QtGui.QWidget(self.frame)
    self.widget_2.setObjectName(_fromUtf8("widget_2"))
    self.horizontalLayout_2 = QtGui.QHBoxLayout(self.widget_2)
    self.horizontalLayout_2.setMargin(0)
    self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
    self.polyregionActive = QtGui.QCheckBox(self.widget_2)
    sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(self.polyregionActive.sizePolicy().hasHeightForWidth())
    self.polyregionActive.setSizePolicy(sizePolicy)
    self.polyregionActive.setObjectName(_fromUtf8("polyregionActive"))
    self.horizontalLayout_2.addWidget(self.polyregionActive)
    self.polygonDisplay = QtGui.QLabel(self.widget_2)
    sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(self.polygonDisplay.sizePolicy().hasHeightForWidth())
    self.polygonDisplay.setSizePolicy(sizePolicy)
    self.polygonDisplay.setStyleSheet(_fromUtf8("color: rgb(192, 0, 0);"))
    self.polygonDisplay.setText(_fromUtf8(""))
    self.polygonDisplay.setObjectName(_fromUtf8("polygonDisplay"))
    self.horizontalLayout_2.addWidget(self.polygonDisplay)
    self.addPoly = QtGui.QPushButton(self.widget_2)
    self.addPoly.setEnabled(False)
    sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(self.addPoly.sizePolicy().hasHeightForWidth())
    self.addPoly.setSizePolicy(sizePolicy)
    self.addPoly.setObjectName(_fromUtf8("addPoly"))
    self.horizontalLayout_2.addWidget(self.addPoly)
    self.delPoly = QtGui.QPushButton(self.widget_2)
    self.delPoly.setEnabled(False)
    sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(self.delPoly.sizePolicy().hasHeightForWidth())
    self.delPoly.setSizePolicy(sizePolicy)
    self.delPoly.setObjectName(_fromUtf8("delPoly"))
    self.horizontalLayout_2.addWidget(self.delPoly)
    self.clearPoly = QtGui.QPushButton(self.widget_2)
    self.clearPoly.setEnabled(False)
    sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(self.clearPoly.sizePolicy().hasHeightForWidth())
    self.clearPoly.setSizePolicy(sizePolicy)
    self.clearPoly.setObjectName(_fromUtf8("clearPoly"))
    self.horizontalLayout_2.addWidget(self.clearPoly)
    self.verticalLayout.addWidget(self.widget_2)
    self.polyTable = QtGui.QTableWidget(self.frame)
    self.polyTable.setEnabled(False)
    self.polyTable.setMinimumSize(QtCore.QSize(0, 50))
    self.polyTable.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
    self.polyTable.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
    self.polyTable.setObjectName(_fromUtf8("polyTable"))
    self.polyTable.setColumnCount(8)
    self.polyTable.setRowCount(0)
    item = QtGui.QTableWidgetItem()
    self.polyTable.setHorizontalHeaderItem(0, item)
    item = QtGui.QTableWidgetItem()
    self.polyTable.setHorizontalHeaderItem(1, item)
    item = QtGui.QTableWidgetItem()
    self.polyTable.setHorizontalHeaderItem(2, item)
    item = QtGui.QTableWidgetItem()
    self.polyTable.setHorizontalHeaderItem(3, item)
    item = QtGui.QTableWidgetItem()
    self.polyTable.setHorizontalHeaderItem(4, item)
    item = QtGui.QTableWidgetItem()
    self.polyTable.setHorizontalHeaderItem(5, item)
    item = QtGui.QTableWidgetItem()
    self.polyTable.setHorizontalHeaderItem(6, item)
    item = QtGui.QTableWidgetItem()
    self.polyTable.setHorizontalHeaderItem(7, item)
    self.polyTable.horizontalHeader().setDefaultSectionSize(40)
    self.polyTable.horizontalHeader().setMinimumSectionSize(20)
    self.verticalLayout.addWidget(self.polyTable)
    self.widget = QtGui.QWidget(self.frame)
    self.widget.setObjectName(_fromUtf8("widget"))
    self.gridLayout = QtGui.QGridLayout(self.widget)
    self.gridLayout.setMargin(0)
    self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
    self.horizontalLayout_3 = QtGui.QHBoxLayout()
    self.horizontalLayout_3.setObjectName(_fromUtf8("horizontalLayout_3"))
    self.presumeIofLambda = QtGui.QCheckBox(self.widget)
    self.presumeIofLambda.setObjectName(_fromUtf8("presumeIofLambda"))
    self.horizontalLayout_3.addWidget(self.presumeIofLambda)
    self.label = QtGui.QLabel(self.widget)
    self.label.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
    self.label.setObjectName(_fromUtf8("label"))
    self.horizontalLayout_3.addWidget(self.label)
    self.scaleFactor = QtGui.QDoubleSpinBox(self.widget)
    sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(self.scaleFactor.sizePolicy().hasHeightForWidth())
    self.scaleFactor.setSizePolicy(sizePolicy)
    self.scaleFactor.setDecimals(4)
    self.scaleFactor.setMaximum(100.0)
    self.scaleFactor.setSingleStep(0.05)
    self.scaleFactor.setProperty("value", 1.0)
    self.scaleFactor.setObjectName(_fromUtf8("scaleFactor"))
    self.horizontalLayout_3.addWidget(self.scaleFactor)
    self.gridLayout.addLayout(self.horizontalLayout_3, 0, 0, 1, 1)
    self.verticalLayout.addWidget(self.widget)
    self.horizontalLayout.addWidget(self.splitter)

    self.retranslateUi(Dialog)
    QtCore.QObject.connect(self.polyregionActive, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), self.polyTable.setEnabled)
    QtCore.QObject.connect(self.polyregionActive, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), self.clearPoly.setEnabled)
    QtCore.QObject.connect(self.polyregionActive, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), self.delPoly.setEnabled)
    QtCore.QObject.connect(self.polyregionActive, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), self.addPoly.setEnabled)
    QtCore.QObject.connect(self.addPoly, QtCore.SIGNAL(_fromUtf8("pressed()")), Dialog.addPolygon)
    QtCore.QObject.connect(self.presumeIofLambda, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), Dialog.optionChanged)
    QtCore.QObject.connect(self.delPoly, QtCore.SIGNAL(_fromUtf8("pressed()")), Dialog.delPolygon)
    QtCore.QObject.connect(self.clearPoly, QtCore.SIGNAL(_fromUtf8("pressed()")), Dialog.clearPolygons)
    QtCore.QObject.connect(self.polyTable, QtCore.SIGNAL(_fromUtf8("itemChanged(QTableWidgetItem*)")), Dialog.polygonChanged)
    QtCore.QObject.connect(self.polyregionActive, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), Dialog.optionChanged)
    QtCore.QObject.connect(self.polyregionActive, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), Dialog.drawXTof)
    QtCore.QObject.connect(self.scaleFactor, QtCore.SIGNAL(_fromUtf8("valueChanged(double)")), Dialog.optionChanged)
    QtCore.QMetaObject.connectSlotsByName(Dialog)
    Dialog.setTabOrder(self.polyregionActive, self.addPoly)
    Dialog.setTabOrder(self.addPoly, self.delPoly)
    Dialog.setTabOrder(self.delPoly, self.clearPoly)
    Dialog.setTabOrder(self.clearPoly, self.polyTable)

  def retranslateUi(self, Dialog):
    Dialog.setWindowTitle(QtGui.QApplication.translate("Dialog", "Dialog", None, QtGui.QApplication.UnicodeUTF8))
    self.polyregionActive.setText(QtGui.QApplication.translate("Dialog", "Polygon regions", None, QtGui.QApplication.UnicodeUTF8))
    self.addPoly.setText(QtGui.QApplication.translate("Dialog", "Add", None, QtGui.QApplication.UnicodeUTF8))
    self.delPoly.setText(QtGui.QApplication.translate("Dialog", "Delete", None, QtGui.QApplication.UnicodeUTF8))
    self.clearPoly.setText(QtGui.QApplication.translate("Dialog", "Clear", None, QtGui.QApplication.UnicodeUTF8))
    item = self.polyTable.horizontalHeaderItem(0)
    item.setText(QtGui.QApplication.translate("Dialog", "λ1", None, QtGui.QApplication.UnicodeUTF8))
    item = self.polyTable.horizontalHeaderItem(1)
    item.setText(QtGui.QApplication.translate("Dialog", "x1", None, QtGui.QApplication.UnicodeUTF8))
    item = self.polyTable.horizontalHeaderItem(2)
    item.setText(QtGui.QApplication.translate("Dialog", "λ2", None, QtGui.QApplication.UnicodeUTF8))
    item = self.polyTable.horizontalHeaderItem(3)
    item.setText(QtGui.QApplication.translate("Dialog", "x2", None, QtGui.QApplication.UnicodeUTF8))
    item = self.polyTable.horizontalHeaderItem(4)
    item.setText(QtGui.QApplication.translate("Dialog", "λ3", None, QtGui.QApplication.UnicodeUTF8))
    item = self.polyTable.horizontalHeaderItem(5)
    item.setText(QtGui.QApplication.translate("Dialog", "x3", None, QtGui.QApplication.UnicodeUTF8))
    item = self.polyTable.horizontalHeaderItem(6)
    item.setText(QtGui.QApplication.translate("Dialog", "λ4", None, QtGui.QApplication.UnicodeUTF8))
    item = self.polyTable.horizontalHeaderItem(7)
    item.setText(QtGui.QApplication.translate("Dialog", "x4", None, QtGui.QApplication.UnicodeUTF8))
    self.presumeIofLambda.setText(QtGui.QApplication.translate("Dialog", "Presume BG~I(λ)", None, QtGui.QApplication.UnicodeUTF8))
    self.label.setText(QtGui.QApplication.translate("Dialog", "Scale Backgound", None, QtGui.QApplication.UnicodeUTF8))

from .mplwidget import MPLWidget
