#-*- coding: utf-8 -*-
'''
Dialog to calculate and viziualize polarization parameters from polarization analysis
measurements of the direct beam.
'''

from numpy import where
from PyQt4.QtGui import QDialog
from polarization_dialog import Ui_Dialog
from .mreduce import Reflectivity

class PolarizationDialog(QDialog):

  def __init__(self, parent):
    QDialog.__init__(self, parent)
    self.parent_window=parent
    parent.initiateReflectivityPlot.connect(self.update_fr)
    self.ui=Ui_Dialog()
    self.ui.setupUi(self)
    self.setWindowTitle(u'QuickNXS - Polarization')
    self.update_fr()

  def update_fr(self):
    '''
    Plot the different flipping ratios of the current dataset.
    '''
    parent=self.parent_window
    if parent.active_data is None or parent.refl is None:
      return
    opts=parent.refl.options
    data=parent.active_data
    channels=data.keys()
    self.ui.flippingRatios.clear()
    if not (('++' in channels and '+-' in channels) or
            ('++' in channels and '-+' in channels)):
      self.ui.flippingRatios.draw()
      return
    FR1=0;FR2=0
    I={}
    if '++' in channels and '-+' in channels:
      p=Reflectivity(data['++'], **opts)
      m=Reflectivity(data['-+'], **opts)
      I['++']=p;I['-+']=m
      reg=where((p.Rraw>0)&(m.Rraw>0))
      fr=p.Rraw/m.Rraw
      FR1=p.Rraw[reg].sum()/m.Rraw[reg].sum()
      self.ui.flippingRatios.plot(p.lamda[reg], fr[reg], label=u'SF1')
    if '++' in channels and '+-' in channels:
      p=Reflectivity(data['++'], **opts)
      m=Reflectivity(data['+-'], **opts)
      I['++']=p;I['+-']=m
      reg=where((p.Rraw>0)&(m.Rraw>0))
      fr=p.Rraw/m.Rraw
      FR2=p.Rraw[reg].sum()/m.Rraw[reg].sum()
      self.ui.flippingRatios.plot(p.lamda[reg], fr[reg], label=u'SF2')
    if len(channels)==4:
      I['--']=Reflectivity(data['--'], **opts)
      p0, p1, phi=self.calc_pols(I)
    self.ui.flippingRatios.legend()
    self.ui.flippingRatios.set_xlabel(u'λ [Å]')
    self.ui.flippingRatios.set_ylabel(u'Flipping Ratio')
    self.ui.flippingRatios.draw()
    self.ui.FR1.setText("%.1f"%FR1)
    self.ui.FR2.setText("%.1f"%FR2)

  def calc_pols(self, I):
    return 0, 0, 0

