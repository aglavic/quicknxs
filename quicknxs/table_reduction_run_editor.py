from PyQt4 import QtGui, QtCore
from table_reduction_runs_editor_interface_refl import Ui_Dialog

class TableReductionRunEditor(QtGui.QDialog):
	
	_open_instances = []
	main_gui = None
	col = 0
	row = 0
	
	def __init__(cls, parent=None, col=0, row=0):
		cls.main_gui = parent
		cls.col = col
		cls.row = row
		
		QtGui.QDialog.__init__(cls, parent=parent)
		cls.setWindowModality(False)
		cls._open_instances.append(cls)
		cls.ui = Ui_Dialog()
		cls.ui.setupUi(cls)
		
		cls.initGui()
		
	def initGui(cls):
		cls.initLayout()
		cls.initContent()
		
	def initContent(cls):
		cls.ui.oldDataLambdaUnits.setText(u'\u00c5')
		cls.ui.dataLambdaUnits.setText(u'\u00c5')
		cls.ui.oldNormLambdaUnits.setText(u'\u00c5')
		cls.ui.normLambdaUnits.setText(u'\u00c5')
		
		verticalHeader = ["Data Run #", u'Lambda Requested (\u00c5)', 'Norm Run', u'Lambda Requested (\u00c5)']
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
			
			
		
		
	def initLayout(cls):
		if cls.col == 0: #data then hide norm frame
			cls.ui.norm_groupBox.setHidden(True)
		else:
			cls.ui.data_groupBox.setHidden(True)