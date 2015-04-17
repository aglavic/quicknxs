import numpy as np
from utilities import convertTOF
from mantid.simpleapi import *
import sfCalculator

class ReductionSfCalculator(object):
	
	sf_gui = None
	table_settings = []
	index_col = [0,1,5,10,11,12,13,14,15]
	nbr_row = -1
	nbr_scripts = 0
	
	def __init__(cls, parent=None):
		cls.sf_gui = parent
		
		cls.collectTableSettings()
		cls.createAndLaunchScripts()
		
	def collectTableSettings(cls):
		nbr_row = cls.sf_gui.ui.tableWidget.rowCount()
		cls.nbr_row = nbr_row
		nbr_column = len(cls.index_col)
		_table_settings = np.zeros((nbr_row, nbr_column))
		
		for _row in range(nbr_row):
			for _col in range(nbr_column):
				if _col == 1:
					_value = str(cls.sf_gui.ui.tableWidget.cellWidget(_row, cls.index_col[_col]).value())
				else:
					_value = str(cls.sf_gui.ui.tableWidget.item(_row, cls.index_col[_col]).text())
				_table_settings[_row, _col] = _value
				
		cls.table_settings = _table_settings
		
	def createAndLaunchScripts(cls):
		scripts = []

		from_to_index_same_lambda = cls.generateIndexSameLambda()
		nbr_scripts = cls.nbr_scripts
		
		incident_medium = cls.getIncidentMedium()
		output_file_name = cls.getOutputFileName()
		
		for i in range(nbr_scripts):
			from_index = int(from_to_index_same_lambda[i,0])
			to_index = int(from_to_index_same_lambda[i,1])

			if (to_index - from_index) <= 1:
				continue

			string_runs = cls.getStringRuns(from_index, to_index)
			list_peak_back = cls.getListPeakBack(from_index, to_index)
			tof_range = cls.getTofRange(from_index)
			
			cls.launchScript(string_runs = string_runs,
			                 list_peak_back = list_peak_back,
			                 incident_medium = incident_medium,
			                 output_file_name = output_file_name,
			                 tof_range = tof_range)
			
			cls.refreshOutputFileContainPreview(output_file_name)

	def launchScript(cls, string_runs = '', list_peak_back=[], incident_medium = '', output_file_name = '', tof_range = []):
		sfCalculator.calculate(string_runs = string_runs,
		                       list_peak_back = list_peak_back,
		                       incident_medium = incident_medium,
		                       output_file_name = output_file_name,
		                       tof_range = tof_range)

	def refreshOutputFileContainPreview(cls, output_file_name):
		cls.sf_gui.displayConfigFile(output_file_name)

	def getStringRuns(cls, from_index, to_index):
		data = cls.table_settings
		string_list = []
		for i in range(from_index, to_index+1):
			string_list.append(str(int(data[i,0])) + ":" + str(int(data[i,1])))
		return ",".join(string_list)

	def getListPeakBack(cls, from_index, to_index):
		data = cls.table_settings
		return data[from_index:to_index+1, 3:7]
	
	def getIncidentMedium(cls):
		return cls.sf_gui.ui.incidentMediumComboBox.currentText()
	
	def getOutputFileName(cls):
		output_file_name = cls.sf_gui.ui.sfFileNameLabel.text()
		return output_file_name
	
	def getTofRange(cls, from_index):
		data = cls.table_settings
		from_tof_ms = data[from_index, 7]
		to_tof_ms = data[from_index, 8 ]
		tof_from_to_micros = convertTOF([from_tof_ms, to_tof_ms], from_units='ms', to_units='micros')
		return tof_from_to_micros

	def generateIndexSameLambda(cls):
		_data = cls.table_settings

		lambda_list = _data[:,2]		
		nbr_scripts = len(set(lambda_list))
		cls.nbr_scripts = nbr_scripts
		
		from_to_index_same_lambda = np.zeros((nbr_scripts, 2))
		
		first_index_lambda = 0
		ref_lambda = lambda_list[0]
		index_script = 0
		for i in range(1,cls.nbr_row):
			live_lambda = lambda_list[i]
			if (live_lambda != ref_lambda):
				from_to_index_same_lambda[index_script,:] = [first_index_lambda, i-1]
				first_index_lambda = i
				ref_lambda = live_lambda
				index_script+= 1
			if  i == (cls.nbr_row-1):
				from_to_index_same_lambda[index_script,:] = [ first_index_lambda, i]

		return from_to_index_same_lambda
