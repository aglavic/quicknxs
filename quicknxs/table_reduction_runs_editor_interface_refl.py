# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'designer/table_reduction_runs_editor.ui'
#
# Created: Wed Mar 11 13:21:51 2015
#      by: PyQt4 UI code generator 4.7.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(841, 781)
        self.verticalLayout_4 = QtGui.QVBoxLayout(Dialog)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.data_groupBox = QtGui.QGroupBox(Dialog)
        self.data_groupBox.setObjectName("data_groupBox")
        self.verticalLayout = QtGui.QVBoxLayout(self.data_groupBox)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.lineEdit = QtGui.QLineEdit(self.data_groupBox)
        self.lineEdit.setObjectName("lineEdit")
        self.horizontalLayout.addWidget(self.lineEdit)
        self.label_2 = QtGui.QLabel(self.data_groupBox)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout.addWidget(self.label_2)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label_3 = QtGui.QLabel(self.data_groupBox)
        self.label_3.setObjectName("label_3")
        self.horizontalLayout_2.addWidget(self.label_3)
        self.oldDataRun = QtGui.QLabel(self.data_groupBox)
        self.oldDataRun.setObjectName("oldDataRun")
        self.horizontalLayout_2.addWidget(self.oldDataRun)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.label_5 = QtGui.QLabel(self.data_groupBox)
        self.label_5.setObjectName("label_5")
        self.horizontalLayout_2.addWidget(self.label_5)
        self.oldDataLambda = QtGui.QLabel(self.data_groupBox)
        self.oldDataLambda.setObjectName("oldDataLambda")
        self.horizontalLayout_2.addWidget(self.oldDataLambda)
        self.oldDataLambdaUnits = QtGui.QLabel(self.data_groupBox)
        self.oldDataLambdaUnits.setObjectName("oldDataLambdaUnits")
        self.horizontalLayout_2.addWidget(self.oldDataLambdaUnits)
        spacerItem1 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem1)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.label_8 = QtGui.QLabel(self.data_groupBox)
        self.label_8.setObjectName("label_8")
        self.horizontalLayout_3.addWidget(self.label_8)
        self.normRun = QtGui.QLabel(self.data_groupBox)
        self.normRun.setObjectName("normRun")
        self.horizontalLayout_3.addWidget(self.normRun)
        spacerItem2 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem2)
        self.label_12 = QtGui.QLabel(self.data_groupBox)
        self.label_12.setObjectName("label_12")
        self.horizontalLayout_3.addWidget(self.label_12)
        self.normLambda = QtGui.QLabel(self.data_groupBox)
        self.normLambda.setObjectName("normLambda")
        self.horizontalLayout_3.addWidget(self.normLambda)
        self.normLambdaUnits = QtGui.QLabel(self.data_groupBox)
        self.normLambdaUnits.setObjectName("normLambdaUnits")
        self.horizontalLayout_3.addWidget(self.normLambdaUnits)
        spacerItem3 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem3)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.verticalLayout_4.addWidget(self.data_groupBox)
        self.norm_groupBox = QtGui.QGroupBox(Dialog)
        self.norm_groupBox.setObjectName("norm_groupBox")
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.norm_groupBox)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.horizontalLayout_4 = QtGui.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.label_14 = QtGui.QLabel(self.norm_groupBox)
        self.label_14.setObjectName("label_14")
        self.horizontalLayout_4.addWidget(self.label_14)
        self.dataRun = QtGui.QLabel(self.norm_groupBox)
        self.dataRun.setObjectName("dataRun")
        self.horizontalLayout_4.addWidget(self.dataRun)
        spacerItem4 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_4.addItem(spacerItem4)
        self.label_18 = QtGui.QLabel(self.norm_groupBox)
        self.label_18.setObjectName("label_18")
        self.horizontalLayout_4.addWidget(self.label_18)
        self.dataLambda = QtGui.QLabel(self.norm_groupBox)
        self.dataLambda.setObjectName("dataLambda")
        self.horizontalLayout_4.addWidget(self.dataLambda)
        self.dataLambdaUnits = QtGui.QLabel(self.norm_groupBox)
        self.dataLambdaUnits.setObjectName("dataLambdaUnits")
        self.horizontalLayout_4.addWidget(self.dataLambdaUnits)
        spacerItem5 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_4.addItem(spacerItem5)
        self.verticalLayout_2.addLayout(self.horizontalLayout_4)
        self.lineEdit_2 = QtGui.QLineEdit(self.norm_groupBox)
        self.lineEdit_2.setStatusTip("")
        self.lineEdit_2.setWhatsThis("")
        self.lineEdit_2.setAccessibleName("")
        self.lineEdit_2.setAccessibleDescription("")
        self.lineEdit_2.setInputMask("")
        self.lineEdit_2.setText("")
        self.lineEdit_2.setObjectName("lineEdit_2")
        self.verticalLayout_2.addWidget(self.lineEdit_2)
        self.horizontalLayout_5 = QtGui.QHBoxLayout()
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.label_21 = QtGui.QLabel(self.norm_groupBox)
        self.label_21.setObjectName("label_21")
        self.horizontalLayout_5.addWidget(self.label_21)
        self.oldNormRun = QtGui.QLabel(self.norm_groupBox)
        self.oldNormRun.setObjectName("oldNormRun")
        self.horizontalLayout_5.addWidget(self.oldNormRun)
        spacerItem6 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_5.addItem(spacerItem6)
        self.label_15 = QtGui.QLabel(self.norm_groupBox)
        self.label_15.setObjectName("label_15")
        self.horizontalLayout_5.addWidget(self.label_15)
        self.oldNormLambda = QtGui.QLabel(self.norm_groupBox)
        self.oldNormLambda.setObjectName("oldNormLambda")
        self.horizontalLayout_5.addWidget(self.oldNormLambda)
        self.oldNormLambdaUnits = QtGui.QLabel(self.norm_groupBox)
        self.oldNormLambdaUnits.setObjectName("oldNormLambdaUnits")
        self.horizontalLayout_5.addWidget(self.oldNormLambdaUnits)
        spacerItem7 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_5.addItem(spacerItem7)
        self.verticalLayout_2.addLayout(self.horizontalLayout_5)
        self.verticalLayout_4.addWidget(self.norm_groupBox)
        self.groupBox_3 = QtGui.QGroupBox(Dialog)
        self.groupBox_3.setObjectName("groupBox_3")
        self.verticalLayout_3 = QtGui.QVBoxLayout(self.groupBox_3)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.tableWidget = QtGui.QTableWidget(self.groupBox_3)
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setColumnCount(4)
        self.tableWidget.setRowCount(0)
        item = QtGui.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(0, item)
        item = QtGui.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(1, item)
        item = QtGui.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(2, item)
        item = QtGui.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(3, item)
        self.verticalLayout_3.addWidget(self.tableWidget)
        self.verticalLayout_4.addWidget(self.groupBox_3)
        self.horizontalLayout_6 = QtGui.QHBoxLayout()
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.pushButton = QtGui.QPushButton(Dialog)
        self.pushButton.setObjectName("pushButton")
        self.horizontalLayout_6.addWidget(self.pushButton)
        spacerItem8 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_6.addItem(spacerItem8)
        self.pushButton_2 = QtGui.QPushButton(Dialog)
        self.pushButton_2.setObjectName("pushButton_2")
        self.horizontalLayout_6.addWidget(self.pushButton_2)
        self.pushButton_3 = QtGui.QPushButton(Dialog)
        self.pushButton_3.setEnabled(False)
        self.pushButton_3.setObjectName("pushButton_3")
        self.horizontalLayout_6.addWidget(self.pushButton_3)
        self.verticalLayout_4.addLayout(self.horizontalLayout_6)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QtGui.QApplication.translate("Dialog", "Dialog", None, QtGui.QApplication.UnicodeUTF8))
        self.data_groupBox.setTitle(QtGui.QApplication.translate("Dialog", "New Data Run(s)", None, QtGui.QApplication.UnicodeUTF8))
        self.lineEdit.setToolTip(QtGui.QApplication.translate("Dialog", "Enter Data Runs and Hit ENTER", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("Dialog", "ex: 10,15-20", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("Dialog", "Old data run(s):", None, QtGui.QApplication.UnicodeUTF8))
        self.oldDataRun.setText(QtGui.QApplication.translate("Dialog", "13445,45454,3454545", None, QtGui.QApplication.UnicodeUTF8))
        self.label_5.setText(QtGui.QApplication.translate("Dialog", "Lambda requested:", None, QtGui.QApplication.UnicodeUTF8))
        self.oldDataLambda.setText(QtGui.QApplication.translate("Dialog", "10.5", None, QtGui.QApplication.UnicodeUTF8))
        self.oldDataLambdaUnits.setText(QtGui.QApplication.translate("Dialog", "Angstroms", None, QtGui.QApplication.UnicodeUTF8))
        self.label_8.setText(QtGui.QApplication.translate("Dialog", "Normalization run:", None, QtGui.QApplication.UnicodeUTF8))
        self.normRun.setText(QtGui.QApplication.translate("Dialog", "4545545", None, QtGui.QApplication.UnicodeUTF8))
        self.label_12.setText(QtGui.QApplication.translate("Dialog", "Lambda requested:", None, QtGui.QApplication.UnicodeUTF8))
        self.normLambda.setText(QtGui.QApplication.translate("Dialog", "10.5", None, QtGui.QApplication.UnicodeUTF8))
        self.normLambdaUnits.setText(QtGui.QApplication.translate("Dialog", "Angstroms", None, QtGui.QApplication.UnicodeUTF8))
        self.norm_groupBox.setTitle(QtGui.QApplication.translate("Dialog", "New Normalization Run", None, QtGui.QApplication.UnicodeUTF8))
        self.label_14.setText(QtGui.QApplication.translate("Dialog", "Data run(s):", None, QtGui.QApplication.UnicodeUTF8))
        self.dataRun.setText(QtGui.QApplication.translate("Dialog", "4545545,4545454,45454", None, QtGui.QApplication.UnicodeUTF8))
        self.label_18.setText(QtGui.QApplication.translate("Dialog", "Lambda requested:", None, QtGui.QApplication.UnicodeUTF8))
        self.dataLambda.setText(QtGui.QApplication.translate("Dialog", "10.5", None, QtGui.QApplication.UnicodeUTF8))
        self.dataLambdaUnits.setText(QtGui.QApplication.translate("Dialog", "Angstroms", None, QtGui.QApplication.UnicodeUTF8))
        self.lineEdit_2.setToolTip(QtGui.QApplication.translate("Dialog", "Enter Normalization Run and Hit ENTER", None, QtGui.QApplication.UnicodeUTF8))
        self.label_21.setText(QtGui.QApplication.translate("Dialog", "Old normalization  run:", None, QtGui.QApplication.UnicodeUTF8))
        self.oldNormRun.setText(QtGui.QApplication.translate("Dialog", "13445", None, QtGui.QApplication.UnicodeUTF8))
        self.label_15.setText(QtGui.QApplication.translate("Dialog", "Lambda requested:", None, QtGui.QApplication.UnicodeUTF8))
        self.oldNormLambda.setText(QtGui.QApplication.translate("Dialog", "10.5", None, QtGui.QApplication.UnicodeUTF8))
        self.oldNormLambdaUnits.setText(QtGui.QApplication.translate("Dialog", "Angstroms", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox_3.setTitle(QtGui.QApplication.translate("Dialog", "Checking Matching Lambdas", None, QtGui.QApplication.UnicodeUTF8))
        self.tableWidget.horizontalHeaderItem(0).setText(QtGui.QApplication.translate("Dialog", "Data", None, QtGui.QApplication.UnicodeUTF8))
        self.tableWidget.horizontalHeaderItem(1).setText(QtGui.QApplication.translate("Dialog", "Lambda Requested", None, QtGui.QApplication.UnicodeUTF8))
        self.tableWidget.horizontalHeaderItem(2).setText(QtGui.QApplication.translate("Dialog", "Normalization", None, QtGui.QApplication.UnicodeUTF8))
        self.tableWidget.horizontalHeaderItem(3).setText(QtGui.QApplication.translate("Dialog", "Lambda Requested", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton.setText(QtGui.QApplication.translate("Dialog", "CANCEL", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton_2.setText(QtGui.QApplication.translate("Dialog", "VALIDATE", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton_3.setText(QtGui.QApplication.translate("Dialog", "OK", None, QtGui.QApplication.UnicodeUTF8))

