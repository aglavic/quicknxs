from PyQt4 import QtGui

class InitFileMenu(object):
	
	mainGui = None
	currentlyActivatedFile = -1
	listFiles = []
	
	def __init__(self, mainGui):
		self.mainGui = mainGui
		
		self.init_list_of_files()
		self.init_separator()
		self.init_action()
		
		self.init_gui()
		
	def init_separator(self):
		if self.listFiles != ['','','','','']:
			self.mainGui.ui.menuFile.addSeparator()
		
	def init_action(self):
		_action1 = QtGui.QAction('', self.mainGui)
		_action1.triggered.connect(self.mainGui.launch_config_file1)
		_action1.setCheckable(True)
		_action1.setVisible(False)
		self.mainGui.ui.menuFile.addAction(_action1)
		_action2 = QtGui.QAction('', self.mainGui)
		_action2.setCheckable(True)
		_action2.triggered.connect(self.mainGui.launch_config_file2)
		_action2.setVisible(False)
		self.mainGui.ui.menuFile.addAction(_action2)
		_action3 = QtGui.QAction('', self.mainGui)
		_action3.triggered.connect(self.mainGui.launch_config_file3)
		_action3.setCheckable(True)
		_action3.setVisible(False)
		self.mainGui.ui.menuFile.addAction(_action3)
		_action4 = QtGui.QAction('', self.mainGui)
		_action4.triggered.connect(self.mainGui.launch_config_file4)
		_action4.setCheckable(True)
		_action4.setVisible(False)
		self.mainGui.ui.menuFile.addAction(_action4)
		_action5 = QtGui.QAction('', self.mainGui)
		_action5.triggered.connect(self.mainGui.launch_config_file5)
		_action5.setCheckable(True)
		_action5.setVisible(False)
		self.mainGui.ui.menuFile.addAction(_action5)
		self.mainGui.listAction = [_action1, _action2, _action3, _action4, _action5]
		
	def init_list_of_files(self):
		from quicknxs.config import refllastloadedfiles
		refllastloadedfiles.switch_config('config_files')
		file1 = refllastloadedfiles.reduce1
		file2 = refllastloadedfiles.reduce2
		file3 = refllastloadedfiles.reduce3
		file4 = refllastloadedfiles.reduce4
		file5 = refllastloadedfiles.reduce5
		_list_files = [file1, file2, file3, file4, file5]
		self.listFiles = _list_files

	def	init_gui(self):
		_list_files = self.listFiles
		for i in range(len(_list_files)):
			_file = _list_files[i]
			if _file != '':
				self.mainGui.listAction[i].setText(_file)
				self.mainGui.listAction[i].setVisible(True)
				self.mainGui.ui.menuFile.addAction(self.mainGui.listAction[i])
				
	def activate_file_at_index(self, index):			
		self.currentlyActivatedFile = index
		for i in range(len(self.listFiles)):
			self.mainGui.listAction[i].setChecked(False)
		self.mainGui.listAction[index].setChecked(True)