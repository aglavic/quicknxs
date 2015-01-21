from PyQt4.QtGui import QDialog, QPalette, QCheckBox, QTableWidgetItem, QFileDialog
from display_metadata import Ui_Dialog as UiDialog
from mantid.simpleapi import *
from xml.dom import minidom
import numpy as np
import os
import utilities
import time

class DisplayMetadata(QDialog):
	
	#TODO HARDCODED STRING
	dom_filename = '/SNS/users/j35/nexus_metadata_list.xml'  #for testing only
	
	_open_instances = []
	active_data = None
	main_gui = None
	dom = None
	fields = None
	table = []
	list_metadata_selected = []
	mt_run = None
	
	def __init__(cls, main_gui, active_data, parent=None):
		QDialog.__init__(cls, parent=parent)
		cls.setWindowModality(False)
		cls._open_instances.append(cls)
		cls.ui = UiDialog()
		cls.ui.setupUi(cls)
		cls.ui.metadataTable.setColumnWidth(0,300)
		cls.ui.metadataTable.setColumnWidth(1,200)
		cls.ui.metadataTable.setColumnWidth(2,200)
		
		cls.ui.configureTable.setColumnWidth(0,70)
		cls.ui.configureTable.setColumnWidth(1,300)
		cls.ui.configureTable.setColumnWidth(2,300)
		cls.ui.configureTable.setColumnWidth(3,300)
		
		cls.main_gui = main_gui
		cls.active_data = active_data
		cls.init_gui()
		
		cls.retrieveListMetadataPreviouslySelected()
		cls.populateMetadataTable()
		cls.populateConfigTable()
		
	def clearMetadataTable(cls):
		_meta_table = cls.ui.metadataTable
		nbr_row = _meta_table.rowCount()
		for i in range(nbr_row):
			_meta_table.removeRow(0)
		_meta_table.show()
			
	def clearConfigTable(cls):
		_config_table = cls.ui.configureTable
		nbr_row = _config_table.rowCount()
		for i in range(nbr_row):
			_config_table.removeRow(0)
		_config_table.show()

	def populateMetadataTable(cls):
		cls.clearMetadataTable()
		list_metadata_selected = cls.list_metadata_selected
		if list_metadata_selected is None:
			cls.ui.saveMetadataAsAsciiButton.setEnabled(False)
			return
		else:
			nxs = cls.active_data.nxs
			cls.mt_run = nxs.getRun()
			list_keys = cls.mt_run.keys()
			_index = 0
			for _key in list_keys:
				if _key in list_metadata_selected:
					cls.ui.metadataTable.insertRow(_index)

					_name = _key
					_nameItem = QTableWidgetItem(_name)
					cls.ui.metadataTable.setItem(_index, 0, _nameItem)
					
					[value, units] = cls.retrieveValueUnits(_name)
					_valueItem = QTableWidgetItem(value)
					cls.ui.metadataTable.setItem(_index, 1, _valueItem)
					_unitsItem = QTableWidgetItem(units)
					cls.ui.metadataTable.setItem(_index, 2, _unitsItem)
					
					_index += 1
		cls.ui.saveMetadataAsAsciiButton.setEnabled(True)
		
	def populateConfigTable(cls):
		cls.clearConfigTable()
		nxs = cls.active_data.nxs
		cls.mt_run = nxs.getRun()
		list_keys = cls.mt_run.keys()
		
		_metadata_table = cls.list_metadata_selected
		
		_index = 0
		for _key in list_keys:
			cls.ui.configureTable.insertRow(_index)

			_name = _key

			_yesNo = QCheckBox()
			if _name in _metadata_table:
				_yesNo.setChecked(True)
			_yesNo.setText('')
			cls.ui.configureTable.setCellWidget(_index, 0, _yesNo)

			_nameItem = QTableWidgetItem(_name)
			cls.ui.configureTable.setItem(_index, 1, _nameItem)
			
			[value, units] = cls.retrieveValueUnits(_name)
			_valueItem = QTableWidgetItem(value)
			cls.ui.configureTable.setItem(_index, 2, _valueItem)
			_unitsItem = QTableWidgetItem(units)
			cls.ui.configureTable.setItem(_index, 3, _unitsItem)
			
			_index += 1
		
	def retrieveValueUnits(cls, _name):
		mt_run = cls.mt_run
		_value = mt_run.getProperty(_name).value
		if isinstance(_value, float):
			_value = str(_value)
		elif len(_value) == 1:
			_value = str(_value)
		elif type(_value) == type(""):
			_value = _value
		else:
			_value = '[' + str(_value[0]) + ',...]' + '-> (' + str(len(_value)) + ' entries)'
		_units = mt_run.getProperty(_name).units
		return [_value, _units]
		
	def retrieveListMetadataPreviouslySelected(cls):
		from quicknxs.config import metadataSelected
		metadataSelected.switch_config('listMetadata')
		listMetadataSelected = metadataSelected.metadata_list
		cls.list_metadata_selected = listMetadataSelected
		metadataSelected.switch_config('default')

	def init_gui(cls):
		dom = minidom.parse(cls.dom_filename)
		cls.fields = dom.getElementsByTagName('field')
		_full_file_name = cls.active_data.full_file_name

		nbr_row = len(cls.fields)
		nbr_column = len(_full_file_name)
		cls.table = np.empty((nbr_row, nbr_column), dtype=object)
		
		for i in range(nbr_column):
			_file_name = _full_file_name[i]
			_nxs = LoadEventNexus(Filename=str(_file_name))
	
	def close_gui(cls):
		cls.close()

	def getNodeValue(cls,node,flag):
		try:
			_tmp = node.getElementsByTagName(flag)
			_value = _tmp[0].childNodes[0].nodeValue
		except:
			_value = ''
		return _value
	
	def userChangedTab(cls, int):
		if int == 0: #user is back on metadata tab
			cls.list_metadata_selected = cls.getNewListMetadataSelected()
			cls.populateMetadataTable()
			
	def getNewListMetadataSelected(cls):
		_config_table = cls.ui.configureTable
		nbr_row = _config_table.rowCount()
		_list_metadata_selected = []
		for r in range(nbr_row):
			_is_selected = _config_table.cellWidget(r,0).isChecked()
			if _is_selected:
				_name = _config_table.item(r,1).text()
				_list_metadata_selected.append(_name)
		return _list_metadata_selected

	def saveListMetadataSelected(cls):
		_listMetadata = cls.list_metadata_selected
		from quicknxs.config import metadataSelected
		metadataSelected.switch_config('listMetadata')
		metadataSelected.metadata_list = _listMetadata
		metadataSelected.switch_config('default')

	def saveMetadataListAsAscii(cls):
		_filter = u'List Metadata (*_metadata.txt);;All(*.*)'
		_run_number = cls.active_data.run_number
		_default_name = cls.main_gui.path_ascii + '/' + _run_number + '_metadata.txt'
		filename = QFileDialog.getSaveFileName(cls, u'Save Metadata into ASCII',
		                                       _default_name,
		                                       filter=_filter)
		if filename == '':
			return
	
		cls.main_gui.path_config = os.path.dirname(filename)
		
		text = ['# Metadata Selected for run ' + _run_number]
		text.append('#Name - Value - Units')
		
		_metadata_table = cls.ui.metadataTable
		nbr_row = _metadata_table.rowCount()
		for r in range(nbr_row):
			_line = _metadata_table.item(r,0).text() + ' ' + str(_metadata_table.item(r,1).text()) + ' ' + 	str(_metadata_table.item(r,2).text())
			text.append(_line)
		utilities.write_ascii_file(filename, text)
	
	def exportConfiguration(cls):
		_filter = u"Metadata Configuration (*_metadata.cfg);; All (*.*)"
		_date = time.strftime("%d_%m_%Y")
		_default_name = cls.main_gui.path_config + '/' + _date + '_metadata.cfg'
		filename = QFileDialog.getSaveFileName(cls, u'Export Metadata Configuration',
		                                       _default_name,
		                                       filter = (_filter))
		if filename == '':
			return
		
		cls.main_gui.path_config = os.path.dirname(filename)
		
		list_metadata_selected = cls.list_metadata_selected
		text = []
		for _name in list_metadata_selected:
			text.append(_name)
			
		utilities.write_ascii_file(filename, text)

	def importConfiguration(cls):
		_filter = u"Metadata Configuration (*_metadata.cfg);; All (*.*)"
		_default_path = cls.main_gui.path_config
		filename = QFileDialog.getOpenFileName(cls, u'Import Metadata Configuration',
		                                       directory=_default_path,
		                                       filter=(_filter))
		if filename == '':
			return
		
		data = utilities.import_ascii_file(filename)
		cls.list_metadata_selected = data
		cls.checkTrueImportedMetadataFromConfigFile()
		
	def checkTrueImportedMetadataFromConfigFile(cls):
		list_metadata_selected = cls.list_metadata_selected
		_config_table = cls.ui.configureTable
		nbr_row = _config_table.rowCount()
		for r in range(nbr_row):
			_name = cls.ui.configureTable.item(r,1).text()
			_yesNo = QCheckBox()
			if _name in list_metadata_selected:
				_yesNo.setChecked(True)
			_yesNo.setText('')
			cls.ui.configureTable.setCellWidget(r, 0, _yesNo)

	def unselectAll(cls):
		_config_table = cls.ui.configureTable
		nbr_row = _config_table.rowCount()
		for r in range(nbr_row):
			_name = cls.ui.configureTable.item(r,1).text()
			_yesNo = QCheckBox()
			_yesNo.setText('')
			cls.ui.configureTable.setCellWidget(r, 0, _yesNo)

	def closeEvent(cls, event=None):
		cls.saveListMetadataSelected()
