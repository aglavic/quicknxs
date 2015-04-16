import numpy as np

class ReductionSfCalculator(object):
	
	sf_gui = None
	caller_function_name = 'sfCalculator.calculate'
	table_settings = []
	index_col = [0,1,5,10,11,12,13,14,15]
	nbr_row = -1
	nbr_scripts = 0
	
	def __init__(cls, parent=None):
		cls.sf_gui = parent
		
		cls.collectTableSettings()
		cls.createScripts()
		
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
		
	def createScripts(cls):
		_data = cls.table_settings
		scripts = []

		from_to_index_same_lambda = cls.generateIndexSameLambda()
		nbr_scripts = cls.nbr_scripts
		
		incident_medium = cls.getIncidentMedium()
		output_file_name = clg.getOutputFileName()
		
		for i in range(nbr_scripts):
			from_index = from_to_index_same_lambda[i,0]
			to_index = from_to_index_same_lambda[i,1]

			string_runs = cls.getStringRuns(_data, from_index, to_index)
			list_peak_back = cls.getListPeakBack(_data, from_index, to_index)
			tof_range = clg.getTofRange(_data, from_index)
			


	def getStringRuns(cls, data, from_index, to_index):
		return ''

	def getListPeakBack(cls, data, from_index, to_index):
		return []
	
	def getIncidentMedium(cls):
		return ''
	
	def getOutputFileName(cls):
		return ''
	
	def getTofRange(cls):
		return []

	
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
