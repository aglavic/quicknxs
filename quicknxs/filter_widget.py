# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'designer/filter_widget.ui'
#
# Created by: PyQt5 UI code generator 5.7
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_FilterWidget(object):
  def setupUi(self, FilterWidget):
    FilterWidget.setObjectName("FilterWidget")
    FilterWidget.resize(484, 69)
    self.verticalLayout = QtWidgets.QVBoxLayout(FilterWidget)
    self.verticalLayout.setContentsMargins(0, 0, 0, 0)
    self.verticalLayout.setObjectName("verticalLayout")
    self.horizontalLayout = QtWidgets.QHBoxLayout()
    self.horizontalLayout.setObjectName("horizontalLayout")
    self.label = QtWidgets.QLabel(FilterWidget)
    self.label.setObjectName("label")
    self.horizontalLayout.addWidget(self.label)
    self.filterColumn = QtWidgets.QComboBox(FilterWidget)
    self.filterColumn.setObjectName("filterColumn")
    self.horizontalLayout.addWidget(self.filterColumn)
    self.numberCompare = QtWidgets.QComboBox(FilterWidget)
    self.numberCompare.setObjectName("numberCompare")
    self.numberCompare.addItem("")
    self.numberCompare.addItem("")
    self.numberCompare.addItem("")
    self.numberCompare.addItem("")
    self.numberCompare.addItem("")
    self.numberCompare.addItem("")
    self.horizontalLayout.addWidget(self.numberCompare)
    self.strCompare = QtWidgets.QComboBox(FilterWidget)
    self.strCompare.setObjectName("strCompare")
    self.strCompare.addItem("")
    self.strCompare.addItem("")
    self.strCompare.addItem("")
    self.horizontalLayout.addWidget(self.strCompare)
    self.filterEntry = QtWidgets.QLineEdit(FilterWidget)
    self.filterEntry.setObjectName("filterEntry")
    self.horizontalLayout.addWidget(self.filterEntry)
    self.pushButton = QtWidgets.QPushButton(FilterWidget)
    self.pushButton.setObjectName("pushButton")
    self.horizontalLayout.addWidget(self.pushButton)
    self.verticalLayout.addLayout(self.horizontalLayout)
    self.activeFilters = QtWidgets.QFrame(FilterWidget)
    self.activeFilters.setFrameShape(QtWidgets.QFrame.StyledPanel)
    self.activeFilters.setFrameShadow(QtWidgets.QFrame.Raised)
    self.activeFilters.setObjectName("activeFilters")
    self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.activeFilters)
    self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
    self.verticalLayout_2.setObjectName("verticalLayout_2")
    self.label_2 = QtWidgets.QLabel(self.activeFilters)
    self.label_2.setObjectName("label_2")
    self.verticalLayout_2.addWidget(self.label_2)
    self.verticalLayout.addWidget(self.activeFilters)

    self.retranslateUi(FilterWidget)
    self.numberCompare.setCurrentIndex(5)
    self.strCompare.setCurrentIndex(1)
    self.pushButton.pressed.connect(FilterWidget.addFilter)
    self.filterColumn.currentIndexChanged['int'].connect(FilterWidget.toggleColumn)
    self.filterEntry.textChanged['QString'].connect(FilterWidget.checkEntry)
    self.filterEntry.returnPressed.connect(FilterWidget.addFilter)
    QtCore.QMetaObject.connectSlotsByName(FilterWidget)

  def retranslateUi(self, FilterWidget):
    _translate = QtCore.QCoreApplication.translate
    FilterWidget.setWindowTitle(_translate("FilterWidget", "Form"))
    self.label.setText(_translate("FilterWidget", "Column"))
    self.numberCompare.setItemText(0, _translate("FilterWidget", "="))
    self.numberCompare.setItemText(1, _translate("FilterWidget", "<"))
    self.numberCompare.setItemText(2, _translate("FilterWidget", ">"))
    self.numberCompare.setItemText(3, _translate("FilterWidget", "≤"))
    self.numberCompare.setItemText(4, _translate("FilterWidget", "≥"))
    self.numberCompare.setItemText(5, _translate("FilterWidget", "≈"))
    self.strCompare.setItemText(0, _translate("FilterWidget", "="))
    self.strCompare.setItemText(1, _translate("FilterWidget", "contains"))
    self.strCompare.setItemText(2, _translate("FilterWidget", "RegEx"))
    self.pushButton.setText(_translate("FilterWidget", "Add"))
    self.label_2.setText(_translate("FilterWidget", "Active:"))

