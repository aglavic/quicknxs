from mantid.simpleapi import *
from logging import info
from qreduce import NXSData
from display_plots import DisplayPlots

class OpenRunNumber(object):
	
	self = None
	run_number_found = []
	replaced_data = False
	
	def __init__(cls, self, cell=None, replaced_data=False):
		cls.self = self
		cls.replaced_data = replaced_data
		
		run_found = []
		run_not_found = []
		cls.run_number_found = []
		
		if cell is None:
			run_number_field = self.ui.numberSearchEntry.text()
		else:
			run_number_field = cell.text()
		run_number_field = run_number_field.strip()
		if run_number_field == '':
			return
		
		# list of runs
		list_run_number = filter(None, run_number_field.split(','))
		for run_number in list_run_number:
			try:
				full_file_name = FileFinder.findRuns("REF_L_%d" %int(run_number))[0]
				run_found.append(full_file_name)
				cls.run_number_found.append(run_number)
			except:
				run_not_found.append(run_number)
				
		if run_not_found != []:
			info('Could not locate run(s) %s !' %(','.join(run_not_found)))
		
		if run_found != []:
			cls.open_file(run_found)
			
		self.ui.numberSearchEntry.setText('')
		
	def open_file(cls, list_full_file_name):
		info('Reading runs %s ...' %(','.join(cls.run_number_found)))
		
		self = cls.self
		is_data = self.is_working_with_data()
		
		back_offset_from_peak = self.ui.autoBackSelectionWidth.value()
		is_with_auto_peak_finder = self.is_with_auto_peak_finder()
		is_with_auto_Tof_finder = self.ui.autoTofFlag.isChecked()
		
		data = NXSData(list_full_file_name, 
		               bins = self.ui.eventTofBins.value(),
		               callback = self.updateEventReadout,
		               angle_offset = self.ui.angleOffsetValue.text(),
		               is_data = is_data,
		               is_auto_peak_finder = is_with_auto_peak_finder,
		               back_offset_from_peak = back_offset_from_peak,
		               is_auto_tof_finder = is_with_auto_Tof_finder)

		if data is None:
			return
		
		if cls.replaced_data:
			[r,c] = self.getCurrentRowColumnSelected()
		else:
			[r,c] = cls.getRowColumnNextDataSet()
			if c is not 0:
				c = 1
			
		self.bigTableData[r,c] = data
		[true_r, true_c] = self.getTrueCurrentRowColumnSelected()
		if true_r == -1:
			r = 0
			true_c = 0
		self._prev_row_selected = r
		self._prev_col_selected = true_c
		
		self.enableWidgets(status=True)

	def getFirstEmptyLine(cls):
		self = cls.self
		bigTableData = self.bigTableData
		[nbr_row, nbr_col] = bigTableData.shape
		for r in range(nbr_row):
			field1 = bigTableData[r,0]
			field2 = bigTableData[r,1]
			field3 = bigTableData[r,2]
			if (field1 is None) and (field2 is None) and (field3 is None):
				return r
		return nbr_row

	def getRowColumnNextDataSet(cls):
		self = cls.self
		_selected_row = self.ui.reductionTable.selectedRanges()
		_is_data = self.is_working_with_data()
		if _selected_row == []:
			_new_row = 0
			if _is_data:
				_new_column = 0
			else:
				_new_column = 6
			return [_new_row, _new_column]
			
		if _is_data:
			_new_row = cls.getFirstEmptyLine()
			_new_column = 0
		else:
			_new_row = _selected_row[0].bottomRow()
			_new_column = 6
		return [_new_row, _new_column]
		