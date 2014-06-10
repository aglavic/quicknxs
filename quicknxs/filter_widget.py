# -*- coding: utf-8 -*-
#@PydevCodeAnalysisIgnore

# Form implementation generated from reading ui file 'designer/filter_widget.ui'
#
# Created: Mon Jun  9 14:36:47 2014
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

class Ui_FilterWidget(object):
  def setupUi(self, FilterWidget):
    FilterWidget.setObjectName(_fromUtf8("FilterWidget"))
    FilterWidget.resize(484, 69)
    self.verticalLayout = QtGui.QVBoxLayout(FilterWidget)
    self.verticalLayout.setMargin(0)
    self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
    self.horizontalLayout = QtGui.QHBoxLayout()
    self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
    self.label = QtGui.QLabel(FilterWidget)
    self.label.setObjectName(_fromUtf8("label"))
    self.horizontalLayout.addWidget(self.label)
    self.filterColumn = QtGui.QComboBox(FilterWidget)
    self.filterColumn.setObjectName(_fromUtf8("filterColumn"))
    self.horizontalLayout.addWidget(self.filterColumn)
    self.numberCompare = QtGui.QComboBox(FilterWidget)
    self.numberCompare.setObjectName(_fromUtf8("numberCompare"))
    self.numberCompare.addItem(_fromUtf8(""))
    self.numberCompare.addItem(_fromUtf8(""))
    self.numberCompare.addItem(_fromUtf8(""))
    self.numberCompare.addItem(_fromUtf8(""))
    self.numberCompare.addItem(_fromUtf8(""))
    self.numberCompare.addItem(_fromUtf8(""))
    self.horizontalLayout.addWidget(self.numberCompare)
    self.strCompare = QtGui.QComboBox(FilterWidget)
    self.strCompare.setObjectName(_fromUtf8("strCompare"))
    self.strCompare.addItem(_fromUtf8(""))
    self.strCompare.addItem(_fromUtf8(""))
    self.strCompare.addItem(_fromUtf8(""))
    self.horizontalLayout.addWidget(self.strCompare)
    self.filterEntry = QtGui.QLineEdit(FilterWidget)
    self.filterEntry.setObjectName(_fromUtf8("filterEntry"))
    self.horizontalLayout.addWidget(self.filterEntry)
    self.pushButton = QtGui.QPushButton(FilterWidget)
    self.pushButton.setObjectName(_fromUtf8("pushButton"))
    self.horizontalLayout.addWidget(self.pushButton)
    self.verticalLayout.addLayout(self.horizontalLayout)
    self.activeFilters = QtGui.QFrame(FilterWidget)
    self.activeFilters.setFrameShape(QtGui.QFrame.StyledPanel)
    self.activeFilters.setFrameShadow(QtGui.QFrame.Raised)
    self.activeFilters.setObjectName(_fromUtf8("activeFilters"))
    self.verticalLayout_2 = QtGui.QVBoxLayout(self.activeFilters)
    self.verticalLayout_2.setMargin(0)
    self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
    self.label_2 = QtGui.QLabel(self.activeFilters)
    self.label_2.setObjectName(_fromUtf8("label_2"))
    self.verticalLayout_2.addWidget(self.label_2)
    self.verticalLayout.addWidget(self.activeFilters)

    self.retranslateUi(FilterWidget)
    self.numberCompare.setCurrentIndex(5)
    self.strCompare.setCurrentIndex(1)
    QtCore.QObject.connect(self.pushButton, QtCore.SIGNAL(_fromUtf8("pressed()")), FilterWidget.addFilter)
    QtCore.QObject.connect(self.filterColumn, QtCore.SIGNAL(_fromUtf8("currentIndexChanged(int)")), FilterWidget.toggleColumn)
    QtCore.QObject.connect(self.filterEntry, QtCore.SIGNAL(_fromUtf8("textChanged(QString)")), FilterWidget.checkEntry)
    QtCore.QObject.connect(self.filterEntry, QtCore.SIGNAL(_fromUtf8("returnPressed()")), FilterWidget.addFilter)
    QtCore.QMetaObject.connectSlotsByName(FilterWidget)

  def retranslateUi(self, FilterWidget):
    FilterWidget.setWindowTitle(_translate("FilterWidget", "Form", None))
    self.label.setText(_translate("FilterWidget", "Column", None))
    self.numberCompare.setItemText(0, _translate("FilterWidget", "=", None))
    self.numberCompare.setItemText(1, _translate("FilterWidget", "<", None))
    self.numberCompare.setItemText(2, _translate("FilterWidget", ">", None))
    self.numberCompare.setItemText(3, _translate("FilterWidget", "≤", None))
    self.numberCompare.setItemText(4, _translate("FilterWidget", "≥", None))
    self.numberCompare.setItemText(5, _translate("FilterWidget", "≈", None))
    self.strCompare.setItemText(0, _translate("FilterWidget", "=", None))
    self.strCompare.setItemText(1, _translate("FilterWidget", "contains", None))
    self.strCompare.setItemText(2, _translate("FilterWidget", "RegEx", None))
    self.pushButton.setText(_translate("FilterWidget", "Add", None))
    self.label_2.setText(_translate("FilterWidget", "Active:", None))

