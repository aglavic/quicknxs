#-*- coding: utf-8 -*-
'''
  Module for advanced definition of background subtraction.
'''

from PyQt4.QtGui import QDialog, QTableWidgetItem
from matplotlib.patches import Polygon, Rectangle
from numpy import array, sqrt
from .background_dialog import Ui_Dialog

class BackgroundDialog(QDialog):
  '''
  Allow the user to have more control on the background extraction procedure.
  A list of polygon regions can be defined for the background calculation and
  the background is shown in a X vs. Lambda map and as normalized intensity
  plot in comparison to the specular data.
  '''
  last_bg=(0., 0.)

  def __init__(self, parent):
    QDialog.__init__(self, parent)
    self.main_window=parent
    self.ui=Ui_Dialog()
    self.ui.setupUi(self)
    self.polygons=[]
    self.active_poly=None
    self.ui.xTof.canvas.mpl_connect('button_press_event', self.mouseClicked)
    parent.fileLoaded.connect(self.drawXTof)
    parent.initiateReflectivityPlot.connect(self.drawBG)

  def mouseClicked(self, event):
    '''
    Add a point to the current polygon.
    '''
    if event.button!=1 or event.inaxes is None or self.active_poly is None:
      return
    parent=self.main_window
    data=parent.active_data[parent.active_channel]
    x, y=event.xdata, int(round(event.ydata))
    y=min(max(y, 0), data.x.shape[0]-1)
    x=min(max(x, data.lamda[0]), data.lamda[-1])
    self.ui.polyTable.setItem(len(self.polygons), len(self.active_poly)*2 ,
                              QTableWidgetItem("%.3f"%x))
    self.ui.polyTable.setItem(len(self.polygons), len(self.active_poly)*2+1,
                              QTableWidgetItem(str(y)))
    self.ui.polyTable.resizeColumnsToContents()
    self.active_poly.append([x, y])
    if len(self.active_poly)==4:
      # polygon is complete, add it to the list and show it on the plot
      self.ui.polygonDisplay.setText('')
      self.polygons.append(self.active_poly)
      self.active_poly=None
      self.drawXTof()
      self.optionChanged()
    else:
      self.ui.polygonDisplay.setText('Click point %i'%(len(self.active_poly)+1))

  def addPolygon(self):
    '''
    Add a new polygon entry.
    '''
    self.active_poly=[]
    self.ui.polygonDisplay.setText('Click point 1')
    self.ui.polyTable.setRowCount(len(self.polygons)+1)

  def delPolygon(self):
    '''
    Remove one polygon from the list.
    '''
    idx=self.ui.polyTable.currentRow()
    if idx<0:
      return
    self.ui.polyTable.removeRow(idx)
    self.polygons.pop(idx)
    self.drawXTof()
    self.optionChanged()

  def clearPolygons(self):
    '''
    Remove all polygons.
    '''
    self.ui.polyTable.setRowCount(0)
    self.polygons=[]
    self.active_poly=None
    self.drawXTof()
    self.optionChanged()

  def polygonChanged(self, item):
    '''
    Update polygon points.
    '''
    row, col=item.row(), item.column()
    try:
      val=float(item.text())
    except:
      return
    if len(self.polygons)>row:
      self.polygons[row][col//2][col%2]=val
      self.drawXTof()
      self.optionChanged()

  def drawXTof(self):
    '''
    Display the x vs. ToF data to visualize the polygon areas.
    '''
    self.ui.xTof.clear()
    parent=self.main_window
    data=parent.active_data[parent.active_channel]
    self.ui.xTof.imshow(data.xtofdata[::-1], log=True,
                                 aspect='auto', cmap=parent.color,
                                 extent=[data.lamda[0], data.lamda[-1], 0, data.x.shape[0]-1])
    self.ui.xTof.set_xlabel(u'$\\lambda{}$ [Å]')
    self.ui.xTof.set_ylabel(u'x [pix]')
    if self.ui.polyregionActive.isChecked():
      for poly in self.polygons:
        if len(poly)<4:
          continue
        polygon=Polygon(array(poly), closed=True, alpha=0.25, color='black')
        self.ui.xTof.canvas.ax.add_patch(polygon)

    if parent.refl:
      x_pos=parent.refl.options['bg_pos']
      x_width=parent.refl.options['bg_width']
      rect=Rectangle((data.lamda[0], x_pos-x_width/2.), data.lamda[-1]-data.lamda[0],
                     x_width, alpha=0.15, color='red')
      self.last_bg=(x_pos, x_width)
      self.ui.xTof.canvas.ax.add_patch(rect)
    self.ui.xTof.draw()

  def drawBG(self):
    '''
    Display the specular and background intensity.
    '''
    self.ui.BG.clear()
    parent=self.main_window
    refl=parent.refl
    options=refl.options
    if not options['normalization']:
      return
    norm=options['normalization'].Rraw
    dnorm=options['normalization'].dRraw
    reg=norm>0
    lamda=refl.lamda[reg]
    # normalize all intensities by direct beam
    I=refl.I[reg]/norm[reg]
    dI=sqrt((refl.dI[reg]/norm[reg])**2+(refl.I[reg]/norm[reg]**2*dnorm[reg])**2)
    BGraw=refl.BGraw[reg]/norm[reg]
    dBGraw=sqrt((refl.dBGraw[reg]/norm[reg])**2+(refl.BGraw[reg]/norm[reg]**2*dnorm[reg])**2)
    BG=refl.BG[reg]/norm[reg]
    dBG=sqrt((refl.dBG[reg]/norm[reg])**2+(refl.BG[reg]/norm[reg]**2*dnorm[reg])**2)
    if (BG<=0).all():
      ymin=1e-10
    else:
      ymin=min(I[I>0].min(), BG[BG>0].min(), BGraw[BGraw>0].min())
    ymax=max(I.max(), BG.max(), BGraw.max())
    self.ui.BG.errorbar(lamda, I, yerr=dI, label='Specular', color='black')
    self.ui.BG.errorbar(lamda, BGraw, yerr=dBGraw, label='BGraw')
    self.ui.BG.errorbar(lamda, BG, yerr=dBG, label='Background')
    self.ui.BG.legend(loc=2)
    self.ui.BG.set_xlabel(u'$\\lambda{}$ [Å]')
    self.ui.BG.set_ylabel(u'I')
    self.ui.BG.set_yscale('log')
    self.ui.BG.canvas.ax.set_ylim(ymin*0.8, ymax*1.25)
    self.ui.BG.draw()
    if (options['bg_pos'], options['bg_width'])!=self.last_bg:
      # update the background region, if necessary
      self.drawXTof()

  def optionChanged(self):
    '''
    Recalculate the background and reflectivity when options have been changed.
    The updates of the dialog plots are triggered automatically.
    '''
    self.main_window.initiateReflectivityPlot.emit(True)

  def closeEvent(self, *args, **kwargs):
    # disconnect when closed as object is not actually destroyed and will slow down plots
    self.main_window.fileLoaded.disconnect(self.drawXTof)
    self.main_window.initiateReflectivityPlot.disconnect(self.drawBG)
    self.main_window.background_dialog=None
    return QDialog.closeEvent(self, *args, **kwargs)
