#-*- coding: utf-8 -*-
'''
  Small widget modifications to be easier to work with.
'''

from PyQt4.QtGui import QSpinBox
from PyQt4.QtCore import pyqtSlot

class LimitingSpinBox(QSpinBox):

  @pyqtSlot(int)
  def setMaxValue(self, value):
    self.setMaximum(value)

  @pyqtSlot(int)
  def setMinValue(self, value):
    self.setMinimum(value)

