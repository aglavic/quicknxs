import unittest
from numpy import empty
import sys
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from quicknxs.autopopulatemaintable.maintableautofill import MainTableAutoFill
from mock import MagicMock
from quicknxs.lconfigdataset import LConfigDataset


class TestMainTableAutoFill(unittest.TestCase):
    
    def setUp(self):
        ''''setup variables used by tests '''
        pass

    ## step0 ##
    def test_null_raw_list(self):
        ''' Step0 - raw list is None '''
        maintable = MainTableAutoFill()
        sorted_list_runs = maintable.sorted_list_of_runs
        self.assertEqual(sorted_list_runs, [])

    def test_empty_raw_list(self):
        ''' Step0 - input raw list of runs is empty'''
        maintable = MainTableAutoFill(raw_list_of_runs='')
        sorted_list_runs = maintable.sorted_list_of_runs
        self.assertEqual(sorted_list_runs, [])

    def test_check_raw_list_case1(self):
        ''' Step0 - Assert raw list of runs correctly given (case 1)'''
        maintable = MainTableAutoFill(raw_list_of_runs='1, 2, 3, 4, 5')
        raw_list_runs = maintable.raw_list_of_runs
        self.assertEqual(raw_list_runs, '1, 2, 3, 4, 5')

    def test_check_raw_list_case2(self):
        ''' Step0 - Assert raw list of runs correctly given (case2)'''
        maintable = MainTableAutoFill(raw_list_of_runs='1, 2, 4-10, 15, 16')
        raw_list_runs = maintable.raw_list_of_runs
        self.assertEqual(raw_list_runs, '1, 2, 4-10, 15, 16')

    def test_check_data_type_data(self):
        ''' Step0 - check that passing nothing will use data as data type'''
        maintable = MainTableAutoFill()
        data_type = maintable.data_type_selected
        self.assertEqual(data_type, 'data')

    def test_check_data_type_norm(self):
        ''' Step0 - check that passing norm will use it as data type'''
        maintable = MainTableAutoFill(data_type_selected='norm')
        data_type = maintable.data_type_selected
        self.assertEqual(data_type, 'norm')

    ## step1 ##
    def test_list_of_files_case1(self):
        ''' Step1 - check discrete list of files - [1, 2, 3, 4, 5]'''
        maintable = MainTableAutoFill(raw_list_of_runs='1, 2, 3, 4, 5')
        data_list = maintable.discrete_list_of_runs
        self.assertEqual(data_list, [1, 2, 3, 4, 5])
        
    def test_list_of_files_case2(self):
        ''' Step1 - check discrete list of files - [1, 2, 3, 5-10, 15, 16]'''
        maintable = MainTableAutoFill(raw_list_of_runs='1, 2, 3, 5-10, 15, 16')
        data_list = maintable.discrete_list_of_runs
        self.assertEqual(data_list, [1, 2, 3, 5, 6, 7, 8, 9, 10, 15, 16])

    def test_list_of_files_case3(self):
        ''' Step1 - check discrete list of files - [1, 5-10, 15, 16, 20-22]'''
        maintable = MainTableAutoFill(raw_list_of_runs='1, 5-10, 15, 16, 20-22')
        data_list = maintable.discrete_list_of_runs
        self.assertEqual(data_list, [1, 5, 6, 7, 8, 9, 10, 15, 16, 20, 21, 22])

    ## step2 ##
    def test_check_input_parameters_case1(self):
        ''' Step2 - check that there are no pre-loaded data in BigTableData (3rd column)'''
        main_gui = None
        maintable = MainTableAutoFill(main_gui = main_gui)
        program_main_gui = maintable.main_gui
        self.assertEqual(main_gui, program_main_gui)

    def test_check_input_parameters_case2(self):
        ''' Step2 - check that there are no pre-loaded data in BigTableData (3rd column) with a false reset table flag'''
        main_gui = None
        maintable = MainTableAutoFill(main_gui = main_gui, reset_table=False)
        program_main_gui = maintable.main_gui
        self.assertEqual(main_gui, program_main_gui)
        
    def test_check_input_parameters_case3(self):
        ''' Step2 - check that there are no pre-loaded data in BigTableData (3rd column) with a true reset table flag'''
        main_gui = None
        maintable = MainTableAutoFill(main_gui = main_gui, reset_table=True)
        program_main_gui = maintable.main_gui
        self.assertEqual(main_gui, program_main_gui)

    def test_check_input_parameters_case4(self):
        ''' Step2 - check that there are no pre-loaded data in BigTableData (3rd column)'''
        main_gui = MagicMock()
        main_gui.BigTableData = empty((20,3), dtype=object)
        maintable = MainTableAutoFill(main_gui= main_gui)
        program_main_gui = maintable.main_gui
        self.assertEqual(main_gui, program_main_gui)
    
    def test_check_input_parameters_case5(self):
        ''' Step2 - check that there are no pre-loaded data in BigTableData (3rd column) with true reset table'''
        main_gui = MagicMock()
        main_gui.BigTableData = empty((20,3), dtype=object)
        maintable = MainTableAutoFill(main_gui= main_gui, reset_table=True)
        program_main_gui = maintable.main_gui
        self.assertEqual(main_gui, program_main_gui)

    def test_check_input_parameters_case6(self):
        ''' Step2 - Make sure that if data have been loaded, the 3rd column of bigTable is not empty'''
        main_gui = MagicMock()
        main_gui.bigTableData = empty((20,3), dtype=object)
        main_gui.bigTableData[0:5,2] = LConfigDataset()
        maintable = MainTableAutoFill(main_gui= main_gui)
        _maintable_big_table_data = maintable.big_table_data
        _maintable_big_table_data_3rd_column = _maintable_big_table_data[0,2]
        self.assertIsInstance(_maintable_big_table_data_3rd_column, LConfigDataset)
        
    def test_check_input_parameters_case7(self):
        ''' Step2 - Make sure that if data have been loaded, the 3rd column of bigTable is not empty with true reset table'''
        main_gui = MagicMock()
        main_gui.bigTableData = empty((20,3), dtype=object)
        main_gui.bigTableData[0:5,2] = LConfigDataset()
        maintable = MainTableAutoFill(main_gui= main_gui, reset_table=True)
        _maintable_big_table_data = maintable.big_table_data
        self.assertEqual(_maintable_big_table_data, None)

    def test_check_input_parameters_case8(self):
        ''' Step2 - Make sure that if data have been loaded, the 3rd column of bigTable is not empty
        and they have runs defined '''
        main_gui = MagicMock()
        main_gui.bigTableData = empty((20,3), dtype=object)
        _lconfig1 = LConfigDataset()
        _lconfig1.data_sets = '123'
        _lconfig2 = LConfigDataset()
        _lconfig2.data_sets = '456'
        _lconfig3 = LConfigDataset()
        _lconfig3.data_sets = '789'
        main_gui.bigTableData[0:3,2] = [_lconfig1, _lconfig2, _lconfig3]
        maintable = MainTableAutoFill(main_gui= main_gui)
        _maintable_big_table_data = maintable.big_table_data
        _maintable_big_table_data_3rd_column = _maintable_big_table_data[0:3,2]
        _first_data_set = _maintable_big_table_data_3rd_column[0].data_sets
        self.assertEqual(_first_data_set, '123')
        
    def test_check_input_parameters_case9(self):
        ''' Step2 - Make sure that if data have been loaded, the 3rd column of bigTable is not empty
        and they have runs defined with reset table'''
        main_gui = MagicMock()
        main_gui.bigTableData = empty((20,3), dtype=object)
        _lconfig1 = LConfigDataset()
        _lconfig1.data_sets = '123'
        _lconfig2 = LConfigDataset()
        _lconfig2.data_sets = '456'
        _lconfig3 = LConfigDataset()
        _lconfig3.data_sets = '789'
        main_gui.bigTableData[0:3,2] = [_lconfig1, _lconfig2, _lconfig3]
        maintable = MainTableAutoFill(main_gui= main_gui, reset_table=True)
        _maintable_big_table_data = maintable.big_table_data
        self.assertEqual(_maintable_big_table_data, None)

    def test_check_input_parameters_case10(self):
        ''' Step2 - Make sure that if data have been loaded, the 3rd column of bigTable is not empty
        and they have runs defined '''
        main_gui = MagicMock()
        main_gui.bigTableData = empty((20,3), dtype=object)
        _lconfig1 = LConfigDataset()
        _lconfig1.data_sets = '123'
        _lconfig2 = LConfigDataset()
        _lconfig2.data_sets = '456'
        _lconfig3 = LConfigDataset()
        _lconfig3.data_sets = '789'
        main_gui.bigTableData[0:3,2] = [_lconfig1, _lconfig2, _lconfig3]
        maintable = MainTableAutoFill(main_gui= main_gui)
        _maintable_big_table_data = maintable.big_table_data
        _maintable_big_table_data_3rd_column = _maintable_big_table_data[0:3,2]
        _first_data_set = _maintable_big_table_data_3rd_column[0].data_sets
        self.assertNotEqual(_first_data_set, '222')
    
    def test_check_input_parameters_case11(self):
        ''' Step2 - Make sure that if data have been loaded, the 3rd column of bigTable is not empty
        and they have runs defined '''
        main_gui = MagicMock()
        main_gui.bigTableData = empty((20,3), dtype=object)
        _lconfig1 = LConfigDataset()
        _lconfig1.data_sets = '123'
        _lconfig2 = LConfigDataset()
        _lconfig2.data_sets = '456'
        _lconfig3 = LConfigDataset()
        _lconfig3.data_sets = '789'
        main_gui.bigTableData[0:3,2] = [_lconfig1, _lconfig2, _lconfig3]
        maintable = MainTableAutoFill(main_gui= main_gui)
        _maintable_big_table_data = maintable.big_table_data
        _maintable_big_table_data_3rd_column = _maintable_big_table_data[0:3,2]
        _first_data_set = _maintable_big_table_data_3rd_column[1].data_sets
        self.assertEqual(_first_data_set, '456')
        
    def test_check_input_parameters_case12(self):
        ''' Step2 - Make sure that if data have been loaded, the 3rd column of bigTable is not empty
        and they have runs defined '''
        main_gui = MagicMock()
        main_gui.bigTableData = empty((20,3), dtype=object)
        _lconfig1 = LConfigDataset()
        _lconfig1.data_sets = '123'
        _lconfig2 = LConfigDataset()
        _lconfig2.data_sets = '456'
        _lconfig3 = LConfigDataset()
        _lconfig3.data_sets = '789'
        main_gui.bigTableData[0:3,2] = [_lconfig1, _lconfig2, _lconfig3]
        maintable = MainTableAutoFill(main_gui= main_gui)
        _maintable_big_table_data = maintable.big_table_data
        _maintable_big_table_data_3rd_column = _maintable_big_table_data[0:3,2]
        _first_data_set = _maintable_big_table_data_3rd_column[1].data_sets
        self.assertNotEqual(_first_data_set, '123')
    
if __name__ == '__main__':
    unittest.main()