import numpy as np

class ReductionSfCalculator(object):
	
	sf_gui = None
	caller_function_name = 'sfCalculator.calculate'
	table_settings = []
	index_col = [0,1,5,10,11,12,13,14,15]
	nbr_row = -1
	
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
		
		lambda_list = _data[:,2]		
		nbr_scripts = len(set(lambda_list))
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


