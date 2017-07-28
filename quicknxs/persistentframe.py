#-*- coding: utf-8 -*-
'''
  doc
'''

from PyQt5.QtWidgets import QFrame

class PersistentFrame(QFrame):
  do_hide=True

  def hide(self):
    if self.do_hide:
      QFrame.hide(self)

