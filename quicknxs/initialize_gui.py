from PyQt4 import QtGui, QtCore
from .version import str_version
from export_stitching_ascii_settings import ExportStitchingAsciiSettings
from .gui_utils import DelayedTrigger
from init_file_menu import InitFileMenu
from reduced_config_files_handler import ReducedConfigFilesHandler
from all_plot_axis import AllPlotAxis

class InitializeGui(object):
	
	self = None
	
	def __init__(cls, self):
		
		cls.self = self
		
		window_title = 'QuickNXS for REF_L'
		self.setWindowTitle(u'%s   %s'%(window_title, str_version))
		self.cache_indicator=QtGui.QLabel("Cache Size: 0.0MB")
		self.ui.statusbar.addPermanentWidget(self.cache_indicator)
		button=QtGui.QPushButton('Empty Cache')
		self.ui.statusbar.addPermanentWidget(button)
		button.pressed.connect(self.empty_cache)
		button.setFlat(True)
		button.setMaximumSize(150, 20)
		
		self.eventProgress=QtGui.QProgressBar(self.ui.statusbar)
		self.eventProgress.setMinimumSize(20, 14)
		self.eventProgress.setMaximumSize(140, 100)
		self.ui.statusbar.addPermanentWidget(self.eventProgress)
		
		#set up the header of the big table
		verticalHeader = ["Data Run #",u'2\u03b8 (\u00B0)',u'\u03bbmin(\u00c5)',
			          u'\u03bbmax (\u00c5)',u'Qmin (1/\u00c5)',u'Qmax (1/\u00c5)',
			          'Norm. Run #']
		self.ui.reductionTable.setHorizontalHeaderLabels(verticalHeader)
		self.ui.reductionTable.resizeColumnsToContents()
		# define the context menu of the recap table
		self.ui.reductionTable.horizontalHeader().setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
		self.ui.reductionTable.horizontalHeader().customContextMenuRequested.connect(self.handleReductionTableMenu)
	    
		# set up the header of the scaling factor table
		verticalHeader = ["Data Run #","SF: auto","SF: manual","SF: 1"]
		self.ui.dataStitchingTable.setHorizontalHeaderLabels(verticalHeader)
		self.ui.dataStitchingTable.resizeColumnsToContents()
		
		palette_green = QtGui.QPalette()
		palette_green.setColor(QtGui.QPalette.Foreground, QtCore.Qt.green)
		self.ui.sf_found_label.setPalette(palette_green)
		
		palette_red = QtGui.QPalette()
		palette_red.setColor(QtGui.QPalette.Foreground, QtCore.Qt.red)
		self.ui.sf_not_found_label.setPalette(palette_red)
	    
		# set up header for reduced ascii table
		verticalHeader = ["ASCII files", "Active"]
		self.ui.reducedAsciiDataSetTable.setHorizontalHeaderLabels(verticalHeader)
		self.ui.reducedAsciiDataSetTable.setColumnWidth(0,249)
		self.ui.reducedAsciiDataSetTable.setColumnWidth(1,49)
	    
		self.exportStitchingAsciiSettings = ExportStitchingAsciiSettings()
	    
		self.ui.plotTab.setCurrentIndex(0)
		# start a separate thread for delayed actions
		self.trigger=DelayedTrigger()
		self.trigger.activate.connect(self.processDelayedTrigger)
		self.trigger.start()
		
		cls.defineRightDefaultPath()
		cls.initFileMenu()
		self.reducedFilesLoadedObject = ReducedConfigFilesHandler(self)
		cls.initConfigGui()
		cls.initErrorWidgets()
		self.allPlotAxis = AllPlotAxis()
		
		self.ui.numberSearchEntry.setFocus()
		
	def defineRightDefaultPath(cls):
		import socket
		if socket.gethostname() == 'lrac.sns.gov':
			cls.self.path_config = '/SNS/REF_L/'
			cls.self.path_ascii = '/SNS/REF_L'
		
	def initFileMenu(cls):
		cls.self.fileMenuObject = InitFileMenu(cls.self)
		
	def initConfigGui(cls):
		from quicknxs.config import refllastloadedfiles
		refllastloadedfiles.switch_config('config_files')
		if refllastloadedfiles.config_files_path != '':
			cls.self.path_config =  refllastloadedfiles.config_files_path
		
	def initErrorWidgets(cls):  
		self = cls.self
		palette = QtGui.QPalette()
		palette.setColor(QtGui.QPalette.Foreground, QtCore.Qt.red)
		self.ui.data_peak1_error.setVisible(False)
		self.ui.data_peak1_error.setPalette(palette)
		self.ui.data_peak2_error.setVisible(False)
		self.ui.data_peak2_error.setPalette(palette)
		self.ui.data_back1_error.setVisible(False)
		self.ui.data_back1_error.setPalette(palette)
		self.ui.data_back2_error.setVisible(False)
		self.ui.data_back2_error.setPalette(palette)
		self.ui.norm_peak1_error.setVisible(False)
		self.ui.norm_peak1_error.setPalette(palette)
		self.ui.norm_peak2_error.setVisible(False)
		self.ui.norm_peak2_error.setPalette(palette)
		self.ui.norm_back1_error.setVisible(False)
		self.ui.norm_back1_error.setPalette(palette)
		self.ui.norm_back2_error.setVisible(False)
		self.ui.norm_back2_error.setPalette(palette)
		self.ui.data_selection_error_label.setVisible(False)
		self.ui.data_selection_error_label.setPalette(palette)
		self.ui.norm_selection_error_label.setVisible(False)
		self.ui.norm_selection_error_label.setPalette(palette)
		