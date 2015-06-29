import numpy as np
from qreduce import NXSData
import sys
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from quicknxs.autopopulatemaintable.sort_nxsdata import SortNXSData

class myError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class SortNexusList(object):
    '''
    Will sort the NXSData list (numpy.ndarray) provided according to the criteria1 and criteria2
    where criteria1 and criteria2 looks like ['name_argumne','sort_order']
    sort_order is either 'increasing' or 'decreasing'
    '''
    
    parent = None
    
    list_nxs_sorted = None
    criteria_type = ['increasing','decreasing']
    raw_list_nxs = None
    
    criteria1_value = None
    criteria1_type = ''
    
    criteria2_value = None
    criteria2_type = ''
        
    def __init__(self, parent = None, list_nxs = None, criteria1 = None, criteria2 = None):
        if list_nxs is None:
            raise myError("Need a list of nexus")
        if type(list_nxs) is not np.ndarray:
            raise myError("Need a numpy nexus_list array")
        if criteria1 is None and criteria2 is None:
            raise myError("Need at least 1 criteria")

        if criteria1 is not None:
            if len(criteria1) != 2:
                raise myError("Wrong criteria arguments number!")
            if not criteria1[1] in self.criteria_type:
                raise myError("Wrong criteria1 argument name")
            [self.criteria1_value, self.criteria1_type] = criteria1

        if criteria2 is not None:
            if len(criteria2) != 2:
                raise myError("Wrong criteria arguments number!")
            if not criteria2[1] in self.criteria_type:
                raise myError("Wrong criteria2 argument name")
            [self.criteria2_value, self.criteria2_type] = criteria2
            
        self.raw_list_nxs = list_nxs
        self.parent = parent
 
    def sortList(self):
        _list_nxs = self.raw_list_nxs
        nbr_nxs = _list_nxs.size
        if nbr_nxs == 1:
            self.list_nxs_sorted = _list_nxs
            return
        
        sortnxs = SortNXSData(parent = self.parent, array_nxsdata_to_sort = _list_nxs)
        list_nxs_sorted = sortnxs.sortedArrayOfNXSData
        
    
        
        
        
