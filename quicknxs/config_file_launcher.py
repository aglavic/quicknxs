class ConfigFileLauncher(object):
	
	def __init__(cls, self, file_index):
		
		_configObject = self.reducedFilesLoadedObject
		_filename = _configObject.configFiles[file_index].fullFileName
		_configObject.configFiles[file_index].setNewTime()
		self.reducedFilesLoadedObject = _configObject
		self.loading_configuration_file(_filename)
		self.fileMenuObject.activate_file_at_index(file_index)
		