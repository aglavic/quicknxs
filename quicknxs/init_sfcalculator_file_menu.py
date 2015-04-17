from PyQt4 import QtGui, QtCore

class InitSFCalculatorFileMenu(object):
	
	sf_gui = None
	currentlyActivatedFile = -1
	listFiles = []
	
	def __init__(self, parent=None):
		self.sf_gui = parent
		
		self.initListOfFiles()
		self.initSeparator()
		self.initAction()
		
		self.initGui()
		
	def initSeparator(self):
		if self.listFiles != ['','','','','']:
			self.sf_gui.ui.menuFile.addSeparator()
		
	def action(self, connect_function):
		_action = QtGui.QAction('', self.sf_gui)
		_action.triggered.connect(connect_function)
		_action.setCheckable(True)
		_action.setShortcut(QtGui.QKeySequence(QtCore.Qt.META + QtCore.Qt.Key_0))
		_action.setVisible(False)
		return _action
		
	def initAction(self):
		list_config_file = [self.sf_gui.launchConfigFile1,
		                    self.sf_gui.launchConfigFile2,
		                    self.sf_gui.launchConfigFile3,
		                    self.sf_gui.launchConfigFile4,
		                    self.sf_gui.launchConfigFile5,
		                    self.sf_gui.launchConfigFile6,
		                    self.sf_gui.launchConfigFile7,
		                    self.sf_gui.launchConfigFile8,
		                    self.sf_gui.launchConfigFile9,
		                    self.sf_gui.launchConfigFile10]
		for _config_file in list_config_file:
			_action = self.action(_config_file)
			self.sf_gui.ui.menuFile.addAction(_action)
			self.sf_gui.file_menu_action_list.append(_action)

	def initListOfFiles(self):
		from quicknxs.config import refllastloadedfiles
		refllastloadedfiles.switch_config('config_files')
		file1 = refllastloadedfiles.reduce1
		file2 = refllastloadedfiles.reduce2
		file3 = refllastloadedfiles.reduce3
		file4 = refllastloadedfiles.reduce4
		file5 = refllastloadedfiles.reduce5
		_list_files = [file1, file2, file3, file4, file5]
		self.listFiles = _list_files

	def	initGui(self):
		_list_files = self.listFiles
		for i in range(len(_list_files)):
			_file = _list_files[i]
			if _file != '':
				self.sf_gui.file_menu_action_list[i].setText(_file)
				self.sf_gui.file_menu_action_list[i].setVisible(True)
				self.sf_gui.ui.menuFile.addAction(self.sf_gui.file_menu_action_list[i])
				
	def activateFileAtIndex(self, index):			
		self.currentlyActivatedFile = index
		for i in range(len(self.listFiles)):
			self.sf_gui.file_menu_action_list[i].setChecked(False)
		self.sf_gui.file_menu_action_list[index].setChecked(True)