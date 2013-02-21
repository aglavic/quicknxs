#-*- coding: utf-8 -*-
'''
  Module for advanced definition of background subtraction.
'''

from PyQt4.QtGui import QDialog, QTableWidgetItem
from matplotlib.patches import Polygon
from matplotlib.nxutils import points_inside_poly
from numpy import array, meshgrid
from .background_dialog import Ui_Dialog

class BackgroundDialog(QDialog):

  def __init__(self, parent):
    QDialog.__init__(self, parent)
    self.main_window=parent
    self.ui=Ui_Dialog()
    self.ui.setupUi(self)
    self.polygons=[]
    self.active_poly=None
    self.ui.xTof.canvas.mpl_connect('button_press_event', self.mouseClicked)

  def mouseClicked(self, event):
    '''
    Add a point to the current polygon.
    '''
    if event.button!=1 or event.xdata is None or self.active_poly is None:
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
      self.ui.polygonDisplay.setText('')
      self.polygons.append(self.active_poly)
      self.active_poly=None
      self.drawXTof()
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
    idx=self.ui.polyTable.currentRow()
    if idx<0:
      return
    self.ui.polyTable.removeRow(idx)
    self.polygons.pop(idx)
    self.drawXTof()

  def clearPolygons(self):
    self.ui.polyTable.setRowCount(0)
    self.polygons=[]
    self.active_poly=None
    self.drawXTof()

  def polygonChanged(self, item):
    row, col=item.row(), item.column()
    try:
      val=float(item.text())
    except:
      return
    if len(self.polygons)>row:
      self.polygons[row][col//2][col%2]=val
      self.drawXTof()

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
    self.ui.xTof.set_xlabel(u'λ [Å]')
    self.ui.xTof.set_ylabel(u'x [pix]')
    if self.ui.polyregionActive.isChecked():
      for poly in self.polygons:
        if len(poly)<4:
          continue
        polygon=Polygon(array(poly), closed=True, alpha=0.25, color='black')
        self.ui.xTof.canvas.ax.add_patch(polygon)
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
    reg=norm>0
    lamda=refl.lamda[reg]
    I=refl.I[reg]/norm[reg]
    dI=refl.dI[reg]/norm[reg]
    BGraw=refl.BGraw[reg]/norm[reg]
    dBGraw=refl.dBGraw[reg]/norm[reg]
    BG=refl.BG[reg]/norm[reg]
    dBG=refl.dBG[reg]/norm[reg]
    ymin=min(I[I>0].min(), BG[BG>0].min(), BGraw[BGraw>0].min())
    ymax=max(I.max(), BG.max(), BGraw.max())
    self.ui.BG.errorbar(lamda, I, yerr=dI, label='Specular', color='black')
    self.ui.BG.errorbar(lamda, BGraw, yerr=dBGraw, label='BGraw')
    self.ui.BG.errorbar(lamda, BG, yerr=dBG, label='Background')
    self.ui.BG.legend(loc=2)
    self.ui.BG.set_xlabel(u'λ [Å]')
    self.ui.BG.set_ylabel(u'I')
    self.ui.BG.set_yscale('log')
    self.ui.BG.canvas.ax.set_ylim(ymin*0.8, ymax*1.25)
    self.ui.BG.draw()

  def getRegion(self):
    parent=self.main_window
    data=parent.active_data[parent.active_channel]
    X, Lamda=meshgrid(data.x, data.lamda)
    inside=X.flatten()<0
    for poly in self.polygons:
      inside=inside|points_inside_poly(array([Lamda.flatten(), X.flatten()]).transpose(),
                              array(poly))
#    lamdas=unique(Lamda.flatten()[inside])
    return inside.reshape(X.shape)

  def optionChanged(self):
    self.main_window.initiateReflectivityPlot.emit(True)
