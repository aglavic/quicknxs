from file_loaded_object import FileLoadedObject
from PyQt4 import QtGui
from PyQt4 import QtCore

class ReducedSFCalculatorConfigFilesHandler(object):
	'''
	This class handles the config files previously loaded and will replace the oldest files (of 5)
	by the new freshly loaded one (if not already there)
	'''	
	mainGui = None
	
	config_files = []
	active_file_index = -1
	total_files_loaded = 0
	TOTAL_NUMBER_OF_FILES = 10
	
	def __init__(self, mainGui):
		self.mainGui = mainGui
		self.populateWithCurrentConfigContain()
		
	def populateWithCurrentConfigContain(self):
		from quicknxs.config import reflsfcalculatorlastloadedfiles
		reflsfcalculatorlastloadedfiles.switch_config('config_files')
		file1 = reflsfcalculatorlastloadedfiles.reduce1
		file2 = reflsfcalculatorlastloadedfiles.reduce2
		file3 = reflsfcalculatorlastloadedfiles.reduce3
		file4 = reflsfcalculatorlastloadedfiles.reduce4
		file5 = reflsfcalculatorlastloadedfiles.reduce5
		file6 = reflsfcalculatorlastloadedfiles.reduce6
		file7 = reflsfcalculatorlastloadedfiles.reduce7
		file8 = reflsfcalculatorlastloadedfiles.reduce8
		file9 = reflsfcalculatorlastloadedfiles.reduce9
		file10 = reflsfcalculatorlastloadedfiles.reduce10
		file = [file1, file2, file3, file4, file5, file6, file7, file8, file9, file10]
		date1 = reflsfcalculatorlastloadedfiles.date1
		date2 = reflsfcalculatorlastloadedfiles.date2
		date3 = reflsfcalculatorlastloadedfiles.date3
		date4 = reflsfcalculatorlastloadedfiles.date4
		date5 = reflsfcalculatorlastloadedfiles.date5
		date6 = reflsfcalculatorlastloadedfiles.date6
		date7 = reflsfcalculatorlastloadedfiles.date7
		date8 = reflsfcalculatorlastloadedfiles.date8
		date9 = reflsfcalculatorlastloadedfiles.date9
		date10 = reflsfcalculatorlastloadedfiles.date10
		date = [date1, date2, date3, date4, date5, date6, date7, date8, date9, date10]
		for i in range(self.TOTAL_NUMBER_OF_FILES):
			if file[i] != '':
				_fileLoad = FileLoadedObject(file[i], date[i])
				self.config_files.append(_fileLoad)
				self.total_files_loaded += 1
	
	def addFile(self, fullFileName):
		
		_newFileObject = FileLoadedObject(fullFileName)
		
		if len(self.config_files) == 0:
			self._add_file_to_array(_newFileObject)
			return
		
		[isAlreadyThere, index] = self._is_new_file(_newFileObject)
		if isAlreadyThere:
			self.switch_old_with_new_file(_newFileObject, index)
			self.mainGui.file_menu_object.activateFileAtIndex(index)
		else:
			self._add_file_to_array(_newFileObject)
			
	def _is_new_file(self, newFileObject):
		_nbrFile = len(self.config_files)
		for i in range(_nbrFile):
			if newFileObject.fullFileName == self.config_files[i].fullFileName:
				return [True, i]
		return [False, -1]
			
	def _add_file_to_array(self, _newFileObject):
		if len(self.config_files) == self.TOTAL_NUMBER_OF_FILES:
			self._add_at_the_top(_newFileObject)
			self.mainGui.file_menu_object.activateFileAtIndex(0)
		else:
			self.config_files.append(_newFileObject)
			self.total_files_loaded += 1
			self.mainGui.file_menu_object.activateFileAtIndex(self.total_files_loaded)
	
	def _add_at_the_top(self, newFileObject):	
		for i in range(self.TOTAL_NUMBER_OF_FILES-1,0,-1):
			self.config_files[i] = self.config_files[i-1]
		self.config_files[0] = newFileObject

	def switch_old_with_new_file(self, newFileObject, index):
		self.config_files[index] = newFileObject
		
	def _replace_with_oldest_file(self, newFileObject):
		_oldestIndex = self._get_index_of_oldest_file()
		self.config_files[_oldestIndex] = newFileObject

	def _get_index_of_oldest_file(self):
		_oldestTime = self.config_files[0].lastTimeUsed
		_index = 0
		for i in range(1,self.TOTAL_NUMBER_OF_FILES):
			_time = self.config_files[i]
			if _time < _oldestTime:
				_oldestTime = _time
				_index = i
		return _index
			
	def updateGui(self):
		listKey = [QtCore.Qt.Key_0, 
		           QtCore.Qt.Key_1,
		           QtCore.Qt.Key_2,
		           QtCore.Qt.Key_3,
		           QtCore.Qt.Key_4]
		for i in range(self.total_files_loaded):
			_file = self.config_files[i].fullFileName
			_key = listKey[i]
			if _file != '':
				self.mainGui.list_action[i].setText(_file)
				self.mainGui.list_action[i].setVisible(True)
				self.mainGui.list_action[i].setShortcuts(QtGui.QKeySequence(QtCore.Qt.META + _key))

	def save(self):
		from quicknxs.config import reflsfcalculatorlastloadedfiles
		reflsfcalculatorlastloadedfiles.switch_config('config_files')
		
		if  self.total_files_loaded>0 and self.config_files[0].fullFileName != '':
			reflsfcalculatorlastloadedfiles.reduce1 = self.config_files[0].fullFileName
			reflsfcalculatorlastloadedfiles.date1 = self.config_files[0].lastTimeUsed
		
		if self.total_files_loaded>1 and self.config_files[1].fullFileName != '':
			reflsfcalculatorlastloadedfiles.reduce2 = self.config_files[1].fullFileName
			reflsfcalculatorlastloadedfiles.date2 = self.config_files[1].lastTimeUsed

		if self.total_files_loaded>2 and self.config_files[2].fullFileName != '':
			reflsfcalculatorlastloadedfiles.reduce3 = self.config_files[2].fullFileName
			reflsfcalculatorlastloadedfiles.date3 = self.config_files[2].lastTimeUsed
			
		if self.total_files_loaded>3 and self.config_files[3].fullFileName != '':
			reflsfcalculatorlastloadedfiles.reduce4 = self.config_files[3].fullFileName
			reflsfcalculatorlastloadedfiles.date4 = self.config_files[3].lastTimeUsed

		if self.total_files_loaded>4 and self.config_files[4].fullFileName != '':
			reflsfcalculatorlastloadedfiles.reduce5 = self.config_files[4].fullFileName
			reflsfcalculatorlastloadedfiles.date5 = self.config_files[4].lastTimeUsed
			
		if self.total_files_loaded>5 and self.config_files[5].fullFileName != '':
			reflsfcalculatorlastloadedfiles.reduce5 = self.config_files[5].fullFileName
			reflsfcalculatorlastloadedfiles.date5 = self.config_files[5].lastTimeUsed

		if self.total_files_loaded>6 and self.config_files[6].fullFileName != '':
			reflsfcalculatorlastloadedfiles.reduce5 = self.config_files[6].fullFileName
			reflsfcalculatorlastloadedfiles.date5 = self.config_files[6].lastTimeUsed

		if self.total_files_loaded>7 and self.config_files[7].fullFileName != '':
			reflsfcalculatorlastloadedfiles.reduce5 = self.config_files[7].fullFileName
			reflsfcalculatorlastloadedfiles.date5 = self.config_files[7].lastTimeUsed

		if self.total_files_loaded>8 and self.config_files[8].fullFileName != '':
			reflsfcalculatorlastloadedfiles.reduce5 = self.config_files[8].fullFileName
			reflsfcalculatorlastloadedfiles.date5 = self.config_files[8].lastTimeUsed

		if self.total_files_loaded>9 and self.config_files[9].fullFileName != '':
			reflsfcalculatorlastloadedfiles.reduce5 = self.config_files[9].fullFileName
			reflsfcalculatorlastloadedfiles.date5 = self.config_files[9].lastTimeUsed

		reflsfcalculatorlastloadedfiles.switch_config('default')