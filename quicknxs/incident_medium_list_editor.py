from PyQt4.QtGui import QDialog
from PyQt4.QtCore import Qt
from incident_medium_list_editor_interface import Ui_Dialog as UiDialog
from utilities import removeEmptyStrElementAndUpdateIndexSelected


class IncidentMediumListEditor(QDialog):
	
	sf_gui = None
	current_index = -1
	
	def __init__(cls,  parent=None):
		cls.sf_gui = parent
		
		QDialog.__init__(cls, parent=parent)
		cls.setWindowModality(False)
		cls.ui = UiDialog()
		cls.ui.setupUi(cls)
		
		cls.initGui()
		
	def initGui(cls):
		_list = [str(cls.sf_gui.ui.incidentMediumComboBox.itemText(i)) for i in range(1,cls.sf_gui.ui.incidentMediumComboBox.count())]
		cls.current_index = cls.sf_gui.ui.incidentMediumComboBox.currentIndex()-1
		[_list, current_index] = removeEmptyStrElementAndUpdateIndexSelected(_list, cls.current_index)
		cls.fillGui(_list)
		
	def fillGui(cls, _list):
		_text = "\n".join(_list)
		cls.ui.textEdit.setText(_text)
		
	def validateEvent(cls):
		print 'in validate'
		