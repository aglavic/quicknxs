from compare_two_nxsdata_for_sfcalculator import CompareTwoNXSDataForSFcalculator
from qreduce import NXSData

class Position(object):
	before = -1
	same = 0
	after = 1

class SortNXSData(object):

	sortedArrayOfNXSData = None
	
	def __init__(cls, arrayOfNXSDataToSort): 
		nbr_runs = len(arrayOfNXSDataToSort)
		if nbr_runs<2:
			cls.sortedArrayOfNXSData = arrayOfNXSDataToSort
						
		_sortedArrayOfNXSData = [arrayOfNXSDataToSort[0]]
		_positionIndexNXSDataToPosition=0
		for indexToPosition in range(1,nbr_runs):
			_nxsdataToPosition = arrayOfNXSDataToSort[indexToPosition]
			for indexInPlace in range(len(_sortedArrayOfNXSData)):
				_nxsdataToCompareWith = _sortedArrayOfNXSData[indexInPlace]
				compareTwoNXSData = CompareTwoNXSDataForSFcalculator(_nxsdataToCompareWith, _nxsdataToPosition)
				_isBeforeSameOrAfter = compareTwoNXSData.result()
				if _isBeforeSameOrAfter == Position.before:
					_positionIndexNXSDataToPosition = indexInPlace
					break
				elif _isBeforeSameOrAfter == Position.after:
					_positionIndexNXSDataToPosition += 1
				else:
					_new_nxsdata = cls.mergedNXSData(_nxsdataToPosition, _nxsdataToCompareWith)
					_sortedArrayOfNXSData[indexToPosition] = _new_nxsdata
					break
			_sortedArrayOfNXSData.insert(_positionIndexNXSDataToPosition, _nxsdataToPosition)
		cls.sortedArrayOfNXSData = _sortedArrayOfNXSData	
					
	def mergedNXSData(cls, nxsdata1, nxsdata2):
		_full_file_name1 = nxsdata1.active_data.full_file_name
		_full_file_name2 = nxsdata2.active_data.full_file_name
		_new_nxsdata =  NXSData([_full_file_name1, _full_file_name2], bins=500)
		return _new_nxsdata
	
	def getSortedList(cls):
		return cls.sortedArrayOfNXSData