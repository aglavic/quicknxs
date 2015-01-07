from clear_plots import ClearPlots
from display_plots import DisplayPlots
from open_run_number import OpenRunNumber
from PyQt4 import QtGui

class SelectionBigTableChanged(object):
	
	self = None
	current_row = None
	current_column = None
	is_data = True
	active_data = None
	
	def __init__(cls, self, row, column):
		cls.self = self
		cls.current_row = row
		cls.current_column = column
		
		if cls.same_cell_selected():
			return
		
		if column == 6:
			col_index = 1
			cls.is_data = False
		else:
			col_index = 0
		row_index = row
		self.ui.dataNormTabWidget.setCurrentIndex(col_index)
		
		_active_data = cls.retrieve_active_data(row_index, col_index)
		self.active_data = _active_data
		cls.active_data = _active_data
		
		cls.record_new_row_col_selected()
		cls.load_and_display_cell()
				
	def load_and_display_cell(cls):
		cell = cls.self.ui.reductionTable.selectedItems()
		if cell == [] or cell[0] == '' or cell[0].text() == '':
			ClearPlots(cls.self, is_data=cls.is_data, is_norm=not cls.is_data, all_plots=True)
		else:
			cell = cell[0]
			if (cls.active_data is not None) and (cls.active_data.nxs is not None):
				DisplayPlots(cls.self)
			else:
				OpenRunNumber(cls.self, cell, replaced_data=True)
		
	def record_new_row_col_selected(cls):
		cls.self._prev_row_selected = cls.current_row
		cls.self._prev_col_selected = cls.current_column
		
	def retrieve_active_data(cls, row, col):
		_data = cls.self.bigTableData[row, col]
		try:
			active_data = _data.active_data
		except:
			active_data = None
		return active_data

	def same_cell_selected(cls):
		if (cls.self._prev_row_selected == cls.current_row) and (cls.self._prev_col_selected == cls.current_column):
			return True
		if (cls.self._prev_row_selected == cls.current_row) and (cls.self._prev_col_selected < 6) and (cls.current_column < 6):
			return True
		return False