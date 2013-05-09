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
      I['++']=p.Rraw;I['-+']=m.Rraw
      reg=where((p.Rraw>0)&(m.Rraw>0))
      fr=p.Rraw/m.Rraw
      FR1=fr[reg].mean()
      self.ui.flippingRatios.plot(p.lamda[reg], fr[reg], label=u'SF$_1$')
    if '++' in channels and '+-' in channels:
      p=Reflectivity(data['++'], **opts)
      m=Reflectivity(data['+-'], **opts)
      I['++']=p.Rraw;I['+-']=m.Rraw
      reg=where((p.Rraw>0)&(m.Rraw>0))
      fr=p.Rraw/m.Rraw
      FR2=fr[reg].mean()
      self.ui.flippingRatios.plot(p.lamda[reg], fr[reg], label=u'SF$_2$')
    if len(channels)==4:
      I['--']=Reflectivity(data['--'], **opts).Rraw
      reg=where((I['++']>0)&(I['+-']>0)&(I['-+']>0)&(I['--']>0))
      phi, Fp, Fa=self.calc_pols(I)
      self.ui.wavelengthPol.clear()
      self.ui.wavelengthPol.plot(p.lamda[reg], phi[reg], label=u'φ')
      self.ui.wavelengthPol.plot(p.lamda[reg], Fp[reg], label=u'F$_1$')
      self.ui.wavelengthPol.plot(p.lamda[reg], Fa[reg], label=u'F$_2$')
      self.ui.wavelengthPol.legend()
      self.ui.wavelengthPol.set_xlabel(u'λ [Å]')
      self.ui.wavelengthPol.set_ylabel(u'Efficiency')
      self.ui.wavelengthPol.draw()
    self.ui.flippingRatios.legend()
    self.ui.flippingRatios.set_xlabel(u'λ [Å]')
    self.ui.flippingRatios.set_ylabel(u'Flipping Ratio')
    self.ui.flippingRatios.draw()
    self.ui.FR1.setText("%.1f"%FR1)
    self.ui.FR2.setText("%.1f"%FR2)

  def calc_pols(self, I):
    '''
    Calculate efficiency parameters from intensities using the
    nomenclature given in:
    A.R. Wildes, Neutron Polarization Analysis Corrections Made Easy, 
                 Neutron News 17:2, 17-25 (2007)
    '''
    I00=I['++'];I01=I['+-'];I10=I['-+'];I11=I['--']
    # combined polarizer/analyzer efficiency
    phi=((I00-I01)*(I00-I10))/(I00*I11-I01*I10)
    # flipper 1 efficiency
    Fp=(I00-I01-I10+I11)/2./(I00-I01)
    # flipper 2 efficiency
    Fa=(I00-I01-I10+I11)/2./(I00-I10)
    return phi, Fp, Fa

