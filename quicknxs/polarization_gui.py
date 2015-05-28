#-*- coding: utf-8 -*-
'''
Dialog to calculate and viziualize polarization parameters from polarization analysis
measurements of the direct beam.
'''

from numpy import where, ones_like, array, sqrt, hstack, argsort, float64, savetxt
from PyQt4.QtGui import QDialog, QTableWidgetItem, QFileDialog, QInputDialog
from polarization_dialog import Ui_Dialog
from .qreduce import Reflectivity
from .mpfit import mpfit

class PolarizationDialog(QDialog):
  Icurrent={}
  _auto_change_active=False
  polarization_parameters=None

  def __init__(self, parent):
    QDialog.__init__(self, parent)
    self.parent_window=parent
    parent.initiateReflectivityPlot.connect(self.update_fr)
    self.ui=Ui_Dialog()
    self.ui.setupUi(self)
    self.setWindowTitle(u'QuickNXS - Polarization')
    self._WLitems=[]
    self._FMitems=[]
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
      phi, _dphi, Fp, _dFp, Fa, _dFa=self.calc_pols(I)
      self.ui.PolLabel.setText(u'φ=%.3f F1=%.3f F2=%.3f'%(phi[reg].mean(), Fp[reg].mean(),
                                                          Fa[reg].mean()))
      #self.ui.wavelengthPol.errorbar(p.lamda[reg], phi[reg], yerr=dphi[reg], fmt='-b', label=u'$\\phi$')
      #self.ui.wavelengthPol.errorbar(p.lamda[reg], Fp[reg], yerr=dFp[reg], fmt='-r', label=u'F$_1$')
      #self.ui.wavelengthPol.errorbar(p.lamda[reg], Fa[reg], yerr=dFa[reg], fmt='-g', label=u'F$_2$')
    else:
      self.ui.PolLabel.setText('')
    #self.ui.wavelengthPol.legend()
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

  def calc_fullpols(self, I, FM):
    '''
    Calculate all 4 polariation parameter from a direct beam measurement and a magnetic
    materials measurement.
    '''
    phi, dphi, Fp, dFp, Fa, dFa=self.calc_pols(I)
    F00=FM['++'].Rraw;F01=FM['+-'].Rraw;F10=FM['-+'].Rraw;F11=FM['--'].Rraw
    #ddF00=FM['++'].dRraw**2;ddF01=FM['+-'].dRraw**2;ddF10=FM['-+'].dRraw**2;ddF11=FM['--'].dRraw**2
    p1=(1-2*Fa)*F00+(2*Fa-1)*F10-F01+F11
    p2=(1-2*Fa)*F00+(2*Fa-1)*F01-F10+F11
    p=0.5*(sqrt(phi*p1/p2)+1)
    dp=dphi

