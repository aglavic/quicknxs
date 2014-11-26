from file_loaded_object import FileLoadedObject
from PyQt4 import QtGui

class ReducedConfigFilesHandler(object):
	'''
	This class handles the config files previously loaded and will replace the oldest files (of 5)
	by the new freshly loaded one (if not already there)
	'''	
	mainGui = None
	
	configFiles = []
	activeFileIndex = -1
	totalFilesLoaded = 0
	TOTAL_NUMBER_OF_FILES = 5
	
	def __init__(self, mainGui):
		self.mainGui = mainGui
		self.populateWithCurrentConfigContain()
		
	def populateWithCurrentConfigContain(self):
		from quicknxs.config import refllastloadedfiles
		refllastloadedfiles.switch_config('config_files')
		file1 = refllastloadedfiles.reduce1
		file2 = refllastloadedfiles.reduce2
		file3 = refllastloadedfiles.reduce3
		file4 = refllastloadedfiles.reduce4
		file5 = refllastloadedfiles.reduce5
		file = [file1, file2, file3, file4, file5]
		date1 = refllastloadedfiles.date1
		date2 = refllastloadedfiles.date2
		date3 = refllastloadedfiles.date3
		date4 = refllastloadedfiles.date4
		date5 = refllastloadedfiles.date5
		date = [date1, date2, date3, date4, date5]
		for i in range(self.TOTAL_NUMBER_OF_FILES):
			if file[i] != '':
				_fileLoad = FileLoadedObject(file[i], date[i])
				self.configFiles.append(_fileLoad)
				self.totalFilesLoaded += 1
	
	def addFile(self, fullFileName):
		
		_newFileObject = FileLoadedObject(fullFileName)
		
		if len(self.configFiles) == 0:
			self._add_file_to_array(_newFileObject)
			return
		
		[isAlreadyThere, index] = self._is_new_file(_newFileObject)
		if isAlreadyThere:
			self.switch_old_with_new_file(_newFileObject, index)
			self.mainGui.fileMenuObject.activate_file_at_index(index)
		else:
			self._add_file_to_array(_newFileObject)
			
	def _is_new_file(self, newFileObject):
		_nbrFile = len(self.configFiles)
		for i in range(_nbrFile):
			if newFileObject.fullFileName == self.configFiles[i].fullFileName:
				return [True, i]
		return [False, -1]
			
	def _add_file_to_array(self, _newFileObject):
		if len(self.configFiles) == self.TOTAL_NUMBER_OF_FILES:
			self._add_at_the_top(_newFileObject)
			self.mainGui.fileMenuObject.activate_file_at_index(0)
		else:
			self.configFiles.append(_newFileObject)
			self.totalFilesLoaded += 1
			self.mainGui.fileMenuObject.activate_file_at_index(self.totalFilesLoaded)
	
	def _add_at_the_top(self, newFileObject):	
		for i in range(self.TOTAL_NUMBER_OF_FILES-1,0,-1):
			self.configFiles[i] = self.configFiles[i-1]
		self.configFiles[0] = newFileObject

	def switch_old_with_new_file(self, newFileObject, index):
		self.configFiles[index] = newFileObject
		
	def _replace_with_oldest_file(self, newFileObject):
		_oldestIndex = self._get_index_of_oldest_file()
		self.configFiles[_oldestIndex] = newFileObject

	def _get_index_of_oldest_file(self):
		_oldestTime = self.configFiles[0].lastTimeUsed
		_index = 0
		for i in range(1,self.TOTAL_NUMBER_OF_FILES):
			_time = self.configFiles[i]
			if _time < _oldestTime:
				_oldestTime = _time
				_index = i
		return _index
			
	def updateGui(self):
		for i in range(self.totalFilesLoaded):
			_file = self.configFiles[i].fullFileName
			if _file != '':
				self.mainGui.listAction[i].setText(_file)
				self.mainGui.listAction[i].setVisible(True)

	def save(self):
		from quicknxs.config import refllastloadedfiles
		refllastloadedfiles.switch_config('config_files')
		
		if  self.totalFilesLoaded>0 and self.configFiles[0].fullFileName != '':
			refllastloadedfiles.reduce1 = self.configFiles[0].fullFileName
			refllastloadedfiles.date1 = self.configFiles[0].lastTimeUsed
		
		if self.totalFilesLoaded>1 and self.configFiles[1].fullFileName != '':
			refllastloadedfiles.reduce2 = self.configFiles[1].fullFileName
			refllastloadedfiles.date2 = self.configFiles[1].lastTimeUsed

		if self.totalFilesLoaded>2 and self.configFiles[2].fullFileName != '':
			refllastloadedfiles.reduce3 = self.configFiles[2].fullFileName
			refllastloadedfiles.date3 = self.configFiles[2].lastTimeUsed
			
		if self.totalFilesLoaded>3 and self.configFiles[3].fullFileName != '':
			refllastloadedfiles.reduce4 = self.configFiles[3].fullFileName
			refllastloadedfiles.date4 = self.configFiles[3].lastTimeUsed

		if self.totalFilesLoaded>4 and self.configFiles[4].fullFileName != '':
			refllastloadedfiles.reduce5 = self.configFiles[4].fullFileName
			refllastloadedfiles.date5 = self.configFiles[4].lastTimeUsed
			
		refllastloadedfiles.switch_config('default')