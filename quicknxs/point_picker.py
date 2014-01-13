#-*- coding: utf-8 -*-
'''
A dialog to delete unwanted points from a reflectivity curve.
'''

import numpy as np
from os import path
from PyQt4.QtGui import QDialog, QTableWidgetItem
from .point_picker_dialog import Ui_Dialog

class PointPicker(QDialog):
  '''
  A dialog to delete unwanted points from a reflectivity curve.
  '''
  origin_file=None
  _table_change_active=False
  filtered_idxs=None

  def __init__(self, fname, pre_filter=None):
    QDialog.__init__(self)
    self.ui=Ui_Dialog()
    self.ui.setupUi(self)
    self.setWindowTitle(u'Point Picker - %s'%fname)
    self.origin_file=fname
    self.read_filedata()
    self.fill_table()
    if pre_filter:
      self.apply_filter(pre_filter)
    self.plot()
    self.ui.plot.canvas.mpl_connect('button_press_event', self.pickPoint)

  def read_filedata(self):
    '''
    Read the ascii data of the origin file.
    '''
    data=np.loadtxt(self.origin_file, comments='#', unpack=True)
    self.Qz=data[0]
    self.dQz=data[3]
    self.R=data[1]
    self.dR=data[2]
    self.ai=data[4]
    # start by showing all points
    self.plot_region=(self.ai==self.ai)

  def fill_table(self):
    '''
    Format the numbers of the origin data and put them into the table.
    '''
    self._table_change_active=True

    table=self.ui.pointTable
    table.clearSelection()
    table.setRowCount(0)
    table.setRowCount(len(self.ai))
    for i, (ai, Qz, R) in enumerate(zip(self.ai, self.Qz, self.R)):
        item=QTableWidgetItem("%.3f"%ai)
        table.setItem(i, 0, item)
        item=QTableWidgetItem("%.5f"%Qz)
        table.setItem(i, 1, item)
        item=QTableWidgetItem("%.2e"%R)
        table.setItem(i, 2, item)
    table.resizeColumnsToContents()
    col_widths=table.columnWidth(0)+table.columnWidth(1)+table.columnWidth(2)
    self.ui.splitter.setSizes([col_widths+60, self.size().width()-68-col_widths])
    self._table_change_active=False

  def apply_filter(self, flist):
    '''
    Activate line indices corresponding to a given list.
    '''
    self._table_change_active=True
    table=self.ui.pointTable
    rows=table.rowCount()
    for idx in flist:
      if idx>=rows or idx<0:
        continue
      table.selectRow(idx)
    self._table_change_active=False
    self.selectionChanged(do_plot=False)

  def plot(self):
    '''
    Draw lines for the filtered data colored by incident angle values and
    black dots for removed points. 
    '''
    plot=self.ui.plot

    # collect information about the current view
    if len(plot.toolbar._views)>0:
      spos=plot.toolbar._views._pos
      view=plot.toolbar._views[spos]
      position=plot.toolbar._positions[spos]
    else:
      view=None

    plot.clear()
    # collect filtered data
    reg=self.plot_region
    ai=self.ai[reg]
    Qz=self.Qz[reg]
    R=self.R[reg]
    dR=self.dR[reg]
    ais=np.unique(ai)
    # draw plots for all different ai values in different colors
    for aii in ais:
      subreg=(ai==aii)
      plot.errorbar(Qz[subreg], R[subreg], dR[subreg], label=u'α$_i$=%.3f'%aii)
    # draw points filtered
    Qz_filtered=self.Qz[np.logical_not(reg)]
    R_filtered=self.R[np.logical_not(reg)]
    plot.plot(Qz_filtered, R_filtered, 'ok', markersize=2, label=u'filtered')
    plot.set_yscale('log')
    plot.set_xlabel('Q$_z$')
    plot.set_ylabel('R')
    plot.legend()

    # keep old zoom position
    if view is not None:
      plot.toolbar.push_current()
      plot.toolbar._views.push(view)
      plot.toolbar._positions.push(position)
      plot.toolbar._update_view()
    plot.draw()

  def selectionChanged(self, do_plot=True):
    '''
    The selected rows in the table have changed so the plot_region gets
    updated and the plot is redrawn.
    '''
    if self._table_change_active:
      return
    table=self.ui.pointTable
    selection=table.selectedItems()
    self.plot_region[:]=True
    for item in selection:
      iindex=table.indexFromItem(item)
      row=iindex.row()
      self.plot_region[row]=False
    if do_plot:
      self.plot()

  def pickPoint(self, event):
    '''
    Callback for mouse button pressed on plot.
    '''
    if self.ui.plot.toolbar._active is None and event.button==1 and \
      event.xdata is not None:
      # no tool is selected and a button was pressed inside the plot
      x, y=event.xdata, event.ydata
      dist=abs(self.Qz-x)
      idx=dist.argmin()
      self.ui.pointTable.selectRow(idx)

  def accept(self):
    '''
    Called when the OK button was pressed. Exports the filtered data
    to a new file, adding a specific header entry containing the
    filtered row numbers.
    '''
    fpath, fname=path.split(self.origin_file)
    pre, post=fname.rsplit('_', 1)
    outfile=path.join(fpath, pre+'_filtered_'+post)
    original_lines=open(self.origin_file, 'r').readlines()
    output=open(outfile, 'w')
    # collect indices of filtered regions
    reg=self.plot_region
    self.filtered_idxs=np.arange(len(self.Qz))[np.logical_not(reg)].tolist()

    for oline in original_lines:
      if oline.startswith('#'):
        if '[Data]' in oline:
          # insert additional header info for filtering
          output.write('# [Filtered Indices]')
          output.write('\n# Original File: %s\n# Filtered Indices: ('%self.origin_file)
          for idx in self.filtered_idxs:
            output.write(str(idx)+', ')
          output.write(')\n#\n')
        output.write(oline)
      else:
        break
    value=np.array([self.Qz[reg], self.R[reg], self.dR[reg], self.dQz[reg], self.ai[reg]])
    np.savetxt(output, value.T, delimiter='\t', fmt='%-18e')
    output.close()
    QDialog.accept(self)
