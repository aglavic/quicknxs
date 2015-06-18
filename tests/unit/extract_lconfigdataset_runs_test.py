import unittest
import sys
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from quicknxs.autopopulatemaintable.extract_lconfigdataset_runs import ExtractLConfigDataSetRuns
from mock import MagicMock
from quicknxs.lconfigdataset import LConfigDataset
from numpy import empty

class TestMainTableAutoFill(unittest.TestCase):
    
    def setUp(self):
        ''''setup variables used by tests '''
        self.list_of_run_from_input = "1,2"

    def test_correct_simple_list_of_lconfig(self):
        ''' Assert correct list of runs reported '''
        main_gui = MagicMock()
        _lconfig1 = LConfigDataset()
        _lconfig1.data_sets = '1'
        _lconfig2 = LConfigDataset()
        _lconfig2.data_sets = '2'
        _lconfig3 = LConfigDataset()
        _lconfig3.data_sets = '3'
        lconfigdataset = [_lconfig1, _lconfig2, _lconfig3]
        _extractor = ExtractLConfigDataSetRuns(lconfigdataset = lconfigdataset)
        list_runs = _extractor.list_runs()
        self.assertEqual([1,2,3], list_runs)

    def test_empty_lconfig(self):
        ''' Assert empty list of runs if empty lconfig '''
        main_gui = MagicMock()
        lconfigdataset = []
        _extractor = ExtractLConfigDataSetRuns(lconfigdataset = lconfigdataset)
        list_runs = _extractor.list_runs()
        self.assertEqual([], list_runs)

if __name__ == '__main__':
    unittest.main()