#    ddp1=0.
#    ddp2=0.
#    ddp12=ddp1/p2**2+ddp2*p1**2/p2**4
#    ddphi=dphi**2
#    ddphip12=ddphi*(p1/p2)**2+ddp12*phi**2

    a=(phi/(2*p-1)+1)/2.
    da=dp
    return p, dp, a, da, Fp, dFp, Fa, dFa

  def addWL(self):
    self._WLitems.append(self.Icurrent)
    self._FMitems.append(None)
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
    self.ui.wlTable.setItem(row, 3, QTableWidgetItem('None'))

  def clearWL(self):
    self._WLitems=[]
    self._FMitems=[]
    self.polarization_parameters=None
    self.ui.exportButton.setEnabled(False)
    self.ui.wlTable.setRowCount(0)
    self.ui.wavelengthPol.clear()
    self.ui.flippingRatios.clear()
    self.ui.wavelengthPol.draw()
    self.ui.flippingRatios.draw()
    self.ui.exportButton.setEnabled(False)

  def assignFM(self):
    tbl=self.ui.wlTable
    selection=tbl.selectedItems()
    if len(selection)==0:
      return
    row=tbl.row(selection[0])
    if not (self._WLitems[row][1].values()[0].lamda==self.Icurrent[1].values()[0].lamda).all():
      return
    self._FMitems[row]=self.Icurrent
    tbl.setItem(row, 3, QTableWidgetItem(self.Icurrent[0]))

  def drawFRs(self, active_number=None):
    errbars=self.ui.polErrorbars.isChecked()
    use_FM=(len(self._FMitems)>0) and (not any([item is None for item in self._FMitems]))
    if use_FM:
      lamda_all=[]
      p_all=[]
      a_all=[]
      Fa_all=[]
      Fp_all=[]
    for i, (no, I, ignore) in enumerate(self._WLitems):
      lamda=I.values()[0].lamda
      reg=((lamda>=float(self.ui.wlTable.item(i, 1).text()))&
           (lamda<=float(self.ui.wlTable.item(i, 2).text())))
      if len(I)==4:
        if not use_FM:
          phi, dphi, Fp, dFp, Fa, dFa=self.calc_pols(I)
          if not errbars:
            dphi=None;dFp=None;dFa=None
          else:
            dphi=dphi[reg];dFp=dFp[reg];dFa=dFa[reg]
          self.ui.wavelengthPol.errorbar(lamda[reg], phi[reg], yerr=dphi,
                                         ls='-', color='#008888', label=u'$\\phi$')
          self.ui.wavelengthPol.errorbar(lamda[reg], Fp[reg], yerr=dFp,
                                         ls='-', color='red', label=u'F$_1$')
          self.ui.wavelengthPol.errorbar(lamda[reg], Fa[reg], yerr=dFa,
                                         ls='-', color='orange', label=u'F$_2$')
        else:
          p, dp, a, da, Fp, dFp, Fa, dFa=self.calc_fullpols(I, self._FMitems[i][1])
          if not errbars:
            dp=None;da=None;dFp=None;dFa=None
          else:
            dp=dp[reg];da=da[reg];dFp=dFp[reg];dFa=dFa[reg]
          lamda_all.append(lamda[reg])
          p_all.append(p[reg]);a_all.append(a[reg])
          Fp_all.append(Fp[reg]);Fa_all.append(Fa[reg])
          self.ui.wavelengthPol.errorbar(lamda[reg], p[reg], yerr=dp,
                                         ls='-', color='green', label=u'p')
          self.ui.wavelengthPol.errorbar(lamda[reg], a[reg], yerr=da,
                                         ls='-', color='blue', label=u'a')
          self.ui.wavelengthPol.errorbar(lamda[reg], Fp[reg], yerr=dFp,
                                         ls='-', color='red', label=u'F$_p$')
          self.ui.wavelengthPol.errorbar(lamda[reg], Fa[reg], yerr=dFa,
                                         ls='-', color='orange', label=u'F$_a$')
        if i==0:
          self.ui.wavelengthPol.legend()
      if no==active_number:
        continue
      if '++' in I and '+-' in I:
        fr, dfr=self.calc_fr(I['++'], I['+-'])
        self.ui.flippingRatios.errorbar(lamda[reg], fr[reg], yerr=dfr[reg], fmt='-b', label=None)
      if '++' in I and '-+' in I:
        fr, dfr=self.calc_fr(I['++'], I['-+'])
        self.ui.flippingRatios.errorbar(lamda[reg], fr[reg], yerr=dfr[reg], fmt='-r', label=None)

    if use_FM:
      self.refinePolarizationParameters(lamda_all, p_all, a_all, Fa_all, Fp_all)

  def refinePolarizationParameters(self, lamda_all, p_all, a_all, Fa_all, Fp_all):
    # fit polarization parameters
    # for polarizer and analyzer efficiency use Pn function
    # and for flippers linear regression
    lamda=hstack(lamda_all).astype(float64)
    p=hstack(p_all).astype(float64)
    a=hstack(a_all).astype(float64)
    Fa=hstack(Fa_all).astype(float64)
    Fp=hstack(Fp_all).astype(float64)
    order=argsort(lamda)
    lamda=lamda[order]
    p=p[order]
    a=a[order]
    Fa=Fa[order]
    Fp=Fp[order]
    res=mpfit(Pn_residuals, [0.995, 1.55, 0.15], functkw=dict(lamda=lamda, Pdata=a), nprint=0)
    a_params=res.params
    res=mpfit(Pn_residuals, [0.995, 4.5, 0.15], functkw=dict(lamda=lamda, Pdata=p), nprint=0)
    p_params=res.params
    res=mpfit(lin_residuals, [0., 1.], functkw=dict(lamda=lamda, data=Fa), nprint=0)
    Fa_params=res.params
    res=mpfit(lin_residuals, [0., 1.], functkw=dict(lamda=lamda, data=Fp), nprint=0)
    Fp_params=res.params # store polarization parameters and data columns
    self.polarization_parameters=([lamda, p, Pn(lamda, *p_params)],
                                  [lamda, a, Pn(lamda, *a_params)],
                                  [lamda, Fp, lamda*Fp_params[0]+Fp_params[1]],
                                  [lamda, Fa, lamda*Fa_params[0]+Fa_params[1]],
                                  p_params, a_params, Fp_params, Fa_params)
    self.ui.wavelengthPol.plot(lamda, Pn(lamda, *p_params), color='green')
    self.ui.wavelengthPol.plot(lamda, Pn(lamda, *a_params), color='blue')
    self.ui.wavelengthPol.plot(lamda, lamda*Fp_params[0]+Fp_params[1], color='red')
    self.ui.wavelengthPol.plot(lamda, lamda*Fa_params[0]+Fa_params[1], color='orange')
    self.ui.exportButton.setEnabled(True)

  def exportPolarizationParameters(self):
    name=QFileDialog.getSaveFileName(parent=self, caption=u'Select export file prefix',
                                     filter='ASCII files (*.dat);;All files (*.*)')
    if name!='':
      name=unicode(name)
      if name.endswith('.dat'):
        prefix=name[:-4]
      else:
        prefix=name
      # export parameters
      f=open(prefix+'_parameters.dat', 'w')
      f.write('## Polarizer:\n# Pmax, lamda_0, s\n%g, %g, %g\n'%
              tuple(self.polarization_parameters[4]))
      f.write('## Analyzer:\n# Pmax, lamda_0, s\n%g, %g, %g\n'%
              tuple(self.polarization_parameters[5]))
      f.write('## Flipper1:\n# a, b\n%g, %g\n'%
              tuple(self.polarization_parameters[6]))
      f.write('## Flipper2:\n# a, b\n%g, %g\n'%
              tuple(self.polarization_parameters[7]))
      f.close()
      for name, (x, y, fy) in zip(['p', 'a', 'Fp', 'Fa'], self.polarization_parameters[:4]):
        f=open(prefix+'_%s.dat'%name, 'w')
        f.write('## Wavelength dependence of polarization parameter\n# lambda, data, fit\n')
        savetxt(f, array([x, y, fy]).T)
        f.close()

  def exportFR(self):
    name=QFileDialog.getSaveFileName(parent=self, caption=u'Select export file name',
                                     filter='ASCII files (*.dat);;All files (*.*)')
    if name!='':
      name=unicode(name)
      if not name.endswith('.dat'):
        name+=u'.dat'
      lamdas=[]
      FR1s=[]
      dFR1s=[]
      FR2s=[]
      dFR2s=[]
      for i, (ignore, I, ignore) in enumerate(self._WLitems):
        lamda=I.values()[0].lamda
        reg=((lamda>=float(self.ui.wlTable.item(i, 1).text()))&
             (lamda<=float(self.ui.wlTable.item(i, 2).text())))
        lamdas.append(lamda[reg])
        if '++' in I and '+-' in I:
          fr, dfr=self.calc_fr(I['++'], I['+-'])
          FR2s.append(fr[reg])
          dFR2s.append(dfr[reg])
        if '++' in I and '-+' in I:
          fr, dfr=self.calc_fr(I['++'], I['-+'])
          FR1s.append(fr[reg])
          dFR1s.append(dfr[reg])
      if len(FR1s)!=len(lamdas):
        FR1s=hstack(lamdas)*0.;dFR1s=hstack(lamdas)*0.
      else:
        FR1s=hstack(FR1s);dFR1s=hstack(dFR1s)
      if len(FR2s)!=len(lamdas):
        FR2s=hstack(lamdas)*0.;dFR2s=hstack(lamdas)*0.
      else:
        FR2s=hstack(FR2s);dFR2s=hstack(dFR2s)
      lamdas=hstack(lamdas)
      f=open(name, 'w')
      f.write('## Wavelength dependence of flipping ratio\n')
      f.write('# lambda, FR1, dFR1, FR2, dFR2, P1, P2\n')
      savetxt(f, array([lamdas, FR1s, dFR1s, FR2s, dFR2s,
                        sqrt((FR1s-1.)/(FR1s+1.)), sqrt((FR2s-1.)/(FR2s+1.))]).T)
      f.close()

  def exportFRDetector(self):
    '''
      Save the x,lamda vs. FR data to ASCII file.
    '''
    name=QFileDialog.getSaveFileName(parent=self, caption=u'Select export file name',
                                     filter='ASCII files (*.dat);;All files (*.*)')
    if name!='':
      name=unicode(name)
    else:
      return
    f=open(name, 'w')
    f.write('## Pixel dependence of flipping ratio\n# lambda, X, FR1, dFR1\n')
    for ignore, I, xpos in self._Xitems:
      lamda=I.values()[0].lamda
      fr, dfr=self.calc_fr(I['++'], I['+-'])
      reg=I['++'].Rraw>0
      savetxt(f, array([ones_like(fr[reg])*xpos, lamda[reg], fr[reg], dfr[reg]]).T)
      f.write('\n')
    f.close()

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
      self.ui.exportDetButton.setEnabled(True)

  def addXMultiple(self):
    '''
      Convenience function to add multiple subsequent datasets for different detector angles.
    '''
    items, OK=QInputDialog.getInt(self, u'Add multiple datasets',
                              u'Enter the number of subsequent datasets to be added:',
                              value=1, min=0, max=304, step=1)
    if not OK or items==0:
      return
    self.addX()
    if items==1:
      return
    self._x_items_to_go=items-1
    self.parent_window.initiateReflectivityPlot.connect(self._addXMultiple)
    self.parent_window.nextFile()

  def _addXMultiple(self):
    self._x_items_to_go-=1
    self.addX()
    if self._x_items_to_go==0:
      self._x_items_to_go=None
      self.parent_window.initiateReflectivityPlot.disconnect(self._addXMultiple)
      return
    self.parent_window.nextFile()

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
    self.ui.detectorPol.clear()
    self.ui.detectorPol.draw()
    self.ui.exportDetButton.setEnabled(False)

  def closeEvent(self, *args, **kwargs):
    # disconnect when closed as object is not actually destroyed and will slow down plots
    self.parent_window.initiateReflectivityPlot.disconnect(self.update_fr)
    self.close()
    #return QDialog.closeEvent(self, *args, **kwargs)



def Iup(m, mc, s):
  return where(m<=1., 1.,
               where(m<=mc, 0.2/(mc-1)*m+1+0.2/(mc-1),
                     0.8*s**4/(m-mc+s)**(4)))

def Idown(m, mc, s):
  return where(m<=mc, 1.,
                    s**4/(m-mc+s)**4)

def m_l(lamda, lamda_0):
  return 4.*lamda_0/lamda

def Pn(lamda, Pmax, lamda_0, s):
  m=m_l(lamda, lamda_0)
  if lamda_0>=2.5:
    s2=s;s1=0.05
  else:
    s1=s;s2=0.05
  return Pmax*(Iup(m, 4, s2)-Idown(m, 0.6, s1))/(Iup(m, 4, s2)+Idown(m, 0.6, s1))

def Pn_residuals(p, lamda=None, Pdata=None, fjac=None):
  return 0, Pdata-Pn(lamda, *p)

def lin_residuals(p, lamda=None, data=None, fjac=None):
  return 0, data-(p[0]*lamda+p[1])
