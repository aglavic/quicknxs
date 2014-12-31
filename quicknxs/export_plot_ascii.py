from PyQt4 import QtGui
from logging import info, warning, debug
import os
import utilities
from outputReducedDataDialog import OutputReducedDataDialog

class ExportPlotAscii(object):
	
	self = None
	
	def __init__(cls, self, type='yt'):
		cls.self = self
		
		if type == 'yt':
			cls.export_yt()
		elif type == 'ix':
			cls.export_ix()
		elif type == 'it':
			cls.export_it()
		elif type == 'yi':
			cls.export_yi()
		elif type == 'stitched':
			cls.export_stitched()
		
	def export_yt(cls):
		self = cls.self
		bigTableData = self.bigTableData
		[row,col] = self.getCurrentRowColumnSelected()
		_data = bigTableData[row,col]
		_active_data = _data.active_data
		run_number = _active_data.run_number
		default_filename = 'REFL_' + run_number + '_2dPxVsTof.txt'
		path = self.path_ascii
		default_filename = path + '/' + default_filename
		filename = QtGui.QFileDialog.getSaveFileName(self, 'Create 2D Pixel VS TOF', default_filename)
		
		if str(filename).strip() == '':
			info('User Canceled Outpout ASCII')
			return
		  
		self.path_ascii = os.path.dirname(filename)
		image = _active_data.ytofdata
		utilities.output_2d_ascii_file(filename, image)

	def export_ix(cls):
		self = cls.self
		bigTableData = self.bigTableData
		[row,col] = self.getCurrentRowColumnSelected()
		_data = bigTableData[row,col]
		_active_data = _data.active_data
		run_number = _active_data.run_number
		default_filename = 'REFL_' + run_number + '_ix.txt'
		path = self.path_ascii
		default_filename = path + '/' + default_filename
		filename = QtGui.QFileDialog.getSaveFileName(self, 'Create Counts vs Pixel (low resolution range) ASCII File', default_filename)
		
		if str(filename).strip() == '':
			info('User Canceled Output ASCII')
			return
		
		self.path_ascii = os.path.dirname(filename)
		countsxdata = _active_data.countsxdata
		pixelaxis = range(len(countsxdata))
		
		text = ['#Counts vs Pixels (low resolution range)','#Pixel - Counts']
		sz = len(pixelaxis)
		for i in range(sz):
			_line = str(pixelaxis[i]) + ' ' + str(countsxdata[i])
			text.append(_line)
		utilities.write_ascii_file(filename, text)
	
	def export_it(cls):
		self = cls.self
		bigTableData = self.bigTableData
		[row,col] = self.getCurrentRowColumnSelected()
		_data = bigTableData[row,col]
		_active_data = _data.active_data
		run_number = _active_data.run_number
		default_filename = 'REFL_' + run_number + '_yt.txt'
		path = self.path_ascii
		default_filename = path + '/' + default_filename
		filename = QtGui.QFileDialog.getSaveFileName(self, 'Create Counts vs TOF ASCII File', default_filename)
		
		if str(filename).strip() == '':
			info('User Canceled Output ASCII')
			return
		
		self.path_ascii = os.path.dirname(filename)
		countstofdata = _active_data.countstofdata
		tof = _active_data.tof_axis_auto_with_margin
		if tof[-1] > 1000:
			tof /= 1000.
			
		text = ['#Counts vs  TOF','#TOF(ms) - Counts']
		sz = len(tof)-1
		for i in range(sz):
			_line = str(tof[i]) + ' ' + str(countstofdata[i])
			text.append(_line)
		text.append(str(tof[-1]))
		utilities.write_ascii_file(filename, text)
		
	def export_yi(cls):
		self = cls.self
		bigTableData = self.bigTableData
		[row,col] = self.getCurrentRowColumnSelected()
		_data = bigTableData[row,col]
		_active_data = _data.active_data
		run_number = _active_data.run_number
		default_filename = 'REFL_' + run_number + '_rpx.txt'
		path = self.path_ascii
		default_filename = path + '/' + default_filename
		filename = QtGui.QFileDialog.getSaveFileName(self, 'Create Counts vs Pixel ASCII File', default_filename)
		
		if str(filename).strip() == '':
			info('User Canceled Output ASCII')
			return
		
		self.path_ascii = os.path.dirname(filename)
	      
		ycountsdata = _active_data.ycountsdata
		pixelaxis = range(len(ycountsdata))
		
		text = ['#Counts vs Pixels','#Pixel - Counts']
		sz = len(pixelaxis)
		for i in range(sz):
			_line = str(pixelaxis[i]) + ' ' + str(ycountsdata[i])
			text.append(_line)
		utilities.write_ascii_file(filename, text)
		
	def export_stitched(cls):
		self = cls.self
		_tmp = OutputReducedDataDialog(self, self.stitchingAsciiWidgetObject)
		_tmp.show()
		