from qreduce import NXSData
from compare_two_nxsdata import CompareTwoNXSData

class MyError(Exception):
    def __init(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class SortNXSData(object):

    sorted_array_of_nxsdata = None
    sf_gui = None

    def __init__(self,  
                 parent = None, 
                 array_nxsdata_to_sort = None, 
                 criteria1 = None,
                 criteria2 = None): 

        if array_nxsdata_to_sort is None:
            raise MyError("need something to sort")
        nbr_runs = len(array_nxsdata_to_sort)

        if (criteria1 is None):
            raise MyError("Need criteria1 to work")

        if nbr_runs<2:
            self.sorted_array_of_nxsdata = array_nxsdata_to_sort
            return

        self.sf_gui = parent
        _sorted_array_of_nxsdata = [array_nxsdata_to_sort[0]]
        _positionIndexNXSDataToPosition=0

        for source_index in range(1,nbr_runs):
            _is_same_nxs = False
            _nxsdataToPosition = array_nxsdata_to_sort[source_index]
            for indexInPlace in range(len(_sorted_array_of_nxsdata)):
                _nxsdataToCompareWith = _sorted_array_of_nxsdata[indexInPlace]
                compare_two_nxsdata_object = CompareTwoNXSData(nxsdata_to_compare_with= _nxsdataToCompareWith, 
                                                      nxsdata_to_position =_nxsdataToPosition,
                                                      criteria1 = criteria1,
                                                      criteria2 = criteria2)
                _is_before_same_or_after = compare_two_nxsdata_object.result()
                if _is_before_same_or_after == Position.before:
                    _positionIndexNXSDataToPosition = indexInPlace
                    break
                elif _is_before_same_or_after == Position.after:
                    _positionIndexNXSDataToPosition += 1
                else:
                    _new_nxsdata = self.merged_nxsdata(_nxsdataToPosition, _nxsdataToCompareWith)
                    _sorted_array_of_nxsdata[indexInPlace] = _new_nxsdata
                    _is_same_nxs = True
                    break
            if not _is_same_nxs:
                _sorted_array_of_nxsdata.insert(_positionIndexNXSDataToPosition, _nxsdataToPosition)
        self.sorted_array_of_nxsdata = _sorted_array_of_nxsdata	

    def merged_nxsdata(self, nxsdata1, nxsdata2):
        _full_file_name1 = nxsdata1.active_data.filename
        _full_file_name2 = nxsdata2.active_data.filename
        _new_nxsdata =  NXSData([_full_file_name1, _full_file_name2], bins=self.sf_gui.bin_size, is_auto_peak_finder=True)
        return _new_nxsdata

