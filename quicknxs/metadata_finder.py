from PyQt4.QtGui import QDialog, QPalette, QTableWidgetItem, QCheckBox
from PyQt4.QtCore import Qt
from metadata_finder_interface import Ui_Dialog as UiDialog
from mantid.simpleapi import *
from run_sequence_breaker import RunSequenceBreaker
from decorators import waiting_effects
import utilities
import os

class MetadataFinder(QDialog):
	
	_open_instances = []
	main_gui = None
#	filename0 = ''
	list_metadata_selected = []
	list_nxs = []
	list_filename = []
	list_runs = []
	
	def __init__(cls, main_gui, parent=None):
		cls.main_gui = main_gui
		
		QDialog.__init__(cls, parent=parent)
		cls.setWindowModality(False)
		cls._open_instances.append(cls)
		cls.ui = UiDialog()
		cls.ui.setupUi(cls)
		
		cls.initGui()
		cls.retrieveListMetadataPreviouslySelected()
		
	def initList(cls):
		cls.list_runs = []
		cls.list_filename= []
		cls.list_nxs = []
	
	def initGui(cls):
		cls.ui.inputErrorLabel.setVisible(False)
		palette = QPalette()
		palette.setColor(QPalette.Foreground, Qt.red)
		cls.ui.inputErrorLabel.setPalette(palette)
		
		cls.ui.configureTable.setColumnWidth(0,70)
		cls.ui.configureTable.setColumnWidth(1,300)
		cls.ui.configureTable.setColumnWidth(2,300)
		cls.ui.configureTable.setColumnWidth(3,300)
		
	def retrieveListMetadataPreviouslySelected(cls):
		from quicknxs.config import metadataSelected
		metadataSelected.switch_config('listMetadata')
		listMetadataSelected = metadataSelected.metadata_list
		cls.list_metadata_selected = listMetadataSelected
		metadataSelected.switch_config('default')
		
	def clearMetadataTable(cls):
		_meta_table = cls.ui.metadataTable
		nbr_row = _meta_table.rowCount()
		for i in range(nbr_row):
			_meta_table.removeRow(0)
		_meta_table.show()

	def clearConfigureTable(cls):
		_config_table = cls.ui.configureTable
		nbr_row = _config_table.rowCount()
		for i in range(nbr_row):
			_config_table.removeRow(0)
		_config_table.show()
			
	@waiting_effects
	def runNumberEditEvent(cls):
		cls.initList()
		cls.clearMetadataTable()
		cls.populateMetadataTable()
		cls.populateconfigureTable()
		
	def populateconfigureTable(cls):
		cls.clearConfigureTable()
		_filename = cls.list_filename[0]
		nxs = LoadEventNexus(Filename=_filename)
		list_keys = nxs.getRun().keys()
		_metadata_table = cls.list_metadata_selected

		_index = 0
		for _key in list_keys:
			cls.ui.configureTable.insertRow(_index)

			_yesNo = QCheckBox()
			_name = _key
			if _name in _metadata_table:			
				_yesNo.setChecked(True)
			_yesNo.setText('')
			cls.ui.configureTable.setCellWidget(_index, 0, _yesNo)

			_nameItem = QTableWidgetItem(_name)
			cls.ui.configureTable.setItem(_index, 1, _nameItem)
			
			[value, units] = cls.retrieveValueUnits(nxs.getRun(),_name)
			_valueItem = QTableWidgetItem(value)
			cls.ui.configureTable.setItem(_index, 2, _valueItem)
			_unitsItem = QTableWidgetItem(units)
			cls.ui.configureTable.setItem(_index, 3, _unitsItem)
			
			_index += 1
			
	def retrieveValueUnits(cls, mt_run, _name):
		_name = str(_name)
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

	def populateMetadataTable(cls):
		cls.clearMetadataTable()
		run_sequence = cls.ui.runNumberEdit.text()
		oListRuns = RunSequenceBreaker(run_sequence)
		_list_runs = oListRuns.getFinalList()
		if _list_runs[0] == -1:
			return
		
		if _list_runs[0] == -2:
			cls.ui.inputErrorLabel.setVisible(True)
			return
		
		cls.ui.inputErrorLabel.setVisible(False)
		list_metadata_selected = cls.list_metadata_selected
		
		_header = ['Run #','IPTS']
		for name in list_metadata_selected:
			cls.ui.metadataTable.insertColumn(2)
			_header.append(name)
		cls.ui.metadataTable.setHorizontalHeaderLabels(_header)
		list_nxs = cls.list_nxs
		
		_index = 0
		for _runs in _list_runs:
			cls.ui.metadataTable.insertRow(_index)
			
			_filename = FileFinder.findRuns("REF_L%d" %_runs)[0]
			cls.list_filename.append(_filename)
			_nxs = LoadEventNexus(Filename=_filename)
			cls.list_nxs.append(_nxs)
			cls.list_runs.append(_runs)
			mt_run = _nxs.getRun()

			_runItem = QTableWidgetItem(str(_runs))
			cls.ui.metadataTable.setItem(_index, 0, _runItem)

			_ipts = cls.getIPTS(_filename)
			_iptsItem = QTableWidgetItem(_ipts)
			cls.ui.metadataTable.setItem(_index, 1, _iptsItem)
			
			column_index = 0			
			for name in list_metadata_selected:
				[value,units] = cls.retrieveValueUnits(mt_run, name)
				_str = str(value) + ' ' + str(units)
				_item = QTableWidgetItem(_str)
				cls.ui.metadataTable.setItem(_index, 2+column_index, _item)
				column_index += 1
			
			_index += 1
			
		
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
		
	def saveListMetadataSelected(cls):
		_listMetadata = cls.list_metadata_selected
		from quicknxs.config import metadataSelected
		metadataSelected.switch_config('listMetadata')
		metadataSelected.metadata_list = _listMetadata
		metadataSelected.switch_config('default')
		
	def saveMetadataListAsAscii(cls):
		_filter = u'List Metadata (*_metadata.txt);;All(*.*)'
		_run_number = cls.run0
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
	
	def getIPTS(cls, filename):
		parse_path = filename.split('/')
		return parse_path[3]
	
	