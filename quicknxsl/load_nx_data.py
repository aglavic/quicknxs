from qreduce import NXSData
import utilities

class LoadNXData(object):
	
	nx_data = None
	
	def __init__ (cls, list_of_runs, is_auto_peak_finder=True):
		_list_nx = []
		for _runs in list_of_runs:
			_full_file_name = utilities.findFullFileName(_runs)
			if _full_file_name != '':
				_list_nx.append(_full_file_name)
		
		if _list_nx != []:
			cls.nx_data = NXSData(_list_nx, bins=500, is_auto_peak_finder= is_auto_peak_finder)
	
	def getNXData(cls):
		return cls.nx_data