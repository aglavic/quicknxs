from PyQt4.QtGui import QDialog, QFileDialog, QPalette
from PyQt4.QtCore import Qt
from output_reduced_data_dialog import Ui_Dialog as UiDialog
from stitching_ascii_widget import stitchingAsciiWidgetObject
from export_stitching_ascii_settings import ExportStitchingAsciiSettings
from mantid.simpleapi import *
import os
import utilities


class OutputReducedData(QDialog):
	
	_open_instances = []
	stitchingAsciiWidgetObject = None
	mainGui = None
	filename = ''
	
	q_axis = None
	y_axis = None
	e_axis = None
	
	R_THRESHOLD = 1e-15
	
	metadata = None
	text_data = None
	isWith4thColumnFlag = False
	dq0 = None
	dq_over_q = None
	useLowestErrorValueFlag = True
	
	def __init__(self, mainGui, stitchingAsciiWidgetObject, parent=None):
		QDialog.__init__(self, parent=parent)
		self.setWindowModality(False)
		self._open_instances.append(self)
		self.ui = UiDialog()
		self.ui.setupUi(self)
		
		self.ui.folder_error.setVisible(False)
		palette = QPalette()
		palette.setColor(QPalette.Foreground, Qt.red)
		self.ui.folder_error.setPalette(palette)
		
		self.stitchingAsciiWidgetObject = stitchingAsciiWidgetObject
		self.mainGui = mainGui
		
		# retrieve gui parameters 
		_exportStitchingAsciiSettings = self.mainGui.exportStitchingAsciiSettings
		self.dq0 = str(_exportStitchingAsciiSettings.fourth_column_dq0)
		self.dq_over_q = str(_exportStitchingAsciiSettings.fourth_column_dq_over_q)
		self.isWith4thColumnFlag = bool(_exportStitchingAsciiSettings.fourth_column_flag)
		self.useLowestErrorValueFlag = bool(_exportStitchingAsciiSettings.use_lowest_error_value_flag)
		self.ui.dq0Value.setText(self.dq0)
		self.ui.dQoverQvalue.setText(self.dq_over_q)
		self.ui.output4thColumnFlag.setChecked(self.isWith4thColumnFlag)
		self.ui.usingLessErrorValueFlag.setChecked(self.useLowestErrorValueFlag)
		self.ui.usingMeanValueFalg.setChecked(not self.useLowestErrorValueFlag)
		
	def create_reduce_ascii_button_event(self):
		self.ui.folder_error.setVisible(False)
		if self.stitchingAsciiWidgetObject is None:
			return
		
		run_number = self.mainGui.ui.reductionTable.item(0,0).text()
		default_filename = 'REFL_' + run_number + '_reduced_stitched_data.txt'
		path = self.mainGui.path_ascii
		default_filename = path + '/' + default_filename
		
		filename = QFileDialog.getSaveFileName(self, 'Select Location and Name', default_filename)
		if str(filename).strip() == '':
			return
		
		folder = os.path.dirname(filename)
		if not self.is_folder_access_granted(folder):
			self.ui.folder_error.setVisible(True)
			return
		
		self.filename = filename
		self.mainGui.path_ascii = os.path.dirname(filename)
		self.write_ascii()
		self.close()
		self.save_back_widget_parameters_used()
		
	def save_back_widget_parameters_used(self):
		_isWith4thColumnFlag = self.ui.output4thColumnFlag.isChecked()
		_dq0 = self.ui.dq0Value.text()
		_dq_over_q = self.ui.dQoverQvalue.text()
		_useLowestErrorValueFlag = self.ui.usingLessErrorValueFlag.isChecked()
		
		_exportStitchingAsciiSettings = ExportStitchingAsciiSettings()
		_exportStitchingAsciiSettings.fourth_column_dq0 = _dq0
		_exportStitchingAsciiSettings.fourth_column_dq_over_q = _dq_over_q
		_exportStitchingAsciiSettings.fourth_column_flag = _isWith4thColumnFlag
		_exportStitchingAsciiSettings.use_lowest_error_value_flag = _useLowestErrorValueFlag
		self.mainGui.exportStitchingAsciiSettings = _exportStitchingAsciiSettings
		
	def is_folder_access_granted(self, filename):
		return os.access(filename,os.W_OK)
	
	def write_ascii(self):
		self.isWith4thColumnFlag = self.ui.output4thColumnFlag.isChecked()
		dq_over_q = self.ui.dQoverQvalue.text()
		self.dq_over_q = float(dq_over_q)
		if self.isWith4thColumnFlag:
			dq0 = self.ui.dq0Value.text()
			self.dq0 = float(dq0)
			line1 = '#dQ0[1/Angstroms]= ' + dq0
			line2 = '#dQ/Q= ' + dq_over_q
			line3 = '#Q[1/Angstroms] R delta_R Precision'
			text = [line1, line2, line3]
		else:
			text = ['#Q[1/Angstroms] R delta_R']
			
		self.useLowestErrorValueFlag = self.ui.usingLessErrorValueFlag.isChecked()
		
		self.text_data = text
		self.produce_data_with_common_q_axis()
		self.format_data()
		self.create_file()
		
	def create_file(self):
		utilities.write_ascii_file(self.filename, self.text_data)
		
	def produce_data_with_common_q_axis(self):
		nbrRow = self.mainGui.ui.reductionTable.rowCount()
		_dataObject = self.stitchingAsciiWidgetObject.loadedAsciiArray[0]
		_bigTableData = _dataObject.bigTableData
		
		minQ = 100
		maxQ = 0
		
		for i in range(nbrRow):
			tmp_wks_name = 'wks_' + str(i)
			_data = _bigTableData[i,0]
			
			_q_axis = _data.reduce_q_axis
			_y_axis = _data.reduce_y_axis[:-1]
			_e_axis = _data.reduce_e_axis[:-1]
			
			[_y_axis, _e_axis] = self.applySF(_data, _y_axis, _e_axis)
			
			minQ = min([_q_axis[0], minQ])
			maxQ = max([_q_axis[-1], maxQ])
			
			tmp_wks_name = CreateWorkspace(DataX = _q_axis,
					               DataY = _y_axis,
					               DataE = _e_axis,
					               Nspec = 1,
					               UnitX = "Wavelength",
					               OutputWorkspace = tmp_wks_name)
			tmp_wks_name.setDistribution(True)
			    
			# rebin everyting using the same Q binning parameters  
		binQ = self.dq_over_q
		bin_parameters = str(minQ) + ',-' + str(binQ) + ',' + str(maxQ)
		for i in range(nbrRow):  
				
			tmp_wks_name = 'wks_' + str(i)
			ConvertToHistogram(InputWorkspace = tmp_wks_name,
			                   OutputWorkspace = tmp_wks_name)
			
			Rebin(InputWorkspace = tmp_wks_name, 
			      Params = bin_parameters,
			      OutputWorkspace = tmp_wks_name)
			
		# we use the first histo as output reference
		data_y = mtd['wks_0'].dataY(0).copy()
		data_e = mtd['wks_0'].dataE(0).copy()
			
		skip_index = 0
		point_to_skip = 2
			
		for k in range(1,nbrRow):

			skip_point = True
			can_skip_last_point = False
			
			data_y_k = mtd['wks_' + str(k)].dataY(0)
			data_e_k = mtd['wks_' + str(k)].dataE(0)
			for j in range(len(data_y_k)-1):
					
				if data_y_k[j] > 0:
						
					can_skip_last_point = True
					if skip_point:
						skip_index += 1
						if skip_index == point_to_skip:
							skip_point = False
							skip_index = 0
						else:
							continue
						
				if can_skip_last_point and (data_y_k[j+1] == 0):
					break
					
				if data_y[j] > 0 and data_y_k[j] > 0:
					  
					if self.useLowestErrorValueFlag:
						if (data_e[j] > data_e_k[j]):
							data_y[j] = data_y_k[j]
							data_e[j] = data_e_k[j]
							
					else:
						[data_y[j], data_e[j]] = utilities.weighted_mean([data_y[j], data_y_k[j]],
						                                                 [data_e[j], data_e_k[j]])
							
				elif (data_y[j] == 0) and (data_y_k[j]>0):
					data_y[j] = data_y_k[j]
					data_e[j] = data_e_k[j]
						
		data_x = mtd['wks_1'].dataX(0)
						
		self.q_axis = data_x
		self.y_axis = data_y
		self.e_axis = data_e
		
	def applySF(self, _data, y_array, e_array):
		if self.mainGui.ui.autoSF.isChecked():
		  _sf = _data.sf_auto
		elif self.mainGui.ui.manualSF.isChecked():
		  _sf = _data.sf_manual
		else:
		  _sf = 1
		
		y_array /= _sf
		e_array /= _sf
		
		return [y_array, e_array]

	def format_data(self):
		_q_axis = self.q_axis
		_y_axis = self.y_axis
		_e_axis = self.e_axis
		text = self.text_data
		
		if self.isWith4thColumnFlag:
			dq0 = self.dq0
			dq_over_q = self.dq_over_q
		
		sz = len(_q_axis) - 1
		for i in range(sz):
			if _y_axis[i] > self.R_THRESHOLD:
				_line = str(_q_axis[i])
				_line += ' ' + str(_y_axis[i])
				_line += ' ' + str(_e_axis[i])
				if self.isWith4thColumnFlag:
					_precision = str(dq0 + dq_over_q * _q_axis[i])
					_line += ' ' + _precision
				text.append(_line)
		
		self.text_data = text