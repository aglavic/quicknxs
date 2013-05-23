#-*- coding: utf-8 -*-
'''
  Dialog to compare normalization with reflectivity data in a single plot.
'''

from numpy import *
from PyQt4.QtGui import QDialog
from .rawcompare_dialog import Ui_RawDat
from .mreduce import Reflectivity

class RawCompare(QDialog):
  state_colors=[['#ff0000', '#00ff00', '#0000ff', '#aa00aa'],
                ['#aa0000', '#00aa00', '#0000aa', '#550055']]

  def __init__(self, parent):
    QDialog.__init__(self, parent)
    self.ui=Ui_RawDat()
    self.ui.setupUi(self)
    self.parent=parent
    self.parent.initiateReflectivityPlot.connect(self.draw_plot)
    self.draw_plot()

  def draw_plot(self):
    plot=self.ui.plot
    gui=self.parent
    if not gui.refl:
      return
    plot.clear()
    plot.set_xlabel(u'$\\lambda$ [Å]')
    plot.set_ylabel(u'I [Counts/pC]')

    imax=1e-30
    imin=1e30
    lmin=gui.refl.lamda.min()
    lmax=gui.refl.lamda.max()

    norm=gui.refl.options['normalization']
    if norm:
      lmin=norm.lamda[norm.I>0].min();lmax=norm.lamda[norm.I>0].max()

    if self.ui.showNorm.isChecked() and norm:
      imax=max(imax, norm.I.max()); imin=min(imin, norm.I[norm.I>0].min())
      plot.errorbar(norm.lamda, norm.I, norm.dI, color='#666666', label='Direct Beam')
      if self.ui.showNormBG.isChecked():
        imin=min(imin, norm.BG[norm.BG>0].min())
        plot.errorbar(norm.lamda, norm.BG, norm.dBG, color='#000000', label='Dir. Beam - BG')

    if self.ui.showActive.isChecked():
      if self.ui.showAll.isChecked():
        for i, (channel, data) in enumerate(gui.active_data.items()):
          refl=Reflectivity(data, **gui.refl.options)
          imax=max(imax, refl.I.max()); imin=min(imin, refl.I[refl.I>0].min())
          plot.errorbar(refl.lamda, refl.I, refl.dI, color=self.state_colors[0][i],
                        label=gui.refl.options['number']+' '+channel)
          if self.ui.showBG.isChecked():
            imin=min(imin, refl.BG[refl.BG>0].min())
            plot.errorbar(refl.lamda, refl.BG, refl.dBG, color=self.state_colors[1][i],
                          label=gui.refl.options['number']+' '+channel+' BG')
      else:
        imax=max(imax, gui.refl.I.max()); imin=min(imin, gui.refl.I[gui.refl.I>0].min())
        plot.errorbar(gui.refl.lamda, gui.refl.I, gui.refl.dI, color=self.state_colors[0][0],
                      label=gui.refl.options['number'])
        if self.ui.showBG.isChecked():
          imin=min(imin, gui.refl.BG[gui.refl.BG>0].min())
          plot.errorbar(gui.refl.lamda, gui.refl.BG, gui.refl.dBG,
                        color=self.state_colors[1][0],
                        label=gui.refl.options['number']+' BG')

    if gui.ui.logarithmic_y.isChecked():
      plot.set_yscale('log')
    else:
      plot.set_ylabel('linear')
    plot.canvas.ax.set_xlim(lmin, lmax)
    plot.canvas.ax.set_ylim(imin, imax*1.5)
    plot.legend(loc=8)
    plot.draw()
