from utilities import removeEmptyStrElementAndUpdateIndexSelected

class CheckSfRunReductionButtonStatus(object):
	
	sf_gui = None
	
	def __init__(cls, parent=None):
		cls.sf_gui = parent
				
	def isIncidentMediumReady(cls):
		_list = [str(cls.sf_gui.ui.incidentMediumComboBox.itemText(i)) for i in range(1,cls.sf_gui.ui.incidentMediumComboBox.count())]
		_current_index = cls.sf_gui.ui.incidentMediumComboBox.currentIndex()-1
		[_list, current_index] = removeEmptyStrElementAndUpdateIndexSelected(_list, _current_index)
		if _list == [] or current_index == -1:
			return False
		return True
	
	def isBigTableReady(cls):
		nbr_row = cls.sf_gui.ui.tableWidget.rowCount()
		for _row in range(nbr_row):
			peak1 = str(cls.sf_gui.ui.tableWidget.item(_row, 10).text())
			peak2 = str(cls.sf_gui.ui.tableWidget.item(_row, 11).text())
			back1 = str(cls.sf_gui.ui.tableWidget.item(_row, 12).text())
			back2 = str(cls.sf_gui.ui.tableWidget.item(_row, 13).text())
			
			if (peak1 == 'N/A') or (peak2 == 'N/A') or (back1 == 'N/A') or (back2 == 'N/A'):
				return false
			
			if int(peak1) < int(back1):
				return False
			
			if int(back2) < int(peak2):
				return False
		
		return True
	
	def isOutputFileNameReady(cls):
		output_file_name = cls.sf_gui.ui.sfFileNameLabel.text()
		if output_file_name == 'N/A':
			return False
		return True
	
	def isEverythingReady(cls):
		return (cls.isIncidentMediumReady() and cls.isBigTableReady() and cls.isOutputFileNameReady())