# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'designer/compare_widget.ui'
#
# Created by: PyQt5 UI code generator 5.7
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Form(object):
  def setupUi(self, Form):
    Form.setObjectName("Form")
    Form.resize(851, 718)
    self.verticalLayout = QtWidgets.QVBoxLayout(Form)
    self.verticalLayout.setObjectName("verticalLayout")
    self.splitter = QtWidgets.QSplitter(Form)
    self.splitter.setOrientation(QtCore.Qt.Vertical)
    self.splitter.setObjectName("splitter")
    self.frame_7 = QtWidgets.QFrame(self.splitter)
    sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(2)
    sizePolicy.setHeightForWidth(self.frame_7.sizePolicy().hasHeightForWidth())
    self.frame_7.setSizePolicy(sizePolicy)
    self.frame_7.setFrameShape(QtWidgets.QFrame.StyledPanel)
    self.frame_7.setFrameShadow(QtWidgets.QFrame.Sunken)
    self.frame_7.setObjectName("frame_7")
    self.verticalLayout_6 = QtWidgets.QVBoxLayout(self.frame_7)
    self.verticalLayout_6.setObjectName("verticalLayout_6")
    self.comparePlot = MPLWidget(self.frame_7)
    self.comparePlot.setObjectName("comparePlot")
    self.verticalLayout_6.addWidget(self.comparePlot)
    self.widget_6 = QtWidgets.QWidget(self.splitter)
    sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(self.widget_6.sizePolicy().hasHeightForWidth())
    self.widget_6.setSizePolicy(sizePolicy)
    self.widget_6.setObjectName("widget_6")
    self.horizontalLayout_15 = QtWidgets.QHBoxLayout(self.widget_6)
    self.horizontalLayout_15.setContentsMargins(0, 0, 0, 0)
    self.horizontalLayout_15.setObjectName("horizontalLayout_15")
    self.compareList = QtWidgets.QTableWidget(self.widget_6)
    self.compareList.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
    self.compareList.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectItems)
    self.compareList.setObjectName("compareList")
    self.compareList.setColumnCount(3)
    self.compareList.setRowCount(0)
    item = QtWidgets.QTableWidgetItem()
    self.compareList.setHorizontalHeaderItem(0, item)
    item = QtWidgets.QTableWidgetItem()
    self.compareList.setHorizontalHeaderItem(1, item)
    item = QtWidgets.QTableWidgetItem()
    self.compareList.setHorizontalHeaderItem(2, item)
    self.horizontalLayout_15.addWidget(self.compareList)
    self.frame_8 = QtWidgets.QFrame(self.widget_6)
    self.frame_8.setFrameShape(QtWidgets.QFrame.StyledPanel)
    self.frame_8.setFrameShadow(QtWidgets.QFrame.Raised)
    self.frame_8.setObjectName("frame_8")
    self.verticalLayout_10 = QtWidgets.QVBoxLayout(self.frame_8)
    self.verticalLayout_10.setObjectName("verticalLayout_10")
    self.pushButton = QtWidgets.QPushButton(self.frame_8)
    self.pushButton.setObjectName("pushButton")
    self.verticalLayout_10.addWidget(self.pushButton)
    self.pushButton_2 = QtWidgets.QPushButton(self.frame_8)
    self.pushButton_2.setObjectName("pushButton_2")
    self.verticalLayout_10.addWidget(self.pushButton_2)
    self.horizontalLayout_15.addWidget(self.frame_8)
    self.verticalLayout.addWidget(self.splitter)

    self.retranslateUi(Form)
    self.pushButton_2.pressed.connect(Form.open_file)
    self.pushButton.pressed.connect(Form.clear_plot)
    self.compareList.itemChanged['QTableWidgetItem*'].connect(Form.draw)
    self.compareList.cellDoubleClicked['int','int'].connect(Form.edit_cell)
    QtCore.QMetaObject.connectSlotsByName(Form)
    Form.setTabOrder(self.compareList, self.pushButton_2)
    Form.setTabOrder(self.pushButton_2, self.pushButton)

  def retranslateUi(self, Form):
    _translate = QtCore.QCoreApplication.translate
    Form.setWindowTitle(_translate("Form", "Form"))
    item = self.compareList.horizontalHeaderItem(0)
    item.setText(_translate("Form", "File"))
    item = self.compareList.horizontalHeaderItem(1)
    item.setText(_translate("Form", "Color"))
    item = self.compareList.horizontalHeaderItem(2)
    item.setText(_translate("Form", "Label"))
    self.pushButton.setText(_translate("Form", "Clear"))
    self.pushButton_2.setText(_translate("Form", "Open"))

from .mplwidget import MPLWidget
