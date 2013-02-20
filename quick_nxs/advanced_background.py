#-*- coding: utf-8 -*-
'''
  Module for advanced definition of background subtraction.
'''

from PyQt4.QtGui import QDialog, QTableWidgetItem
from matplotlib.patches import Polygon
from matplotlib.nxutils import points_inside_poly
from numpy import array, meshgrid, unique
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
    self.drawXTof()
    #self.drawBG()

  def mouseClicked(self, event):
    if event.button!=1 or event.xdata is None or self.active_poly is None:
      return
    parent=self.main_window
    data=parent.active_data[parent.active_channel]
    x, y=event.xdata, int(round(event.ydata))
    y=min(max(y, 0), data.x.shape[0]-1)
    x=min(max(x, data.lamda[0]), data.lamda[-1])
    self.ui.polyTable.setItem(len(self.polygons), len(self.active_poly)*2+1 ,
                              QTableWidgetItem("%.3f"%x))
    self.ui.polyTable.setItem(len(self.polygons), len(self.active_poly)*2,
                              QTableWidgetItem(str(y)))
    self.ui.polyTable.resizeColumnsToContents()
    self.active_poly.append((x, y))
    if len(self.active_poly)==4:
      self.ui.polygonDisplay.setText('')
      self.polygons.append(self.active_poly)
      poly=Polygon(array(self.active_poly), closed=True, alpha=0.25, color='black')
      self.ui.xTof.canvas.ax.add_patch(poly)
      self.ui.xTof.draw()
      print self.getRegion().sum()
      self.active_poly=None
    else:
      self.ui.polygonDisplay.setText('Click point %i'%(len(self.active_poly)+1))


  def addPolygon(self):
    self.active_poly=[]
    self.ui.polygonDisplay.setText('Click point 1')
    self.ui.polyTable.setRowCount(len(self.polygons)+1)


  def drawXTof(self):
    self.ui.xTof.clear()
    parent=self.main_window
    data=parent.active_data[parent.active_channel]
    self.ui.xTof.imshow(data.xtofdata[::-1], log=True,
                                 aspect='auto', cmap=parent.color,
                                 extent=[data.lamda[0], data.lamda[-1], 0, data.x.shape[0]-1])
    self.ui.xTof.set_xlabel(u'λ [Å]')
    self.ui.xTof.set_ylabel(u'x [pix]')
    self.ui.xTof.draw()

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
