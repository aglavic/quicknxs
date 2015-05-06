import colors
from PyQt4 import QtGui

class CheckErrorWidgets(object):
	
	def __init__(cls, self):
		
		[row, col] = self.getCurrentRowColumnSelected()
		bError = False
		if col == 0: #data
			
			col_index = 0
			self.ui.data_peak1_error.setVisible(False)
			self.ui.data_peak2_error.setVisible(False)
			self.ui.data_back1_error.setVisible(False)
			self.ui.data_back2_error.setVisible(False)
			
			peak2 = self.ui.dataPeakToValue.value()
			peak1 = self.ui.dataPeakFromValue.value()
			back1 = self.ui.dataBackFromValue.value()
			back2 = self.ui.dataBackToValue.value()
						
			if back1 > peak1:
				bError = True
				self.ui.data_peak1_error.setVisible(True)
				self.ui.data_back1_error.setVisible(True)
			
			if back2 < peak2:
				bError = True
				self.ui.data_peak2_error.setVisible(True)
				self.ui.data_back2_error.setVisible(True)
		      
			self.ui.data_selection_error_label.setVisible(bError)
						
		else: #norm
		    
			col_index = 6
			self.ui.norm_peak1_error.setVisible(False)
			self.ui.norm_peak2_error.setVisible(False)
			self.ui.norm_back1_error.setVisible(False)
			self.ui.norm_back2_error.setVisible(False)
			
			peak2 = self.ui.normPeakToValue.value()
			peak1 = self.ui.normPeakFromValue.value()
			back1 = self.ui.normBackFromValue.value()
			back2 = self.ui.normBackToValue.value()
			
			if back1 > peak1:
				bError = True
				self.ui.norm_peak1_error.setVisible(True)
				self.ui.norm_back1_error.setVisible(True)
				
			if back2 < peak2:
				bError = True
				self.ui.norm_peak2_error.setVisible(True)
				self.ui.norm_back2_error.setVisible(True)
	      
			self.ui.norm_selection_error_label.setVisible(bError)  

		_brush_color = QtGui.QBrush()
		if bError:
			_brush_color.setColor(colors.VALUE_BAD)
		else:
			_brush_color = QtGui.QBrush()
		self.ui.reductionTable.item(row, col_index).setForeground(_brush_color)
