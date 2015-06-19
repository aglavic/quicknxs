import numpy as np
from utilities import convertTOF, createAsciiFile
from mantid.simpleapi import *
from PyQt4 import QtGui
import sfCalculator
import time

class ReductionSfCalculator(object):
	
	sf_gui = None
	export_script_flag = False
	export_script_file = ''
	export_script = []
	table_settings = []
	index_col = [0,1,5,10,11,12,13,14,15]
	nbr_row = -1
	nbr_scripts = 0
	new_sfcalculator_script = True
	
	def __init__(cls, parent=None, export_script_flag=False):
		cls.sf_gui = parent
		cls.export_script_flag = export_script_flag
		
		if export_script_flag:
			_path = cls.sf_gui.main_gui.path_config
			_filter = u'python (*.py);;All (*.*)'
			filename = QtGui.QFileDialog.getSaveFileName(cls.sf_gui, 'Export Script File', _path, filter=_filter)
			if not(filename == ''):
				cls.export_script_file = filename
				cls.prepareExportScript()
			else:
				return
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
		cls.sf_gui.updateProgressBar(0.1)
		
		for i in range(nbr_scripts):
			from_index = int(from_to_index_same_lambda[i,0])
			to_index = int(from_to_index_same_lambda[i,1])

			if (to_index - from_index) <= 1:
				continue

			string_runs = cls.getStringRuns(from_index, to_index)
			list_peak_back = cls.getListPeakBack(from_index, to_index)
			tof_range = cls.getTofRange(from_index)
			
			if not cls.export_script:
				cls.launchScript(string_runs = string_runs,
					         list_peak_back = list_peak_back,
					         incident_medium = incident_medium,
					         output_file_name = output_file_name,
					         tof_range = tof_range)
			
				cls.refreshOutputFileContainPreview(output_file_name)
			else:
				cls.exportScript(string_runs = string_runs,
					         list_peak_back = list_peak_back,
					         incident_medium = incident_medium,
					         output_file_name = output_file_name,
					         tof_range = tof_range)
	
			cls.sf_gui.updateProgressBar(float(i+1)/float(nbr_scripts))
			QtGui.QApplication.processEvents()
		
		if cls.export_script_flag:
			createAsciiFile(cls.export_script_file, cls.export_script)

	def launchScript(cls, string_runs = '', list_peak_back=[], incident_medium = '', output_file_name = '', tof_range = []):
		if cls.new_sfcalculator_script:
			peak_ranges = []
			bck_ranges = []
			for item in list_peak_back:
				peak_ranges.append(int(item[0]))
				peak_ranges.append(int(item[1]))
				bck_ranges.append(int(item[2]))
				bck_ranges.append(int(item[3]))
			
			run_list = []
			att_list = []
			toks = string_runs.strip().split(',')
			for item in toks:
				pair = item.strip().split(':')
				run_list.append(int(pair[0]))
				att_list.append(int(pair[1]))
			
			LRScalingFactors(DirectBeamRuns = run_list,
			                 Attenuators = att_list,
			                 IncidentMedium = incident_medium,
			                 TOFRange = tof_range, TOFSteps = 200,
			                 SignalPeakPixelRange = peak_ranges, 
			                 SignalBackgroundPixelRange = bck_ranges,
			                 ScalingFactorFile= output_file_name)
			
		else:
			sfCalculator.calculate(string_runs = string_runs,
			                       list_peak_back = list_peak_back,
			                       incident_medium = incident_medium,
			                       output_file_name = output_file_name,
			                       tof_range = tof_range)

	def prepareExportScript(cls):
		script = []
		if cls.new_sfcalculator_script:			
			script.append('# quicksNXS LRScalingFactors scaling factor calculation script\n')
		else:
			script.append('# quicksNXS sfCalculator scaling factor calculation script\n')
		_date = time.strftime("%d_%m_%Y")
		script.append('# Script  automatically generated on ' + _date + '\n')
		script.append('\n')
		script.append('import os\n')
		script.append('import mantid\n')
		script.append('from mantid.simpleapi import *\n')
		if not cls.new_sfcalculator_script:
			script.append('import sfCalculator\n')
		cls.export_script = script

	def exportScript(cls, string_runs = '', list_peak_back=[], incident_medium = '', output_file_name = '', tof_range = []):
		filename = cls.export_script_file
		cls.export_script.append('\n')

		if cls.new_sfcalculator_script:
			peak_ranges = []
			bck_ranges = []
			for item in list_peak_back:
				peak_ranges.append(int(item[0]))
				peak_ranges.append(int(item[1]))
				bck_ranges.append(int(item[2]))
				bck_ranges.append(int(item[3]))
		
			run_list = []
			att_list = []
			toks = string_runs.strip().split(',')
			for item in toks:
				pair = item.strip().split(':')
				run_list.append(int(pair[0]))
				att_list.append(int(pair[1]))
		
			_script_exe = 'LRScalingFactors(DirectBeamRuns = ['
			str_run_list = ', '.join(map(lambda x: str(x), run_list))
			_script_exe += str_run_list + '], Attenuators = ['
			str_att_list = ', '.join(map(lambda x: str(x), att_list))
			_script_exe += str_att_list + '], IncidentMedium = '
			_script_exe += '"' + incident_medium + '", TOFRange = ['
			str_tof_list = ', '.join(map(lambda x: str(x), tof_range))
			_script_exe += str_tof_list + '], TOFSteps=200, '
			_script_exe += 'SignalBackgroundPixelRange=['
			str_peak_range = ', '.join(map(lambda x: str(x), peak_ranges))
			_script_exe += str_peak_range + '], SignalBackgroundPixelRange = ['
			str_back_range = ', '.join(map(lambda x: str(x), bck_ranges))
			_script_exe += str_back_range + '], ScalingFactorFile = "'
			_script_exe += output_file_name + '")'
			
			cls.export_script.append(_script_exe)
					
		else:
			_script_exe = 'sfCalculator.calculate(string_runs="%s",' %string_runs
			_script_exe += "list_peak_back=["
			
			[nbr_row, nbr_col] = list_peak_back.shape
			
			_list = []
			for _row in range(nbr_row):
				_peak_back = list_peak_back[_row]
				_term = "[%d,%d,%d,%d]"%(_peak_back[0], _peak_back[1], _peak_back[2], _peak_back[3])
				_list.append(_term)
			_script_exe += ",".join(_list) + "],"
			
			_script_exe += 'incident_medium="%s",' % incident_medium
			_script_exe += 'output_file_name="%s",' % output_file_name
			_script_exe += "tof_range=[%f,%f])\n" % (tof_range[0],tof_range[1]) 
			
			cls.export_script.append(_script_exe)

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
		print 'output_file_name:'
		print output_file_name
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
