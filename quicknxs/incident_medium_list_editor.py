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
		text_medium = cls.ui.textEdit.toPlainText()
		text_list = text_medium.split('\n')
		[text_list, current_index] = removeEmptyStrElementAndUpdateIndexSelected(text_list, cls.current_index)
		text_list.insert(0, 'Select or Define Incident Medium ...')
		cls.sf_gui.ui.incidentMediumComboBox.clear()
		cls.sf_gui.ui.incidentMediumComboBox.addItems(text_list)
		cls.sf_gui.ui.incidentMediumComboBox.setCurrentIndex(current_index)
		cls.close()
		