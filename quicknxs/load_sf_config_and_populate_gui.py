from load_sf_config_xml_file import LoadSFConfigXmlFile
from numpy import empty

class LoadSFConfigAndPopulateGUI(object):
	
	filename = ''
	loading_status = False
	dom = None
	incident_medium_list = []
	incident_medium_index_selected = -1
	sf_data_table = None
	
	def __init__(cls, parent=None, filename=''):
		cls.filename = filename
		
		_domObject = LoadSFConfigXmlFile(parent=parent, filename=filename)
		if _domObject.getLoadingStatus():
			cls.dom = _domObject.getDom()
			sf_data_table = cls.parseDom()
			
		cls.loading_status = True
		
	def parseDom(cls):
		_dom = cls.dom
		nbr_row = len(_dom)
		
		_sf_data_table = empty((nbr_row, 16))
		for index, node in enumerate(_dom):
			if index == 0:
				cls.incident_medium_index_selected = cls.getNodeValue(node, 'incident_medium_index_selected')
				cls.incident_medium_list = cls.getNodeValue(node, 'incident_medium_list')
			
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
	