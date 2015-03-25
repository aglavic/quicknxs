from load_sf_config_xml_file import LoadSFConfigXmlFile
from numpy import empty
from fill_sf_gui_table import FillSFGuiTable

class LoadSFConfigAndPopulateGUI(object):
	
	sf_gui = None
	filename = ''
	loading_status = False
	dom = None
	incident_medium_list = []
	incident_medium_index_selected = -1
	sf_data_table = None
	is_using_si_slits = False

	INFO_MSG = 'Select or Define Incident Medium ...'
	
	def __init__(cls, parent=None, filename=''):
		cls.filename = filename
		cls.sf_gui = parent
		
		_domObject = LoadSFConfigXmlFile(parent=parent, filename=filename)
		if _domObject.getLoadingStatus():
			cls.dom = _domObject.getDom()
			cls.parseDom()
			cls.populateSFGui()
			
		cls.sf_gui.big_table = cls.sf_data_table
		cls.loading_status = True

	def populateSFGui(cls):
		_sf_data_table = cls.sf_data_table
		cls.populateIncidentMedium()
		_fill_sf_gui = FillSFGuiTable(parent=cls.sf_gui, table=_sf_data_table, is_using_si_slits=cls.is_using_si_slits)

	def clearSFtable(cls):
		cls.sf_gui.ui.tableWidget.clearContents()
		nbrRow = cls.sf_gui.ui.tableWidget.rowCount()
		if nbrRow > 0:
			for _row in range(nbrRow):
				cls.sf_gui.ui.tableWidget.removeRow(0)
			
	def populateIncidentMedium(cls):
		cls.incident_medium_list.insert(0, cls.INFO_MSG)
		cls.incident_medium_index_selected += 1
		
		cls.sf_gui.ui.incidentMediumComboBox.clear()
		cls.sf_gui.ui.incidentMediumComboBox.addItems(cls.incident_medium_list)
		cls.sf_gui.ui.incidentMediumComboBox.setCurrentIndex(cls.incident_medium_index_selected)

		
	def parseDom(cls):
		_dom = cls.dom
		_reflsfdata = _dom.getElementsByTagName('RefLSFCalculator')
		nbr_row = len(_reflsfdata)
		
		_sf_data_table = empty((nbr_row, 16), dtype=object)
		for index, node in enumerate(_reflsfdata):
			if index == 0:
				cls.incident_medium_index_selected =int(cls.getNodeValue(node, 'incident_medium_index_selected'))
				cls.incident_medium_list = cls.getNodeValue(node, 'incident_medium_list').split(',')
				cls.is_using_si_slits = cls.getNodeValue(node,'is_using_si_slits')
			
			_sf_data_table[index, 0] = cls.getNodeValue(node, 'data_file')
			_sf_data_table[index, 1] = cls.getNodeValue(node, 'number_attenuator')
			_sf_data_table[index, 2] = cls.getNodeValue(node, 'lambda_min')
			_sf_data_table[index, 3] = cls.getNodeValue(node, 'lambda_max')
			_sf_data_table[index, 4] = cls.getNodeValue(node, 'proton_charge')
			_sf_data_table[index, 5] = cls.getNodeValue(node, 'lambda_requested')
			_sf_data_table[index, 6] = cls.getNodeValue(node, 's1w')
			_sf_data_table[index, 7] = cls.getNodeValue(node, 's1h')
			_sf_data_table[index, 8] = cls.getNodeValue(node, 'si2w')
			_sf_data_table[index, 9] = cls.getNodeValue(node, 'si2h')
			_sf_data_table[index, 10] = cls.getNodeValue(node, 'peak1')
			_sf_data_table[index, 11] = cls.getNodeValue(node, 'peak2')
			_sf_data_table[index, 12] = cls.getNodeValue(node, 'back1')
			_sf_data_table[index, 13] = cls.getNodeValue(node, 'back2')
			_sf_data_table[index, 14] = cls.getNodeValue(node, 'tof1')
			_sf_data_table[index, 15] = cls.getNodeValue(node, 'tof2')
			
		cls.sf_data_table = _sf_data_table

	def getLoadingStatus(cls):
		return cls.loading_status
			
	def getNodeValue(cls, node, flag):
		try:
			_tmp = node.getElementsByTagName(flag)
			_value = _tmp[0].childNodes[0].nodeValue
		except:
			_value = ''
		return _value
	