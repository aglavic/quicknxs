# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'designer/output_reduced_data_dialog.ui'
#
# Created: Tue Dec 23 15:01:26 2014
#      by: PyQt4 UI code generator 4.7.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(406, 360)
        self.verticalLayout_2 = QtGui.QVBoxLayout(Dialog)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.output4thColumnFlag = QtGui.QCheckBox(Dialog)
        self.output4thColumnFlag.setObjectName("output4thColumnFlag")
        self.verticalLayout.addWidget(self.output4thColumnFlag)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label_3 = QtGui.QLabel(Dialog)
        self.label_3.setObjectName("label_3")
        self.horizontalLayout.addWidget(self.label_3)
        self.dq0Value = QtGui.QLineEdit(Dialog)
        self.dq0Value.setObjectName("dq0Value")
        self.horizontalLayout.addWidget(self.dq0Value)
        self.label_4 = QtGui.QLabel(Dialog)
        self.label_4.setObjectName("label_4")
        self.horizontalLayout.addWidget(self.label_4)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label_5 = QtGui.QLabel(Dialog)
        self.label_5.setObjectName("label_5")
        self.horizontalLayout_2.addWidget(self.label_5)
        self.dQoverQvalue = QtGui.QLineEdit(Dialog)
        self.dQoverQvalue.setObjectName("dQoverQvalue")
        self.horizontalLayout_2.addWidget(self.dQoverQvalue)
        spacerItem1 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem1)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.groupBox_3 = QtGui.QGroupBox(Dialog)
        self.groupBox_3.setObjectName("groupBox_3")
        self.usingLessErrorValueFlag = QtGui.QRadioButton(self.groupBox_3)
        self.usingLessErrorValueFlag.setGeometry(QtCore.QRect(25, 24, 199, 22))
        self.usingLessErrorValueFlag.setChecked(True)
        self.usingLessErrorValueFlag.setObjectName("usingLessErrorValueFlag")
        self.usingMeanValueFalg = QtGui.QRadioButton(self.groupBox_3)
        self.usingMeanValueFalg.setGeometry(QtCore.QRect(25, 51, 199, 22))
        self.usingMeanValueFalg.setObjectName("usingMeanValueFalg")
        self.verticalLayout.addWidget(self.groupBox_3)
        self.createAsciiButton = QtGui.QPushButton(Dialog)
        self.createAsciiButton.setObjectName("createAsciiButton")
        self.verticalLayout.addWidget(self.createAsciiButton)
        self.verticalLayout_2.addLayout(self.verticalLayout)

        self.retranslateUi(Dialog)
        QtCore.QObject.connect(self.createAsciiButton, QtCore.SIGNAL("clicked()"), Dialog.create_reduce_ascii_button_event)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QtGui.QApplication.translate("Dialog", "Export ASCII", None, QtGui.QApplication.UnicodeUTF8))
        self.output4thColumnFlag.setText(QtGui.QApplication.translate("Dialog", "with 4th column (precision)", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("Dialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Sans\'; font-size:10pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">dQ<span style=\" vertical-align:sub;\">0</span></p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.dq0Value.setText(QtGui.QApplication.translate("Dialog", "0.0009", None, QtGui.QApplication.UnicodeUTF8))
        self.label_4.setText(QtGui.QApplication.translate("Dialog", "1/Å", None, QtGui.QApplication.UnicodeUTF8))
        self.label_5.setText(QtGui.QApplication.translate("Dialog", "ΔQ/Q", None, QtGui.QApplication.UnicodeUTF8))
        self.dQoverQvalue.setText(QtGui.QApplication.translate("Dialog", "0.01", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox_3.setTitle(QtGui.QApplication.translate("Dialog", "  How to treat overlap values", None, QtGui.QApplication.UnicodeUTF8))
        self.usingLessErrorValueFlag.setText(QtGui.QApplication.translate("Dialog", "use lowest error value", None, QtGui.QApplication.UnicodeUTF8))
        self.usingMeanValueFalg.setText(QtGui.QApplication.translate("Dialog", "use mean value", None, QtGui.QApplication.UnicodeUTF8))
        self.createAsciiButton.setText(QtGui.QApplication.translate("Dialog", "Create Reduce ASCII ...", None, QtGui.QApplication.UnicodeUTF8))

