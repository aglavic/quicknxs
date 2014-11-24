from file_loaded_object import FileLoadedObject
from PyQt4 import QtGui

class PrevFilesLoadedHandler(object):
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
	
	def addFile(self, fullFileName):
		
		_newFileObject = FileLoadedObject(fullFileName)
		
		if self.totalFilesLoaded < self.TOTAL_NUMBER_OF_FILES:
			self._add_file_to_array(_newFileObject)
			return
		
		if self._is_new_file(_newFileObject):
			self._replace_with_oldest_file(_newFileObject)
			
	def _is_new_file(self, newFileObject):
		_nbrFile = len(self.configFiles)
		for i in range(_nbrFile):
			if newFileObject.fullFileName == configFiles[i]:
				return True
		return False
			
	def _add_file_to_array(self, _newFileObject):
		self.configFiles.append(_newFileObject)
		self.totalFilesLoaded += 1
			
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
		_menuFile = self.mainGui.ui.menuFile.addSeparator()
		for i in range(self.totalFilesLoaded):
			_action = QtGui.QAction(self.configFiles[i].fullFileName, self.mainGui)
			self.mainGui.ui.menuFile.addAction(_action)
	
		