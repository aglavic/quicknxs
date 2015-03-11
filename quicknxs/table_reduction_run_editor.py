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
		if cls.col == 0: #data then hide norm frame
			cls.ui.norm_groupBox.setHidden(True)
		else:
			cls.ui.data_groupBox.setHidden(True)