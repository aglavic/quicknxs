from PyQt4.QtGui import QDialog, QPalette, QTableWidgetItem, QCheckBox
from PyQt4.QtCore import Qt
from metadata_finder_interface import Ui_Dialog as UiDialog
from mantid.simpleapi import *
from run_sequence_breaker import RunSequenceBreaker
from decorators import waiting_effects

class MetadataFinder(QDialog):
	
	_open_instances = []
	main_gui = None
	filename0 = ''
	
	def __init__(cls, main_gui, parent=None):
		cls.main_gui = main_gui
		
		QDialog.__init__(cls, parent=parent)
		cls.setWindowModality(False)
		cls._open_instances.append(cls)
		cls.ui = UiDialog()
		cls.ui.setupUi(cls)
		
		cls.initGui()
		
	def initGui(cls):
		cls.ui.inputErrorLabel.setVisible(False)
		palette = QPalette()
		palette.setColor(QPalette.Foreground, Qt.red)
		cls.ui.inputErrorLabel.setPalette(palette)
		
		cls.ui.configureTable.setColumnWidth(0,70)
		cls.ui.configureTable.setColumnWidth(1,300)
		cls.ui.configureTable.setColumnWidth(2,300)
		cls.ui.configureTable.setColumnWidth(3,300)
		
		
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
		cls.clearMetadataTable()
		cls.populateMetadataTable()
		cls.populateconfigureTable()
		
	def populateconfigureTable(cls):
		cls.clearConfigureTable()
		_filename = cls.filename0
		nxs = LoadEventNexus(Filename=_filename)
		list_keys = nxs.getRun().keys()
		_index = 0
		for _key in list_keys:
			cls.ui.configureTable.insertRow(_index)

			_yesNo = QCheckBox()
			_yesNo.setChecked(False)
			_yesNo.setText('')
			cls.ui.configureTable.setCellWidget(_index, 0, _yesNo)

			_name = _key
			_nameItem = QTableWidgetItem(_name)
			cls.ui.configureTable.setItem(_index, 1, _nameItem)
			
			[value, units] = cls.retrieveValueUnits(nxs.getRun(),_name)
			_valueItem = QTableWidgetItem(value)
			cls.ui.configureTable.setItem(_index, 2, _valueItem)
			_unitsItem = QTableWidgetItem(units)
			cls.ui.configureTable.setItem(_index, 3, _unitsItem)
			
			_index += 1
			
	def retrieveValueUnits(cls, mt_run, _name):
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
		
		_index = 0
		for _runs in _list_runs:
			cls.ui.metadataTable.insertRow(_index)
			
			_filename = FileFinder.findRuns("REF_L%d" %_runs)[0]
			if _index ==0:
				cls.filename0 = _filename
			_runItem = QTableWidgetItem(str(_runs))
			cls.ui.metadataTable.setItem(_index, 0, _runItem)

			_ipts = cls.getIPTS(_filename)
			_iptsItem = QTableWidgetItem(_ipts)
			cls.ui.metadataTable.setItem(_index, 1, _iptsItem)
			
			_index += 1
			
			
			
			
	def getIPTS(cls, filename):
		parse_path = filename.split('/')
		return parse_path[3]
		
		