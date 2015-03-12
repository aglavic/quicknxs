from PyQt4 import QtGui, QtCore
from table_reduction_runs_editor_interface_refl import Ui_MainWindow
from run_sequence_breaker import RunSequenceBreaker
from decorators import waiting_effects
from mantid.simpleapi import *
import nexus_utilities
import utilities


class TableReductionRunEditor(QtGui.QMainWindow):
	
	_open_instances = []
	main_gui = None
	col = 0
	row = 0
	
	list_filename = []
	list_nxs = []
	
	def __init__(cls, parent=None, col=0, row=0):
		cls.main_gui = parent
		cls.col = col
		cls.row = row
		
		QtGui.QMainWindow.__init__(cls, parent=parent)
		cls.setWindowModality(False)
		cls._open_instances.append(cls)
		cls.ui = Ui_MainWindow()
		cls.ui.setupUi(cls)
		
		cls.initGui()
		
	def initGui(cls):
		cls.initLayout()
		cls.initContent()
		
	def initContent(cls):
		cls.ui.lambdaUnits.setText(u'\u00c5')
		
		verticalHeader = ["Data Run #", u'Lambda Requested (\u00c5)', 
		                  'Norm Run', u'Lambda Requested (\u00c5)']
		cls.ui.tableWidget.setHorizontalHeaderLabels(verticalHeader)
		cls.ui.tableWidget.resizeColumnsToContents()
		
		data_run = cls.main_gui.ui.reductionTable.item(cls.row, 0).text()
		norm_run = cls.main_gui.ui.reductionTable.item(cls.row, 6).text()
		if cls.col == 0:
			cls.ui.oldDataRun.setText(data_run)
			cls.ui.normRun.setText(norm_run)
		else:
			cls.ui.dataRun.setText(data_run)
			cls.ui.oldNormRun.setText(norm_run)
			
		config = cls.main_gui.bigTableData[cls.row, 2]

		data_lambda = config.data_lambda_requested
		norm_lambda = config.norm_lambda_requested
		if data_lambda != -1:
			lambda_value = str(data_lambda)
		else:
			lambda_value = str(norm_lambda)
		cls.ui.lambdaValue.setText(lambda_value)

	def initLayout(cls):
		if cls.col == 0: #data then hide norm frame
			cls.ui.norm_groupBox.setHidden(True)
		else:
			cls.ui.data_groupBox.setHidden(True)
					
	def dataLineEditValidate(cls):
		run_sequence = cls.ui.dataLineEdit.text()
		oListRuns = RunSequenceBreaker(run_sequence)
		_list_runs = oListRuns.getFinalList()
		cls.ui.dataLineEdit.setText("")

		cls.list_filename = []
		cls.list_nxs = []
		if _list_runs[0] == -1:
			return
		for _runs in _list_runs:
			try:
				_filename = nexus_utilities.findNeXusFullPath(_runs)
			except:
				pass
			cls.list_filename.append(_filename)
			randomString = utilities.generate_random_workspace_name()
			_nxs = LoadEventNexus(Filename=_filename, OutputWorkspace=randomString, MetaDataOnly=True)
			cls.list_nxs.append(_nxs)
		
	def normLineEditValidate(cls):
		_norm_run = cls.ui.normLineEdit.text()
		cls.ui.normLineEdit.setText("")
		
	def closeEvent(cls, event=None):
		cls.close()
	
	