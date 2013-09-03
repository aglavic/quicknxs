#-*- coding: utf-8 -*-
'''
Dialog to calculate and viziualize polarization parameters from polarization analysis
measurements of the direct beam.
'''

from numpy import where, ones_like, array, sqrt
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
    self.ui.wavelengthPol.clear()
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
      I['++']=p;I['-+']=m
      reg=where((p.Rraw>0)&(m.Rraw>0)&(p.lamda>=lmin)&(p.lamda<=lmax))
      fr, dfr=self.calc_fr(p, m)
      FR1=fr[reg].mean()
      self.ui.flippingRatios.errorbar(p.lamda[reg], fr[reg], yerr=dfr[reg], fmt='-r', label=u'SF$_1$')
    if '++' in channels and '+-' in channels:
      p=Reflectivity(data['++'], **opts)
      m=Reflectivity(data['+-'], **opts)
      I['++']=p;I['+-']=m
      reg=where((p.Rraw>0)&(m.Rraw>0)&(p.lamda>=lmin)&(p.lamda<=lmax))
      fr, dfr=self.calc_fr(p, m)
      FR2=fr[reg].mean()
      self.ui.flippingRatios.errorbar(p.lamda[reg], fr[reg], yerr=dfr[reg], fmt='-b', label=u'SF$_2$')
    if len(channels)==4:
      I['--']=Reflectivity(data['--'], **opts)
      reg=where((I['++'].Rraw>0)&(I['+-'].Rraw>0)&(I['-+'].Rraw>0)&
                (I['--'].Rraw>0)&(p.lamda>=lmin)&(p.lamda<=lmax))
      phi, dphi, Fp, dFp, Fa, dFa=self.calc_pols(I)
      self.ui.PolLabel.setText(u'φ=%.3f F1=%.3f F2=%.3f'%(phi[reg].mean(), Fp[reg].mean(),
                                                          Fa[reg].mean()))
      self.ui.wavelengthPol.errorbar(p.lamda[reg], phi[reg], yerr=dphi[reg], fmt='-b', label=u'$\\phi$')
      self.ui.wavelengthPol.errorbar(p.lamda[reg], Fp[reg], yerr=dFp[reg], fmt='-r', label=u'F$_1$')
      self.ui.wavelengthPol.errorbar(p.lamda[reg], Fa[reg], yerr=dFa[reg], fmt='-g', label=u'F$_2$')
    else:
      self.ui.PolLabel.setText('')
    self.ui.wavelengthPol.legend()
    self.ui.wavelengthPol.set_xlabel(u'$\\lambda$ [Å]')
    self.ui.wavelengthPol.set_ylabel(u'Efficiency')
    self.ui.wavelengthPol.canvas.ax.axhline(1., color='black')
    self.ui.wavelengthPol.draw()

    self.ui.flippingRatios.legend()
    self.ui.flippingRatios.set_xlabel(u'$\\lambda$ [Å]')
    self.ui.flippingRatios.set_ylabel(u'Flipping Ratio')
    self.ui.flippingRatios.draw()
    self.ui.FR1.setText("%.1f"%FR1)
    self.ui.FR2.setText("%.1f"%FR2)
    self.Icurrent=(opts['number'], I, opts['x_pos'])

  def calc_fr(self, p, m):
    fr=p.Rraw/m.Rraw
    dfr=sqrt((p.dRraw/m.Rraw)**2+(m.dRraw*p.Rraw/m.Rraw**2)**2)
    return fr, dfr

  def calc_pols(self, I):
    '''
    Calculate efficiency parameters from intensities using the
    formulas (11) given in [ARWildes2007]_.
    '''
    I00=I['++'].Rraw;I01=I['+-'].Rraw;I10=I['-+'].Rraw;I11=I['--'].Rraw
    ddI00=I['++'].dRraw**2;ddI01=I['+-'].dRraw**2;ddI10=I['-+'].dRraw**2;ddI11=I['--'].dRraw**2
    # combined polarizer/analyzer efficiency
    phi1=(I00-I01)*(I00-I10)
    phi2=(I00*I11-I01*I10)
    phi=phi1/phi2
    # error propagation
    ddphi1=((ddI00+ddI01)*(I00-I10)**2)+((ddI00+ddI10)*(I00-I01)**2)
    ddphi2=(ddI00*I11**2+ddI11*I00**2)+(ddI01*I10**2+ddI10*I01**2)
    dphi=sqrt(ddphi1/phi2**2+ddphi2*phi1**2/phi2**4)

    # flipper 1 efficiency
    Fp1=(I00-I01-I10+I11)
    Fp2=2.*(I00-I01)
    Fp=Fp1/Fp2
    ddFp1=(ddI00+ddI01+ddI10+ddI11)
    ddFp2=4.*(ddI00+ddI01)
    dFp=sqrt(ddFp1/Fp2**2+ddFp2*Fp1**2/Fp2**4)

    # flipper 2 efficiency
    Fa1=Fp1
    Fa2=2.*(I00-I10)
    Fa=Fa1/Fa2
    ddFa1=ddFp1
    ddFa2=4.*(ddI00+ddI10)
    dFa=sqrt(ddFa1/Fa2**2+ddFa2*Fa1**2/Fa2**4)
    return phi, dphi, Fp, dFp, Fa, dFa

  def addWL(self):
    self._WLitems.append(self.Icurrent)
    row=self.ui.wlTable.rowCount()
    reg=True
    for value in self.Icurrent[1].values():
      reg=reg&(value.Rraw>0)
    lmin=value.lamda[reg][0]
    lmax=value.lamda[reg][-1]
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
    for i, (no, I, ignore) in enumerate(self._WLitems):
      lamda=I.values()[0].lamda
      if no==active_number:
        continue
      reg=((lamda>=float(self.ui.wlTable.item(i, 1).text()))&
           (lamda<=float(self.ui.wlTable.item(i, 2).text())))
      if '++' in I and '+-' in I:
        fr, dfr=self.calc_fr(I['++'], I['+-'])
        self.ui.flippingRatios.errorbar(lamda[reg], fr[reg], yerr=dfr[reg], fmt='-b', label=None)
      if '++' in I and '-+' in I:
        fr, dfr=self.calc_fr(I['++'], I['-+'])
        self.ui.flippingRatios.errorbar(lamda[reg], fr[reg], yerr=dfr[reg], fmt='-r', label=None)
      if len(I)==4:
        phi, dphi, Fp, dFp, Fa, dFa=self.calc_pols(I)
        self.ui.wavelengthPol.errorbar(lamda[reg], phi[reg], yerr=dphi[reg], fmt='-b', label=None)
        self.ui.wavelengthPol.errorbar(lamda[reg], Fp[reg], yerr=dFp[reg], fmt='-r', label=None)
        self.ui.wavelengthPol.errorbar(lamda[reg], Fa[reg], yerr=dFa[reg], fmt='-g', label=None)


  def addX(self):
    self._Xitems.append(self.Icurrent)
    row=self.ui.xTable.rowCount()
    self._auto_change_active=True
    self.ui.xTable.insertRow(row)
    self.ui.xTable.setItem(row, 0, QTableWidgetItem(self.Icurrent[0]))
    self.ui.xTable.setItem(row, 1, QTableWidgetItem(str(self.Icurrent[2])))
    self._auto_change_active=False
    if len(self._Xitems)>2:
      self.drawXFR()

  def drawXFR(self):
    plot=self.ui.detectorPol
    plot.clear_fig()
    lamdas=[]
    Xs=[]
    FRs=[]
    for ignore, I, xpos in self._Xitems:
      lamda=I.values()[0].lamda
      lamdas.append(lamda)
      FRs.append(I['++'].Rraw/I['+-'].Rraw)
      Xs.append(ones_like(lamda)*xpos)
    plot.pcolormesh(array(Xs), array(lamdas), array(FRs), cmap=self.parent_window.color)
    plot.cplot.set_clim(30, 150)
    plot.set_xlabel(u'X [pix]')
    plot.set_ylabel(u'$\\lambda$ [Å]')
    plot.canvas.fig.colorbar(plot.cplot)
    plot.draw()

  def clearX(self):
    self._Xitems=[]
    self.ui.xTable.setRowCount(0)

  def closeEvent(self, *args, **kwargs):
    # disconnect when closed as object is not actually destroyed and will slow down plots
    self.parent_window.initiateReflectivityPlot.disconnect(self.update_fr)
    return QDialog.closeEvent(self, *args, **kwargs)

