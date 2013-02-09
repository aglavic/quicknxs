# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'designer/autoreduction_dialog.ui'
#
# Created: Sat Feb  9 14:45:56 2013
#      by: PyQt4 UI code generator 4.9.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
  _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
  _fromUtf8 = lambda s: s

class Ui_AutoReductionDialog(object):
  def setupUi(self, AutoReductionDialog):
    AutoReductionDialog.setObjectName(_fromUtf8("AutoReductionDialog"))
    AutoReductionDialog.resize(782, 512)
    self.verticalLayout_2 = QtGui.QVBoxLayout(AutoReductionDialog)
    self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
    self.splitter_2 = QtGui.QSplitter(AutoReductionDialog)
    self.splitter_2.setOrientation(QtCore.Qt.Horizontal)
    self.splitter_2.setObjectName(_fromUtf8("splitter_2"))
    self.directoryView = QtGui.QTreeView(self.splitter_2)
    self.directoryView.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
    self.directoryView.setObjectName(_fromUtf8("directoryView"))
    self.widget_3 = QtGui.QWidget(self.splitter_2)
    self.widget_3.setObjectName(_fromUtf8("widget_3"))
    self.verticalLayout = QtGui.QVBoxLayout(self.widget_3)
    self.verticalLayout.setMargin(0)
    self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
    self.splitter = QtGui.QSplitter(self.widget_3)
    self.splitter.setOrientation(QtCore.Qt.Vertical)
    self.splitter.setObjectName(_fromUtf8("splitter"))
    self.widget = QtGui.QWidget(self.splitter)
    self.widget.setObjectName(_fromUtf8("widget"))
    self.gridLayout = QtGui.QGridLayout(self.widget)
    self.gridLayout.setMargin(0)
    self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
    spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
    self.gridLayout.addItem(spacerItem, 1, 0, 1, 1)
    spacerItem1 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
    self.gridLayout.addItem(spacerItem1, 4, 0, 1, 1)
    self.addNormButton = QtGui.QPushButton(self.widget)
    self.addNormButton.setObjectName(_fromUtf8("addNormButton"))
    self.gridLayout.addWidget(self.addNormButton, 2, 0, 1, 1)
    self.removeNormButton = QtGui.QPushButton(self.widget)
    self.removeNormButton.setObjectName(_fromUtf8("removeNormButton"))
    self.gridLayout.addWidget(self.removeNormButton, 3, 0, 1, 1)
    self.normalizations = QtGui.QListWidget(self.widget)
    self.normalizations.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
    self.normalizations.setObjectName(_fromUtf8("normalizations"))
    self.gridLayout.addWidget(self.normalizations, 1, 1, 4, 1)
    self.label = QtGui.QLabel(self.widget)
    self.label.setAlignment(QtCore.Qt.AlignCenter)
    self.label.setObjectName(_fromUtf8("label"))
    self.gridLayout.addWidget(self.label, 0, 1, 1, 1)
    self.widget_2 = QtGui.QWidget(self.splitter)
    self.widget_2.setObjectName(_fromUtf8("widget_2"))
    self.gridLayout_2 = QtGui.QGridLayout(self.widget_2)
    self.gridLayout_2.setMargin(0)
    self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
    spacerItem2 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
    self.gridLayout_2.addItem(spacerItem2, 1, 0, 1, 1)
    spacerItem3 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
    self.gridLayout_2.addItem(spacerItem3, 4, 0, 1, 1)
    self.addRefButton = QtGui.QPushButton(self.widget_2)
    self.addRefButton.setObjectName(_fromUtf8("addRefButton"))
    self.gridLayout_2.addWidget(self.addRefButton, 2, 0, 1, 1)
    self.removeRefButton = QtGui.QPushButton(self.widget_2)
    self.removeRefButton.setObjectName(_fromUtf8("removeRefButton"))
    self.gridLayout_2.addWidget(self.removeRefButton, 3, 0, 1, 1)
    self.reflectivities = QtGui.QListWidget(self.widget_2)
    self.reflectivities.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
    self.reflectivities.setObjectName(_fromUtf8("reflectivities"))
    self.gridLayout_2.addWidget(self.reflectivities, 1, 1, 4, 1)
    self.label_2 = QtGui.QLabel(self.widget_2)
    self.label_2.setAlignment(QtCore.Qt.AlignCenter)
    self.label_2.setObjectName(_fromUtf8("label_2"))
    self.gridLayout_2.addWidget(self.label_2, 0, 1, 1, 1)
    self.verticalLayout.addWidget(self.splitter)
    self.buttonBox = QtGui.QDialogButtonBox(self.widget_3)
    self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
    self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
    self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
    self.verticalLayout.addWidget(self.buttonBox)
    self.verticalLayout_2.addWidget(self.splitter_2)

    self.retranslateUi(AutoReductionDialog)
    QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), AutoReductionDialog.accept)
    QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), AutoReductionDialog.reject)
    QtCore.QObject.connect(self.addNormButton, QtCore.SIGNAL(_fromUtf8("clicked()")), AutoReductionDialog.addNorm)
    QtCore.QObject.connect(self.removeNormButton, QtCore.SIGNAL(_fromUtf8("clicked()")), AutoReductionDialog.delNorm)
    QtCore.QObject.connect(self.addRefButton, QtCore.SIGNAL(_fromUtf8("clicked()")), AutoReductionDialog.addRef)
    QtCore.QObject.connect(self.removeRefButton, QtCore.SIGNAL(_fromUtf8("clicked()")), AutoReductionDialog.delRef)
    QtCore.QObject.connect(self.directoryView, QtCore.SIGNAL(_fromUtf8("expanded(QModelIndex)")), AutoReductionDialog.resizeDirview)
    QtCore.QMetaObject.connectSlotsByName(AutoReductionDialog)

  def retranslateUi(self, AutoReductionDialog):
    AutoReductionDialog.setWindowTitle(QtGui.QApplication.translate("AutoReductionDialog", "Select files for reduction", None, QtGui.QApplication.UnicodeUTF8))
    self.addNormButton.setText(QtGui.QApplication.translate("AutoReductionDialog", ">", None, QtGui.QApplication.UnicodeUTF8))
    self.removeNormButton.setText(QtGui.QApplication.translate("AutoReductionDialog", "<", None, QtGui.QApplication.UnicodeUTF8))
    self.label.setText(QtGui.QApplication.translate("AutoReductionDialog", "Normalization Files", None, QtGui.QApplication.UnicodeUTF8))
    self.addRefButton.setText(QtGui.QApplication.translate("AutoReductionDialog", ">", None, QtGui.QApplication.UnicodeUTF8))
    self.removeRefButton.setText(QtGui.QApplication.translate("AutoReductionDialog", "<", None, QtGui.QApplication.UnicodeUTF8))
    self.label_2.setText(QtGui.QApplication.translate("AutoReductionDialog", "Reflectivity Files", None, QtGui.QApplication.UnicodeUTF8))

