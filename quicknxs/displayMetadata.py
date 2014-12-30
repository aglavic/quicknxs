from PyQt4.QtGui import QDialog, QPalette
from display_metadata import Ui_Dialog as UiDialog
from mantid.simpleapi import *
from xml.dom import minidom
import numpy as np

class DisplayMetadata(QDialog):
	
	dom_filename = '/SNS/users/j35/nexus_metadata_list.xml'  #for testing only
	
	_open_instances = []
	active_data = None
	main_gui = None
	dom = None
	fields = None
	table = []
	
	def __init__(self, main_gui, active_data, parent=None):
		QDialog.__init__(self, parent=parent)
		self.setWindowModality(False)
		self._open_instances.append(self)
		self.ui = UiDialog()
		self.ui.setupUi(self)
		
		self.main_gui = main_gui
		self.active_data = active_data
		self.init_gui()
		
	def init_gui(self):
		dom = minidom.parse(self.dom_filename)
		self.fields = dom.getElementsByTagName('field')
		_full_file_name = self.active_data.full_file_name

		nbr_row = len(self.fields)
		nbr_column = len(_full_file_name)
		self.table = np.empty((nbr_row, nbr_column), dtype=object)
		
		for i in range(nbr_column):
			_file_name = _full_file_name[i]
			_nxs = LoadEventNexus(Filename=str(_file_name))
			self.retrieve_and_populate_table(_nxs)
	
	def retrieve_and_populate_table(self, nxs):
		for node in self.fields:
			print self.getNodeValue(node,'name')
	
	def close_gui(self):
		self.close()

	def getNodeValue(self,node,flag):
		try:
		  _tmp = node.getElementsByTagName(flag)
		  _value = _tmp[0].childNodes[0].nodeValue
		except:
		  _value = ''
		return _value
	