from PyQt4 import QtGui, QtCore

class InitSFCalculatorFileMenu(object):
	
	sf_gui = None
	currently_activated_file = -1
	list_files = []
	
	def __init__(self, parent=None):
		self.sf_gui = parent
		
		self.initListOfFiles()
		self.initSeparator()
		self.initAction()
		
		self.initGui()
		
	def initSeparator(self):
		if self.list_files != ['','','','','']:
			self.sf_gui.ui.menuFile.addSeparator()
		
	def action(self, connect_function):
		_action = QtGui.QAction('', self.sf_gui)
		_action.triggered.connect(connect_function)
		_action.setCheckable(True)
		_action.setShortcut(QtGui.QKeySequence(QtCore.Qt.META + QtCore.Qt.Key_0))
		_action.setVisible(False)
		return _action
		
	def initAction(self):
		#list_config_file = [self.sf_gui.launchConfigFile1,
		                    #self.sf_gui.launchConfigFile2,
		                    #self.sf_gui.launchConfigFile3,
		                    #self.sf_gui.launchConfigFile4,
		                    #self.sf_gui.launchConfigFile5,
		                    #self.sf_gui.launchConfigFile6,
		                    #self.sf_gui.launchConfigFile7,
		                    #self.sf_gui.launchConfigFile8,
		                    #self.sf_gui.launchConfigFile9,
		                    #self.sf_gui.launchConfigFile10]
		#for _config_file in list_config_file:
			#_action = self.action(_config_file)
			#self.sf_gui.ui.menuFile.addAction(_action)
			#self.sf_gui.file_menu_action_list.append(_action)
		_action1 = QtGui.QAction('', self.sf_gui)
		_action1.triggered.connect(self.sf_gui.launchConfigFile1)
		_action1.setCheckable(True)
		_action1.setShortcut(QtGui.QKeySequence(QtCore.Qt.META + QtCore.Qt.Key_0))
		_action1.setVisible(False)
		self.sf_gui.ui.menuFile.addAction(_action1)
		_action2 = QtGui.QAction('', self.sf_gui)
		_action2.setCheckable(True)
		_action2.setShortcut(QtGui.QKeySequence(QtCore.Qt.META + QtCore.Qt.Key_1))
		_action2.triggered.connect(self.sf_gui.launchConfigFile2)
		_action2.setVisible(False)
		self.sf_gui.ui.menuFile.addAction(_action2)
		_action3 = QtGui.QAction('', self.sf_gui)
		_action3.triggered.connect(self.sf_gui.launchConfigFile3)
		_action3.setShortcut(QtGui.QKeySequence(QtCore.Qt.META + QtCore.Qt.Key_2))
		_action3.setCheckable(True)
		_action3.setVisible(False)
		self.sf_gui.ui.menuFile.addAction(_action3)
		_action4 = QtGui.QAction('', self.sf_gui)
		_action4.triggered.connect(self.sf_gui.launchConfigFile4)
		_action4.setShortcut(QtGui.QKeySequence(QtCore.Qt.META + QtCore.Qt.Key_3))
		_action4.setCheckable(True)
		_action4.setVisible(False)
		self.sf_gui.ui.menuFile.addAction(_action4)
		_action5 = QtGui.QAction('', self.sf_gui)
		_action5.triggered.connect(self.sf_gui.launchConfigFile5)
		_action5.setShortcut(QtGui.QKeySequence(QtCore.Qt.META + QtCore.Qt.Key_4))
		_action5.setCheckable(True)
		_action5.setVisible(False)
		self.sf_gui.ui.menuFile.addAction(_action5)
		_action5 = QtGui.QAction('', self.sf_gui)
		_action5.triggered.connect(self.sf_gui.launchConfigFile5)
		_action5.setShortcut(QtGui.QKeySequence(QtCore.Qt.META + QtCore.Qt.Key_4))
		_action5.setCheckable(True)
		_action5.setVisible(False)
		self.sf_gui.ui.menuFile.addAction(_action5)
		_action6 = QtGui.QAction('', self.sf_gui)
		_action6.triggered.connect(self.sf_gui.launchConfigFile6)
		_action6.setShortcut(QtGui.QKeySequence(QtCore.Qt.META + QtCore.Qt.Key_4))
		_action6.setCheckable(True)
		_action6.setVisible(False)
		self.sf_gui.ui.menuFile.addAction(_action6)
		_action7 = QtGui.QAction('', self.sf_gui)
		_action7.triggered.connect(self.sf_gui.launchConfigFile7)
		_action7.setShortcut(QtGui.QKeySequence(QtCore.Qt.META + QtCore.Qt.Key_4))
		_action7.setCheckable(True)
		_action7.setVisible(False)
		self.sf_gui.ui.menuFile.addAction(_action7)
		_action8 = QtGui.QAction('', self.sf_gui)
		_action8.triggered.connect(self.sf_gui.launchConfigFile8)
		_action8.setShortcut(QtGui.QKeySequence(QtCore.Qt.META + QtCore.Qt.Key_4))
		_action8.setCheckable(True)
		_action8.setVisible(False)
		self.sf_gui.ui.menuFile.addAction(_action8)
		_action9 = QtGui.QAction('', self.sf_gui)
		_action9.triggered.connect(self.sf_gui.launchConfigFile9)
		_action9.setShortcut(QtGui.QKeySequence(QtCore.Qt.META + QtCore.Qt.Key_4))
		_action9.setCheckable(True)
		_action9.setVisible(False)
		self.sf_gui.ui.menuFile.addAction(_action9)
		_action10 = QtGui.QAction('', self.sf_gui)
		_action10.triggered.connect(self.sf_gui.launchConfigFile10)
		_action10.setShortcut(QtGui.QKeySequence(QtCore.Qt.META + QtCore.Qt.Key_4))
		_action10.setCheckable(True)
		_action10.setVisible(False)
		self.sf_gui.ui.menuFile.addAction(_action10)
		
		self.sf_gui.list_action = [_action1, _action2, _action3, _action4, _action5, _action6, _action7, _action8, _action9, _action10]
		

	def initListOfFiles(self):
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
		_list_files = [file1, file2, file3, file4, file5, file6, file7, file8, file9, file10]
		self.list_files = _list_files

	def	initGui(self):
		_list_files = self.list_files
		for i in range(len(_list_files)):
			_file = _list_files[i]
			if _file != '':
				self.sf_gui.list_action[i].setText(_file)
				self.sf_gui.list_action[i].setVisible(True)
				self.sf_gui.ui.menuFile.addAction(self.sf_gui.list_action[i])
				
	def activateFileAtIndex(self, index):			
		self.currently_activated_file = index
		for i in range(len(self.list_files)):
			self.sf_gui.list_action[i].setChecked(False)
		self.sf_gui.list_action[index].setChecked(True)