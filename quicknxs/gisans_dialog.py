# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'designer/gisans_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.7
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
  def setupUi(self, Dialog):
    Dialog.setObjectName("Dialog")
    Dialog.resize(600, 600)
    self.verticalLayout_2 = QtWidgets.QVBoxLayout(Dialog)
    self.verticalLayout_2.setObjectName("verticalLayout_2")
    self.splitter = QtWidgets.QSplitter(Dialog)
    self.splitter.setOrientation(QtCore.Qt.Vertical)
    self.splitter.setObjectName("splitter")
    self.widget_3 = QtWidgets.QWidget(self.splitter)
    sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(2)
    sizePolicy.setHeightForWidth(self.widget_3.sizePolicy().hasHeightForWidth())
    self.widget_3.setSizePolicy(sizePolicy)
    self.widget_3.setObjectName("widget_3")
    self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.widget_3)
    self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
    self.horizontalLayout_2.setObjectName("horizontalLayout_2")
    self.verticalLayout_5 = QtWidgets.QVBoxLayout()
    self.verticalLayout_5.setObjectName("verticalLayout_5")
    self.label_9 = QtWidgets.QLabel(self.widget_3)
    sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(self.label_9.sizePolicy().hasHeightForWidth())
    self.label_9.setSizePolicy(sizePolicy)
    self.label_9.setAlignment(QtCore.Qt.AlignCenter)
    self.label_9.setObjectName("label_9")
    self.verticalLayout_5.addWidget(self.label_9)
    self.widget_4 = QtWidgets.QWidget(self.widget_3)
    sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(self.widget_4.sizePolicy().hasHeightForWidth())
    self.widget_4.setSizePolicy(sizePolicy)
    self.widget_4.setObjectName("widget_4")
    self.horizontalLayout_3 = QtWidgets.QHBoxLayout(self.widget_4)
    self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
    self.horizontalLayout_3.setObjectName("horizontalLayout_3")
    self.label_11 = QtWidgets.QLabel(self.widget_4)
    self.label_11.setObjectName("label_11")
    self.horizontalLayout_3.addWidget(self.label_11)
    self.iMax = QtWidgets.QDoubleSpinBox(self.widget_4)
    self.iMax.setMinimum(-30.0)
    self.iMax.setMaximum(30.0)
    self.iMax.setSingleStep(0.05)
    self.iMax.setObjectName("iMax")
    self.horizontalLayout_3.addWidget(self.iMax)
    self.verticalLayout_5.addWidget(self.widget_4)
    self.label_10 = QtWidgets.QLabel(self.widget_3)
    sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(self.label_10.sizePolicy().hasHeightForWidth())
    self.label_10.setSizePolicy(sizePolicy)
    self.label_10.setAlignment(QtCore.Qt.AlignCenter)
    self.label_10.setObjectName("label_10")
    self.verticalLayout_5.addWidget(self.label_10)
    self.widget_5 = QtWidgets.QWidget(self.widget_3)
    self.widget_5.setObjectName("widget_5")
    self.horizontalLayout_4 = QtWidgets.QHBoxLayout(self.widget_5)
    self.horizontalLayout_4.setContentsMargins(0, 0, 0, 0)
    self.horizontalLayout_4.setObjectName("horizontalLayout_4")
    self.label_12 = QtWidgets.QLabel(self.widget_5)
    self.label_12.setObjectName("label_12")
    self.horizontalLayout_4.addWidget(self.label_12)
    self.iMin = QtWidgets.QDoubleSpinBox(self.widget_5)
    self.iMin.setMinimum(-30.0)
    self.iMin.setMaximum(30.0)
    self.iMin.setSingleStep(0.05)
    self.iMin.setProperty("value", -6.0)
    self.iMin.setObjectName("iMin")
    self.horizontalLayout_4.addWidget(self.iMin)
    self.verticalLayout_5.addWidget(self.widget_5)
    self.plotShowList = QtWidgets.QListWidget(self.widget_3)
    sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Expanding)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(self.plotShowList.sizePolicy().hasHeightForWidth())
    self.plotShowList.setSizePolicy(sizePolicy)
    self.plotShowList.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
    self.plotShowList.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
    self.plotShowList.setProperty("showDropIndicator", False)
    self.plotShowList.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
    self.plotShowList.setObjectName("plotShowList")
    self.verticalLayout_5.addWidget(self.plotShowList)
    self.horizontalLayout_2.addLayout(self.verticalLayout_5)
    self.scrollArea = QtWidgets.QScrollArea(self.widget_3)
    sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(2)
    sizePolicy.setHeightForWidth(self.scrollArea.sizePolicy().hasHeightForWidth())
    self.scrollArea.setSizePolicy(sizePolicy)
    self.scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
    self.scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
    self.scrollArea.setWidgetResizable(True)
    self.scrollArea.setObjectName("scrollArea")
    self.resultImageArea = QtWidgets.QWidget()
    self.resultImageArea.setGeometry(QtCore.QRect(0, 0, 447, 208))
    sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Preferred)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(self.resultImageArea.sizePolicy().hasHeightForWidth())
    self.resultImageArea.setSizePolicy(sizePolicy)
    self.resultImageArea.setObjectName("resultImageArea")
    self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.resultImageArea)
    self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
    self.verticalLayout_4.setObjectName("verticalLayout_4")
    self.resultImageLayout = QtWidgets.QHBoxLayout()
    self.resultImageLayout.setObjectName("resultImageLayout")
    self.verticalLayout_4.addLayout(self.resultImageLayout)
    self.scrollArea.setWidget(self.resultImageArea)
    self.horizontalLayout_2.addWidget(self.scrollArea)
    self.widget_2 = QtWidgets.QWidget(self.splitter)
    sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(self.widget_2.sizePolicy().hasHeightForWidth())
    self.widget_2.setSizePolicy(sizePolicy)
    self.widget_2.setObjectName("widget_2")
    self.horizontalLayout = QtWidgets.QHBoxLayout(self.widget_2)
    self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
    self.horizontalLayout.setObjectName("horizontalLayout")
    self.frame = QtWidgets.QFrame(self.widget_2)
    sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
    sizePolicy.setHorizontalStretch(2)
    sizePolicy.setVerticalStretch(1)
    sizePolicy.setHeightForWidth(self.frame.sizePolicy().hasHeightForWidth())
    self.frame.setSizePolicy(sizePolicy)
    self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
    self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
    self.frame.setObjectName("frame")
    self.verticalLayout = QtWidgets.QVBoxLayout(self.frame)
    self.verticalLayout.setObjectName("verticalLayout")
    self.lambdaPlot = MPLWidget(self.frame)
    self.lambdaPlot.setObjectName("lambdaPlot")
    self.verticalLayout.addWidget(self.lambdaPlot)
    self.horizontalLayout.addWidget(self.frame)
    self.verticalWidget = QtWidgets.QWidget(self.widget_2)
    sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
    sizePolicy.setHorizontalStretch(1)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(self.verticalWidget.sizePolicy().hasHeightForWidth())
    self.verticalWidget.setSizePolicy(sizePolicy)
    self.verticalWidget.setObjectName("verticalWidget")
    self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.verticalWidget)
    self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
    self.verticalLayout_3.setObjectName("verticalLayout_3")
    self.widget = QtWidgets.QWidget(self.verticalWidget)
    sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
    sizePolicy.setHorizontalStretch(1)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(self.widget.sizePolicy().hasHeightForWidth())
    self.widget.setSizePolicy(sizePolicy)
    self.widget.setObjectName("widget")
    self.gridLayout = QtWidgets.QGridLayout(self.widget)
    self.gridLayout.setContentsMargins(0, 0, 0, 0)
    self.gridLayout.setObjectName("gridLayout")
    self.gridQy = QtWidgets.QSpinBox(self.widget)
    self.gridQy.setMinimum(20)
    self.gridQy.setMaximum(300)
    self.gridQy.setSingleStep(10)
    self.gridQy.setProperty("value", 50)
    self.gridQy.setObjectName("gridQy")
    self.gridLayout.addWidget(self.gridQy, 0, 4, 1, 1)
    self.numberSlices = QtWidgets.QSpinBox(self.widget)
    sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
    sizePolicy.setHorizontalStretch(1)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(self.numberSlices.sizePolicy().hasHeightForWidth())
    self.numberSlices.setSizePolicy(sizePolicy)
    self.numberSlices.setMinimum(1)
    self.numberSlices.setMaximum(50)
    self.numberSlices.setProperty("value", 4)
    self.numberSlices.setObjectName("numberSlices")
    self.gridLayout.addWidget(self.numberSlices, 5, 4, 1, 1)
    self.label_3 = QtWidgets.QLabel(self.widget)
    self.label_3.setObjectName("label_3")
    self.gridLayout.addWidget(self.label_3, 3, 5, 1, 1)
    self.projectionMethod = QtWidgets.QComboBox(self.widget)
    self.projectionMethod.setObjectName("projectionMethod")
    self.projectionMethod.addItem("")
    self.gridLayout.addWidget(self.projectionMethod, 7, 4, 1, 2)
    self.lambdaMin = QtWidgets.QDoubleSpinBox(self.widget)
    sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
    sizePolicy.setHorizontalStretch(1)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(self.lambdaMin.sizePolicy().hasHeightForWidth())
    self.lambdaMin.setSizePolicy(sizePolicy)
    self.lambdaMin.setDecimals(3)
    self.lambdaMin.setMinimum(1.9)
    self.lambdaMin.setMaximum(9.0)
    self.lambdaMin.setSingleStep(0.025)
    self.lambdaMin.setProperty("value", 2.0)
    self.lambdaMin.setObjectName("lambdaMin")
    self.gridLayout.addWidget(self.lambdaMin, 3, 4, 1, 1)
    spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
    self.gridLayout.addItem(spacerItem, 9, 4, 1, 1)
    self.label_4 = QtWidgets.QLabel(self.widget)
    self.label_4.setObjectName("label_4")
    self.gridLayout.addWidget(self.label_4, 4, 5, 1, 1)
    self.lambdaMax = QtWidgets.QDoubleSpinBox(self.widget)
    sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
    sizePolicy.setHorizontalStretch(1)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(self.lambdaMax.sizePolicy().hasHeightForWidth())
    self.lambdaMax.setSizePolicy(sizePolicy)
    self.lambdaMax.setDecimals(3)
    self.lambdaMax.setMinimum(1.9)
    self.lambdaMax.setMaximum(20.0)
    self.lambdaMax.setSingleStep(0.025)
    self.lambdaMax.setProperty("value", 5.0)
    self.lambdaMax.setObjectName("lambdaMax")
    self.gridLayout.addWidget(self.lambdaMax, 4, 4, 1, 1)
    self.line = QtWidgets.QFrame(self.widget)
    self.line.setFrameShape(QtWidgets.QFrame.HLine)
    self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
    self.line.setObjectName("line")
    self.gridLayout.addWidget(self.line, 2, 2, 1, 1)
    self.label_8 = QtWidgets.QLabel(self.widget)
    self.label_8.setObjectName("label_8")
    self.gridLayout.addWidget(self.label_8, 1, 2, 1, 1)
    self.gridQz = QtWidgets.QSpinBox(self.widget)
    self.gridQz.setMinimum(20)
    self.gridQz.setMaximum(300)
    self.gridQz.setSingleStep(10)
    self.gridQz.setProperty("value", 50)
    self.gridQz.setObjectName("gridQz")
    self.gridLayout.addWidget(self.gridQz, 1, 4, 1, 1)
    self.lambdaNoDirectPulse = QtWidgets.QCheckBox(self.widget)
    self.lambdaNoDirectPulse.setChecked(True)
    self.lambdaNoDirectPulse.setObjectName("lambdaNoDirectPulse")
    self.gridLayout.addWidget(self.lambdaNoDirectPulse, 6, 2, 1, 4)
    self.usePf = QtWidgets.QCheckBox(self.widget)
    self.usePf.setObjectName("usePf")
    self.gridLayout.addWidget(self.usePf, 1, 3, 1, 1)
    self.label_7 = QtWidgets.QLabel(self.widget)
    self.label_7.setObjectName("label_7")
    self.gridLayout.addWidget(self.label_7, 0, 2, 1, 2)
    self.label = QtWidgets.QLabel(self.widget)
    sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
    sizePolicy.setHorizontalStretch(1)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
    self.label.setSizePolicy(sizePolicy)
    self.label.setObjectName("label")
    self.gridLayout.addWidget(self.label, 3, 2, 1, 2)
    self.label_2 = QtWidgets.QLabel(self.widget)
    sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
    sizePolicy.setHorizontalStretch(1)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
    self.label_2.setSizePolicy(sizePolicy)
    self.label_2.setObjectName("label_2")
    self.gridLayout.addWidget(self.label_2, 4, 2, 1, 2)
    self.label_5 = QtWidgets.QLabel(self.widget)
    sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
    sizePolicy.setHorizontalStretch(1)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(self.label_5.sizePolicy().hasHeightForWidth())
    self.label_5.setSizePolicy(sizePolicy)
    self.label_5.setObjectName("label_5")
    self.gridLayout.addWidget(self.label_5, 5, 2, 1, 2)
    self.label_6 = QtWidgets.QLabel(self.widget)
    sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
    sizePolicy.setHorizontalStretch(1)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(self.label_6.sizePolicy().hasHeightForWidth())
    self.label_6.setSizePolicy(sizePolicy)
    self.label_6.setObjectName("label_6")
    self.gridLayout.addWidget(self.label_6, 7, 2, 1, 2)
    self.pushButton = QtWidgets.QPushButton(self.widget)
    self.pushButton.setObjectName("pushButton")
    self.gridLayout.addWidget(self.pushButton, 9, 2, 1, 2)
    self.verticalLayout_3.addWidget(self.widget)
    self.buttonBox = QtWidgets.QDialogButtonBox(self.verticalWidget)
    self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
    self.buttonBox.setObjectName("buttonBox")
    self.verticalLayout_3.addWidget(self.buttonBox)
    self.horizontalLayout.addWidget(self.verticalWidget)
    self.verticalLayout_2.addWidget(self.splitter)

    self.retranslateUi(Dialog)
    self.lambdaMin.valueChanged['double'].connect(Dialog.lambdaRangeChanged)
    self.lambdaMax.valueChanged['double'].connect(Dialog.lambdaRangeChanged)
    self.numberSlices.valueChanged['int'].connect(Dialog.numberSlicesChanged)
    self.pushButton.pressed.connect(Dialog.createProjectionPlots)
    self.buttonBox.accepted.connect(Dialog.accept)
    self.buttonBox.rejected.connect(Dialog.reject)
    self.plotShowList.itemSelectionChanged.connect(Dialog.changePlotSelection)
    self.iMin.valueChanged['double'].connect(Dialog.changePlotScale)
    self.iMax.valueChanged['double'].connect(Dialog.changePlotScale)
    QtCore.QMetaObject.connectSlotsByName(Dialog)
    Dialog.setTabOrder(self.gridQy, self.gridQz)
    Dialog.setTabOrder(self.gridQz, self.lambdaMin)
    Dialog.setTabOrder(self.lambdaMin, self.lambdaMax)
    Dialog.setTabOrder(self.lambdaMax, self.numberSlices)
    Dialog.setTabOrder(self.numberSlices, self.projectionMethod)
    Dialog.setTabOrder(self.projectionMethod, self.pushButton)
    Dialog.setTabOrder(self.pushButton, self.buttonBox)
    Dialog.setTabOrder(self.buttonBox, self.iMax)
    Dialog.setTabOrder(self.iMax, self.iMin)
    Dialog.setTabOrder(self.iMin, self.plotShowList)
    Dialog.setTabOrder(self.plotShowList, self.scrollArea)

  def retranslateUi(self, Dialog):
    _translate = QtCore.QCoreApplication.translate
    Dialog.setWindowTitle(_translate("Dialog", "QuickNXS - GISANS export"))
    self.label_9.setText(_translate("Dialog", "I-Max"))
    self.label_11.setText(_translate("Dialog", "10^"))
    self.label_10.setText(_translate("Dialog", "I-Min"))
    self.label_12.setText(_translate("Dialog", "10^"))
    self.label_3.setText(_translate("Dialog", "Å"))
    self.projectionMethod.setItemText(0, _translate("Dialog", "Binning"))
    self.label_4.setText(_translate("Dialog", "Å"))
    self.label_8.setText(_translate("Dialog", "Grid Points Qz"))
    self.lambdaNoDirectPulse.setText(_translate("Dialog", "Remove Direct Pulse"))
    self.usePf.setText(_translate("Dialog", "/pf"))
    self.label_7.setText(_translate("Dialog", "Grid Points Qy"))
    self.label.setText(_translate("Dialog", "λ-Min"))
    self.label_2.setText(_translate("Dialog", "λ-Max"))
    self.label_5.setText(_translate("Dialog", "No. of Slices"))
    self.label_6.setText(_translate("Dialog", "Projection Method"))
    self.pushButton.setText(_translate("Dialog", "Create Preview"))

from .mplwidget import MPLWidget
