#-*- coding: utf-8 -*-
'''
A Widget that displays raw data information of a given .nxs file.
'''

import h5py
from PyQt4.QtGui import QDialog, QWidget, QVBoxLayout, QTreeWidgetItem
from numpy import maximum
from .nxs_widget import Ui_NXSWidget

class PathTreeItem(QTreeWidgetItem):
    '''
    A tree widget item that stores a path string.
    '''
    itemPath=None

TEXT_TEMPLATE='''<b>Selected Node Path:</b><br />
 %s
<br /><br />

<b>Attributes:</b>
<table border="1">
    <tr><th>Name</th><th>Value</th></tr>
    %s
</table>

%s
'''

class NXSWidget(QWidget):
  '''
  A widget displaying the contents of a .nxs file with a path tree,
  data plotter and information text widget.
  '''
  active_file=None

  def __init__(self, parent=None, active_file=None):
    QWidget.__init__(self, parent)
    self.ui=Ui_NXSWidget()
    self.ui.setupUi(self)
    if active_file is not None:
      self.loadFile(active_file)

  def loadFile(self, active_file):
    self.active_file=active_file
    self.nxs=h5py.File(active_file, 'r')
    self.buildTree()

  def buildTree(self):
    '''
    Build the tree for all entries in the .nxs file.
    '''
    self.ui.nodeTree.clear()
    tw=self.ui.nodeTree
    for name, entry in self.nxs.items():
      root_widget=QTreeWidgetItem(tw, [name])
      self.buildSubtree(root_widget, entry)

  def buildSubtree(self, widget, item):
    '''
    Recursively build tree items for all nodes of one .nxs entry.
    Each item has its path attached, so it can easily be retrieved later.
    '''
    for name, subitem in item.items():
      sub_widget=PathTreeItem(widget, [name])
      sub_widget.itemPath=subitem.name
      if hasattr(subitem, 'items'):
        self.buildSubtree(sub_widget, subitem)


  def itemChanged(self, item, ignore):
    '''
    Collect the attributes and data for the selected node.
    If the node is a 1D or 2D array, a plot is created.
    '''
    self.ui.nodePlotter.clear()
    if type(item) is PathTreeItem:
      node=self.nxs[item.itemPath]
      # show node attributes
      attr_txt=u''
      for name, value in node.attrs.items():
        attr_txt+='<tr><td>%s</td><td>%s</td></tr>\n'%(name, value)
      # show node values, if it has any
      value_txt=u''
      if hasattr(node, 'value'):
        data=node.value
        if data.shape==(1,):
          value_txt=u'<br /><b>Value:</b><br />%s\n'%data[0]
        elif len(data.shape)==1:
          value_txt=u'<br /><b>Value:</b><br />Array[%i]:<br />%s\n'%(data.shape[0], data)
        else:
          value_txt=u'<br /><b>Value:</b><br />Array[%s]\n'%repr(data.shape)
        if len(data.shape)<3 and data.shape[0]>1:
          self.plotData(data)
      else:
        # show child node values for e.g. motors for convenience
        head_added=False
        for subvalue in ['value', 'average_value', 'minimum_value', 'maximum_value']:
          if subvalue in node and node[subvalue].value.shape==(1,):
            if not head_added:
              head_added=True
              attr_txt+='</table>\n<b>Child Node Values:</b>\n<table border="1">\n'
              attr_txt+='<tr><th>Name</th><th>Value</th></tr>\n'
            attr_txt+='<tr><td>%s</td><td>%s</td></tr>\n'%(subvalue, node[subvalue].value[0])
      self.ui.nodeInfo.setText(TEXT_TEMPLATE%(item.itemPath, attr_txt, value_txt))
    else:
      # for root items just display the name
      self.ui.nodeInfo.setText(item.text(0))
    self.ui.nodePlotter.draw()

  def plotData(self, data):
    self.ui.nodePlotter.clear_fig()
    if len(data.shape)==1:
      self.ui.nodePlotter.plot(data)
    else:
      cmap=self.ui.nodePlotter.imshow(maximum(data.transpose(), 0.1),
                                      aspect='auto', origin='lower')
      #self.ui.nodePlotter.canvas.fig.colorbar(cmap)


class NXSDialog(QDialog):
  '''
  A QDialog with a NXSWidget in it.
  '''

  def __init__(self, parent=None, active_file=None):
    QDialog.__init__(self, parent)
    vbox=QVBoxLayout(self)
    vbox.setMargin(0)
    if active_file is not None:
      self.setWindowTitle(u'NXS Browser - %s'%active_file)
    self.nxs_widget=NXSWidget(self, active_file)
    vbox.addWidget(self.nxs_widget)
    self.resize(700, 700)
    self.nxs_widget.ui.splitter.setSizes([400, 260])
    self.nxs_widget.ui.splitter_2.setSizes([200, 460])
