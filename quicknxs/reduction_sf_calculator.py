import numpy as np

class ReductionSfCalculator(object):
	
	sf_gui = None
	caller_function_name = 'sfCalculator.calculate'
	table_settings = []
	
	def __init__(cls, parent=None):
		cls.sf_gui = parent
		
		cls.collectTableSettings()
		print cls.table_settings
		
	def collectTableSettings(cls):
		nbr_row = cls.sf_gui.ui.tableWidget.rowCount()
		nbr_column = 8
		_table_settings = np.zeros((nbr_row, nbr_column))
		
		index_col = [0,1,10,11,12,13,14,15]
		
		for _row in range(nbr_row):
			for _col in range(nbr_column):
				if _col == 1:
					_value = str(cls.sf_gui.ui.tableWidget.cellWidget(_row, index_col[_col]).value())
				else:
					_value = str(cls.sf_gui.ui.tableWidget.item(_row, index_col[_col]).text())
				_table_settings[_row, _col] = _value
				
		cls.table_settings = _table_settings