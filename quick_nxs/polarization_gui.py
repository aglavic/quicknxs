#-*- coding: utf-8 -*-
'''
Dialog to calculate and viziualize polarization parameters from polarization analysis
measurements of the direct beam.
'''

from numpy import where, ones_like, array
from PyQt4.QtGui import QDialog, QTableWidgetItem
from polarization_dialog import Ui_Dialog
from .mreduce import Reflectivity

class PolarizationDialog(QDialog):
  Icurrent={}
  _auto_change_active=False

  def __init__(self, parent):
    QDialog.__init__(self, parent)
    self.parent_window=parent
    parent.initiateReflectivityPlot.connect(self.update_fr)
    self.ui=Ui_Dialog()
    self.ui.setupUi(self)
    self.setWindowTitle(u'QuickNXS - Polarization')
    self._WLitems=[]
    self._Xitems=[]
    self.update_fr()

  def update_fr(self):
    '''
    Plot the different flipping ratios of the current dataset.
    '''
    if self._auto_change_active:
      return
    parent=self.parent_window
    if parent.active_data is None or parent.refl is None:
      return
    opts=parent.refl.options
    data=parent.active_data
    channels=data.keys()
    self.ui.flippingRatios.clear()
    self.drawFRs()
    if not (('++' in channels and '+-' in channels) or
            ('++' in channels and '-+' in channels)):
      self.ui.flippingRatios.draw()
      return
    FR1=0;FR2=0
    I={}
    nos=[item[0] for item in self._WLitems]
    if opts['number'] in nos:
      this_index=nos.index(opts['number'])
      lmin=float(self.ui.wlTable.item(this_index, 1).text())
      lmax=float(self.ui.wlTable.item(this_index, 2).text())
    else:
      lmin=0.; lmax=15.
    if '++' in channels and '-+' in channels:
      p=Reflectivity(data['++'], **opts)
      m=Reflectivity(data['-+'], **opts)
      I['++']=p.Rraw;I['-+']=m.Rraw
      reg=where((p.Rraw>0)&(m.Rraw>0)&(p.lamda>=lmin)&(p.lamda<=lmax))
      fr=p.Rraw/m.Rraw
      FR1=fr[reg].mean()
      self.ui.flippingRatios.plot(p.lamda[reg], fr[reg], '-r', label=u'SF$_1$')
    if '++' in channels and '+-' in channels:
      p=Reflectivity(data['++'], **opts)
      m=Reflectivity(data['+-'], **opts)
      I['++']=p.Rraw;I['+-']=m.Rraw
      reg=where((p.Rraw>0)&(m.Rraw>0)&(p.lamda>=lmin)&(p.lamda<=lmax))
      fr=p.Rraw/m.Rraw
      FR2=fr[reg].mean()
      self.ui.flippingRatios.plot(p.lamda[reg], fr[reg], '-b', label=u'SF$_2$')
    if len(channels)==4:
      I['--']=Reflectivity(data['--'], **opts).Rraw
      reg=where((I['++']>0)&(I['+-']>0)&(I['-+']>0)&(I['--']>0)&(p.lamda>=lmin)&(p.lamda<=lmax))
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
    self.Icurrent=(opts['number'], p.lamda, I, opts['x_pos'])

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

  def addWL(self):
    self._WLitems.append(self.Icurrent)
    row=self.ui.wlTable.rowCount()
    reg=True
    for value in self.Icurrent[2].values():
      reg=reg&(value>0)
    lmin=self.Icurrent[1][reg][0]
    lmax=self.Icurrent[1][reg][-1]
    self._auto_change_active=True
    self.ui.wlTable.insertRow(row)
    self.ui.wlTable.setItem(row, 0, QTableWidgetItem(self.Icurrent[0]))
    self.ui.wlTable.setItem(row, 1, QTableWidgetItem(str(lmin)))
    self.ui.wlTable.setItem(row, 2, QTableWidgetItem(str(lmax)))
    self._auto_change_active=False

  def clearWL(self):
    self._WLitems=[]
    self.ui.wlTable.setRowCount(0)

  def drawFRs(self, active_number=None):
    for i, (no, lamda, I, ignore) in enumerate(self._WLitems):
      if no==active_number:
        continue
      reg=((lamda>=float(self.ui.wlTable.item(i, 1).text()))&
           (lamda<=float(self.ui.wlTable.item(i, 2).text())))
      if '++' in I and '+-' in I:
        fr=I['++']/I['+-']
        self.ui.flippingRatios.plot(lamda[reg], fr[reg], '-b')
      if '++' in I and '-+' in I:
        fr=I['++']/I['-+']
        self.ui.flippingRatios.plot(lamda[reg], fr[reg], '-r')

  def addX(self):
    self._Xitems.append(self.Icurrent)
    row=self.ui.xTable.rowCount()
    self._auto_change_active=True
    self.ui.xTable.insertRow(row)
    self.ui.xTable.setItem(row, 0, QTableWidgetItem(self.Icurrent[0]))
    self.ui.xTable.setItem(row, 1, QTableWidgetItem(str(self.Icurrent[3])))
    self._auto_change_active=False
    if len(self._Xitems)>2:
      self.drawXFR()

  def drawXFR(self):
    plot=self.ui.detectorPol
    plot.clear_fig()
    lamdas=[]
    Xs=[]
    FRs=[]
    for ignore, lamda, I, xpos in self._Xitems:
      lamdas.append(lamda)
      FRs.append(I['++']/I['+-'])
      Xs.append(ones_like(lamda)*xpos)
    plot.pcolormesh(array(Xs), array(lamdas), array(FRs), cmap=self.parent_window.color)
    plot.cplot.set_clim(30, 150)
    plot.set_xlabel(u'X [pix]')
    plot.set_ylabel(u'λ [Å]')
    plot.canvas.fig.colorbar(plot.cplot)
    plot.draw()

  def clearX(self):
    self._Xitems=[]
    self.ui.xTable.setRowCount(0)
