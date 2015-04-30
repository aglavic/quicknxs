import os
from PyQt4 import QtGui

class SFCalculatorConfigFileLauncher(object):
	
	self = None
	
	def __init__(cls, self, file_index):
		cls.self = self
		
		try:
			_config_object = self.reduced_files_loaded_object
			_filename = _config_object.config_files[file_index].fullFileName
			_config_object.config_files[file_index].setNewTime()
			self.reduced_files_loaded_object = _config_object
			self.loadingConfigurationFileDefined(_filename)
			self.file_menu_object.activateFileAtIndex(file_index)
		except:
			mesg = QtGui.QMessageBox.information(self, "Error Loading the Config File!"
				                         "Was unable to load: %s" %_filename)
			
	
