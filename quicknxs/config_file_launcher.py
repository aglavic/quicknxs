import os
from  logging import warning

class ConfigFileLauncher(object):
	
	self = None
	
	def __init__(cls, self, file_index):
		cls.self = self
		
		try:
			_configObject = self.reducedFilesLoadedObject
			_filename = _configObject.configFiles[file_index].fullFileName
			_configObject.configFiles[file_index].setNewTime()
			self.reducedFilesLoadedObject = _configObject
			self.loading_configuration_file(_filename)
			self.fileMenuObject.activate_file_at_index(file_index)
			self.current_loaded_file = _filename
			self.resetFileHasBeenModified()
		except:
			warning("Wrong File Format!")
			
			
	
