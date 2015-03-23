from utilities import createAsciiFile
import os

class CreateSFConfigXmlFile(object):
	
	sf_gui = None
	output_filename = ''
	str_array = []
	list_item = ['data_file','number_attenuator','lambda_min','lambda_max',
	               'proton_charge','lambda_requested','s1w','s1h','si2w','si2h',
	               'peak1','peak2','back1','back2','tof1','tof2']
	
	def __init__(cls, parent=None, filename=''):
		cls.sf_gui = parent
		cls.output_filename = filename
		
		cls.topPart()
		cls.mainPart()
		cls.bottomPart()
		
		cls.createConfigFile()

	def topPart(cls):
		str_array = cls.str_array
		str_array.append('<Reduction>\n')
		str_array.append(' <instrument_name>REFSF</instrument_name>\n')
		
		# time stamp
		import datetime
		str_array.append(' <timestamp>' + datetime.datetime.now().strftime("%A, %d. %B %Y %I:%M%p") + '</timestamp>\n')
		
		# python version
		import sys
		str_array.append(' <python_version>' + sys.version + '</python_version>\n')
		
		# platform
		import platform
		str_array.append(' <platform>' + platform.system() + '</platform>\n')
		
		# architecture
		str_array.append(' <architecture>' + platform.machine() + '</architecture>\n')
		
		# mantid version
		import mantid
		str_array.append(' <mantid_version>' + mantid.__version__ + '</mantid_version>\n')
		
		# metadata
		str_array.append('<DataSeries>\n')
		
		cls.str_array = str_array
		
	
	def bottomPart(cls):
		str_array = cls.str_array
		
		str_array.append('</DataSeries>\n')
		str_array.append('</Reduction>\n')
		
		cls.str_array = str_array
	
	def mainPart(cls):
		data_table_ui = cls.sf_gui.ui.tableWidget
		nbr_row = data_table_ui.rowCount()
		if nbr_row == 0:
			return []

		[_incident_medium_list, _incident_medium_index] = cls.retrieveIncidentMediumListAndIndex()
		
		str_array = cls.str_array
		for row in range(nbr_row):
			
			str_array.append(' <RefLSFCalculator>\n')
			str_array.append(' <incident_medium_list>' + _incident_medium_list + '</incident_medium_list>\n')
			str_array.append(' <incident_medium_index_selected>' + str(_incident_medium_index) + '</incident_medium_index_selected>\n')
			
			for col in range(16):
				if col == 1:
					_item = str(data_table_ui.cellWidget(row, col).value())
				else:
					_item = str(data_table_ui.item(row, col).text())
					
				str_array.append(cls.builtItemString(index=col, item=_item))

			str_array.append(' </RefLSFCalculator>\n')
		
		cls.str_array = str_array

	def 	builtItemString(cls, index=0, item=''):			
		_list_item = cls.list_item
		_item_str = _list_item[index]
		_str = ' <' + _list_item[index] + '>' + item +'</' + _list_item[index] + '>\n'
		return _str
		
	def retrieveIncidentMediumListAndIndex(cls):
		_list = [str(cls.sf_gui.ui.incidentMediumComboBox.itemText(i)) for i in range(1,cls.sf_gui.ui.incidentMediumComboBox.count())]
		_current_index = cls.sf_gui.ui.incidentMediumComboBox.currentIndex()-1
		_str_list = ",".join(_list)
		return [_str_list, _current_index]

	def createConfigFile(cls):
		createAsciiFile(cls.output_filename, cls.str_array)