import unittest
import numpy as np
import sys
from os import path
from mock import MagicMock
sys.modules['qreduce'] = MagicMock()
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from quicknxs.autopopulatemaintable.sort_nexus_list import SortNexusList, MyError

class TestMainTableAutoFill(unittest.TestCase):

    def setUp(self):
        ''''setup variables used by tests '''
        self.list_nxs = np.array(('a', 'b'))
        self.criteria1 = ['arg1', 'decreasing']
        self.criteria2 = ['arg2', 'increasing']

    def test_no_arguments_provided(self):
        ''' Assert error is thrown if no arguments '''
        self.assertRaises(MyError, SortNexusList)

    def test_no_list_1_criteria_provided(self):
        ''' Assert error is thrown if no list of nexus  with criteria1'''
        self.assertRaises(MyError, SortNexusList, criteria1=['a', 'decreasing'])

    def test_no_list_2_criterias_provided(self):
        ''' Assert error is thrown if no list of nexus with criteria1 and criteria2 '''
        self.assertRaises(MyError, SortNexusList,
                          criteria1=['a', 'decreasing'],
                          criteria2=['b', 'increasing'])

    def test_no_criteria_provided(self):
        ''' Assert error is thrown if no criteria '''
        self.assertRaises(MyError, SortNexusList, list_nxs=self.list_nxs)

    def test_wrong_list_nxs_type(self):
        ''' Assert error is thrown if wrong type of list of nexus '''
        self.assertRaises(MyError, SortNexusList, list_nxs='14345')

    def test_wrong_criteria1_too_many_arguments(self):
        ''' Assert error is thrown if too many criteria1 arguments '''
        self.assertRaises(MyError, SortNexusList,
                          list_nxs=self.list_nxs,
                          criteria1=['yo', 'ya', 'yi'])

    def test_wrong_criteria1_too_few_arguments(self):
        ''' Assert error is thrown if too few criteria1 arguments '''
        self.assertRaises(MyError, SortNexusList,
                          list_nxs=self.list_nxs,
                          criteria1=['yo'])

    def test_wrong_criteria1_right_number_arguments_wrong_name(self):
        ''' Assert error is thrown if right number of criteria1 arguments but wrong type '''
        self.assertRaises(MyError, SortNexusList,
                          list_nxs=self.list_nxs,
                          criteria1=['yo', 'ya'])

    def test_wrong_criteria2_too_many_arguments(self):
        ''' Assert error is thrown if too many criteria2 arguments '''
        self.assertRaises(MyError, SortNexusList,
                          list_nxs=self.list_nxs,
                          criteria2=['yo', 'ya', 'yi'])

    def test_wrong_criteria2_too_few_arguments(self):
        ''' Assert error is thrown if too few criteria2 arguments '''
        self.assertRaises(MyError, SortNexusList, list_nxs=self.list_nxs, criteria2=['yo'])

    def test_wrong_criteria2_right_number_arguments_wrong_name(self):
        ''' Assert error is thrown if right number of criteria2 arguments but wrong type '''
        self.assertRaises(MyError, SortNexusList,
                          list_nxs=self.list_nxs,
                          criteria2=['yo', 'ya'])

    def test_pick_up_right_criteria1_arguments(self):
        ''' Assert right criteria1 arguments are retrieved '''
        sortNxs = SortNexusList(list_nxs=self.list_nxs, criteria1=self.criteria1)
        self.assertEqual('arg1', sortNxs.criteria1_value)
        self.assertEqual('decreasing', sortNxs.criteria1_type)

    def test_pick_up_right_criteria2_arguments(self):
        ''' Assert right criteria2 arguments are retrieved '''
        sortNxs = SortNexusList(list_nxs=self.list_nxs, criteria2=self.criteria2)
        self.assertEqual('arg2', sortNxs.criteria2_value)
        self.assertEqual('increasing', sortNxs.criteria2_type)

    def test_sort_1_nxs_list(self):
        ''' Assert sort correctly list of nxs of only 1 elements '''
        list_nxs = np.array(('nxs1'))
        sortNxs = SortNexusList(list_nxs=list_nxs, criteria1=self.criteria1)
        sortNxs.sortList()
        list_nxs_sorted = sortNxs.list_nxs_sorted
        self.assertEqual(list_nxs, list_nxs_sorted)

if __name__ == '__main__':
    unittest.main()
    