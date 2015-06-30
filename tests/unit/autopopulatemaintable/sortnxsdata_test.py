import unittest
import numpy as np
import sys
from os import path
from mock import MagicMock, patch
sys.modules['qreduce'] = MagicMock()
sys.modules['compare_two_nxsdata'] = MagicMock()
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from quicknxs.autopopulatemaintable.sort_nxsdata import SortNXSData, MyError


class TestSortNXSData(unittest.TestCase):

    def setUp(self):
        ''''setup variables used by tests '''
        self.list_nxs = np.array(('nxs1', 'nxs2', 'nxs3'))
        self.criteria1 = ['arg1', 'decreasing']
        self.criteria2 = ['arg2', 'increasing']
        self.parent = MagicMock()

    def test_missing_array_to_sort(self):
        self.assertRaises(MyError, SortNXSData)

    def test_missing_criteria1(self):
        self.assertRaises(MyError, SortNXSData, array_nxsdata_to_sort=self.list_nxs)
    
    def test_1_nxs_list_case(self):
        sort_nxs = SortNXSData(array_nxsdata_to_sort=['nxs1'], criteria1=self.criteria1)
        sorted_list = sort_nxs.sorted_array_of_nxsdata
        self.assertEqual(['nxs1'], sorted_list)
        
    def test_compare_two_nxsdata_for_loop(self):
        '''Assert that 3 nexus are correctly sorted'''
        compare_two_nxsdata_object = MagicMock()
        compare_two_nxsdata_object.result = MagicMock(return_value=1)
        with patch('compare_two_nxsdata.CompareTwoNXSData', 
                   MagicMock(return_value=compare_two_nxsdata_object)) as mock:
            sort_nxs = SortNXSData(array_nxsdata_to_sort=self.list_nxs,
                                   criteria1=self.criteria1,
                                   criteria2=self.criteria2)
            sorted_array_result = sort_nxs.sorted_array_of_nxsdata
            self.assertEqual(self.list_nxs, sorted_array_result)
        
        

if __name__ == '__main__':
    unittest.main()
