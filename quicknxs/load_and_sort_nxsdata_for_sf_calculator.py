from mantid.simpleapi import *
from qreduce import NXSData
from sort_nxsdata import SortNXSData
from decorators import waiting_effects
import numpy as np
from PyQt4.QtGui import QTableWidgetItem
import nexus_utilities

class LoadAndSortNXSDataForSFcalculator(object):
	
	list_runs = []
	loaded_list_runs = []
	list_NXSData = []
	list_NXSData_sorted = []
	list_metadata = ['gd_prtn_chrg', 'S1HWidth','S1VHeight',
	                 'S2HWidth','S2VHeight','SiHWidth','SiVHeight',
	                 'LambdaRequest','vATT']
	big_table = []
	is_using_Si_slits = False
	
	def __init__(cls, list_runs):
		cls.list_runs = list_runs
		cls.loadNXSData()
		cls.sortNXSData()
		cls.fillTable()
	
	@waiting_effects	
	def loadNXSData(cls):
		cls.list_NXSData = []
		_list_runs = cls.list_runs
		for _runs in _list_runs:
			_full_file_name = cls.findFullFileName(_runs)
			if _full_file_name != '':
				_data = NXSData(_full_file_name, bins=500)
				if _data is not None:
					cls.list_NXSData.append(_data)
					cls.loaded_list_runs.append(_runs)
				
	def sortNXSData(cls):
		if cls.list_NXSData == []:
			return
		oSortNXSDataArray = SortNXSData(cls.list_NXSData)
		cls.list_NXSData_sorted = oSortNXSDataArray.getSortedList()

	def fillTable(cls):
		_list_NXSData_sorted = cls.list_NXSData_sorted
		if _list_NXSData_sorted == []:
			return
		nbr_row = len(_list_NXSData_sorted)
		nbr_column = len(cls.list_metadata) + 1 # +1 for the run number
		big_table = np.empty((nbr_row, nbr_column))
		index_row = 0
		for _nxs in _list_NXSData_sorted:
			_active_data = _nxs.active_data
			
			_run_number = _active_data.run_number
			_nbr_attenuator = _active_data.attenuatorNbr
			_lambda_min = _active_data.lambda_range[0]
			_lambda_max = _active_data.lambda_range[1]
			_proton_charge = _active_data.proton_charge
			_lambda_requested = _active_data.lambda_requested
			_S1W = _active_data.S1H
			_S1H = _active_data.S1W
			cls.is_using_Si_slits = _active_data.isSiThere
			if _active_data.isSiThere:
				_Si2W = _active_data.SiW
				_Si2H = _active_data.SiH
			else:
				_Si2W = _active_data.S2W
				_Si2H = _active_data.S2H
			
			_row = [_run_number,
			        _nbr_attenuator, 
			        _lambda_min,
			        _lambda_max,
			        _proton_charge,
			        _lambda_requested,
			        _S1W, _S1H,
			        _Si2W, _Si2H]
			big_table[index_row, :] = _row
			index_row += 1
		cls.big_table = big_table
	
	def isSiThere(cls):
		return cls.is_using_Si_slits
				
	def retrieveMetadataValue(cls, _name):
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
		return _value
		
	def findFullFileName(cls, run_number):
		try:
			full_file_name = nexus_utilities.findNeXusFullPath(run_number)
		except:
			full_file_name = ''
		return full_file_name
	
	def getTableData(cls):
		return cls.big_table
	
	def getListOfRunsLoaded(cls):
		return cls.loaded_list_runs
	
	def getListNXSDataSorted(cls):
		return cls.list_NXSData_sorted