from PyQt4 import QtGui
from logging import info
import os
from xml.dom import minidom
from numpy import empty
from qreduce import LConfigDataset

class LoadingConfiguration(object):
	
	self = None
	load_config_worked = True
	filename = ''
	
	def __init__(cls, self, filename=''):
		cls.self = self
	
		if filename == '':
			_path = self.path_config
			filename = QtGui.QFileDialog.getOpenFileName(self,'Open Configuration File', _path)      
		
		if not (filename == ""):
			cls.loadingConfigurationFile(filename)
			cls.filename = filename
			
	def statusOk(cls):
		return cls.load_config_worked
	
	def loadingConfigurationFile(cls, filename):
		self = cls.self
		self.path_config = os.path.dirname(filename)
		
		cls.clearReductionTable()
		cls.loadConfigInBigTableData(filename)
		
	def loadConfigInBigTableData(cls, filename):
		try:
			dom = minidom.parse(filename)
		except:
			info('No configuration file loaded')
			cls.load_config_worked = False
			return
		
		cls.populateBigTableData(dom)
		
	def populateBigTableData(cls, dom):
		RefLData = dom.getElementsByTagName('RefLData')
		nbrRowBigTable = len(RefLData)
		
		bigTableData = empty((20,3), dtype=object)
		#parsing XML
		_row = 0
		for node in RefLData:
			_metadataObject = cls.getMetadataObject(node)
			bigTableData[_row, 2] = _metadataObject
			_row += 1
		
		cls.self.bigTableData = bigTableData
			
	def getMetadataObject(self, node):
		iMetadata = LConfigDataset()
		
		_peak_min = self.getNodeValue(node, 'from_peak_pixels')
		_peak_max = self.getNodeValue(node, 'to_peak_pixels')
		iMetadata.data_peak = [_peak_min, _peak_max]
		
		_back_min = self.getNodeValue(node, 'back_roi1_from')
		_back_max = self.getNodeValue(node, 'back_roi1_to')
		iMetadata.data_back = [_back_min, _back_max]
		
		_low_res_min = self.getNodeValue(node, 'x_min_pixel')
		_low_res_max = self.getNodeValue(node, 'x_max_pixel')
		iMetadata.data_low_res = [_low_res_min, _low_res_max]
		
		_back_flag = self.getNodeValue(node, 'background_flag')
		iMetadata.data_back_flag = _back_flag
		
		_low_res_flag = self.getNodeValue(node, 'x_range_flag')
		iMetadata.data_low_res_flag = _low_res_flag
		
		_tof_min = self.getNodeValue(node, 'from_tof_range')
		_tof_max = self.getNodeValue(node, 'to_tof_range')
		if float(_tof_min) < 500:  # ms
			_tof_min = str(float(_tof_min) * 1000)
			_tof_max = str(float(_tof_max) * 1000)
		iMetadata.tof_range = [_tof_min, _tof_max]
		
		_q_min = self.getNodeValue(node, 'from_q_range')
		_q_max = self.getNodeValue(node, 'to_q_range')
		iMetadata.q_range = [_q_min, _q_max]
		
		_lambda_min = self.getNodeValue(node, 'from_lambda_range')
		_lambda_max = self.getNodeValue(node, 'to_lambda_range')
		iMetadata.lambda_range = [_lambda_min, _lambda_max]
		
		iMetadata.tof_units = 'micros'
		
		_data_sets = self.getNodeValue(node, 'data_sets')
		iMetadata.data_sets = _data_sets
		
		_tof_auto = self.getNodeValue(node, 'tof_range_flag')
		iMetadata.tof_auto_flag = _tof_auto
		
		_norm_flag = self.getNodeValue(node, 'norm_flag')
		iMetadata.norm_flag = _norm_flag
		
		_peak_min = self.getNodeValue(node, 'norm_from_peak_pixels')
		_peak_max = self.getNodeValue(node, 'norm_to_peak_pixels')
		iMetadata.norm_peak = [_peak_min, _peak_max]
		
		_back_min = self.getNodeValue(node, 'norm_from_back_pixels')
		_back_max = self.getNodeValue(node, 'norm_to_back_pixels')
		iMetadata.norm_back = [_back_min, _back_max]
		
		_norm_sets = self.getNodeValue(node, 'norm_dataset')
		iMetadata.norm_sets = _norm_sets
	    
		_low_res_min = self.getNodeValue(node, 'norm_x_min')
		_low_res_max = self.getNodeValue(node, 'norm_x_max')
		iMetadata.norm_low_res = [_low_res_min, _low_res_max]
	    
		_back_flag = self.getNodeValue(node, 'norm_background_flag')
		iMetadata.norm_back_flag = _back_flag
		
		_low_res_flag = self.getNodeValue(node, 'norm_x_range_flag')
		iMetadata.norm_low_res_flag = _low_res_flag
		
		try:
			_data_full_file_name = self.getNodeValue(node, 'data_full_file_name')
			_data_full_file_name = _data_full_file_name.split(',')
		except:
			_data_full_file_name = ''
		iMetadata.data_full_file_name = _data_full_file_name
			
		try:
			_norm_full_file_name = self.getNodeValue(node, 'norm_full_file_name')
			_norm_full_file_name = _norm_full_file_name.split(',')
		except:
			_norm_full_file_name = ''
		iMetadata.norm_full_file_name = _norm_full_file_name
	    
		return iMetadata
	
	def getNodeValue(self,node,flag):
		try:
			_tmp = node.getElementsByTagName(flag)
			_value = _tmp[0].childNodes[0].nodeValue
		except:
			_value = ''
		return _value
	
	def clearReductionTable(cls):
		nbrRow = cls.self.ui.reductionTable.rowCount()
		if nbrRow > 0:
			for _row in range(nbrRow):
				cls.self.ui.reductionTable.removeRow(0)