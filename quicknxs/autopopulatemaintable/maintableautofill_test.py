import unittest
from numpy import empty
if __package__ == None:
    import sys
    from os import path
    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from maintableautofill import MainTableAutoFill
from mock import MagicMock
from lconfigdataset import LConfigDataset


class LConfigDataset(object):
    '''
    This class will be used when loading an XML configuration file and will
    keep record of all the information loaded, such as peak, back, TOF range...
    until the data/norm file has been loaded
    '''
    proton_charge = -1

    data_sets = ''
    data_full_file_name = ''
    data_peak = ['0','0']
    data_back = ['0','0']
    data_low_res = ['50','200']
    data_back_flag = True
    data_low_res_flag = True
    data_lambda_requested = -1

    tof_range = ['0','0'] 
    tof_units = 'ms'
    tof_auto_flag = True

    norm_sets = ''
    norm_full_file_name = ''
    norm_flag = True
    norm_peak = ['0','0']
    norm_back = ['0','0']
    norm_back_flag = True
    norm_low_res = ['50','200']
    norm_low_res_flag = True
    norm_lambda_requested = -1

    q_range =['0','0']
    lambda_range = ['0','0']

    reduce_q_axis = []
    reduce_y_axis = []
    reduce_e_axis = []
    sf_auto = 1 # auto scaling calculated by program
    sf_auto_found_match = False 
    sf_manual = 1 # manual scaling defined by user
    sf = 1 #scaling factor apply to data (will be either the auto, manual or 1)

    q_axis_for_display = []
    y_axis_for_display = []
    e_axis_for_display = []

    # use in the auto SF class
    tmp_y_axis = []
    tmp_e_axis = []

class TestMainTableAutoFill(unittest.TestCase):
    
    def setUp(self):
        ''''setup variables used by tests '''
        pass

    ## step0 ##
    def test_nullRawList(self):
        ''' Step0 - raw list is None '''
        maintable = MainTableAutoFill()
        sorted_list_runs = maintable.sorted_list_of_runs
        self.assertEqual(sorted_list_runs, [])

    def test_emptyRawList(self):
        ''' Step0 - input raw list of runs is empty'''
        maintable = MainTableAutoFill(raw_list_of_runs='')
        sorted_list_runs = maintable.sorted_list_of_runs
        self.assertEqual(sorted_list_runs, [])

    def test_makeSureRawListCorrectlyGiven_case1(self):
        ''' Step0 - raw list of runs correctly given '''
        maintable = MainTableAutoFill(raw_list_of_runs='1,2,3,4,5')
        raw_list_runs = maintable.raw_list_of_runs
        self.assertEqual(raw_list_runs, '1,2,3,4,5')

    def test_makeSureRawListCorrectlyGiven_case2(self):
        ''' Step0 - raw list of runs correctly given '''
        maintable = MainTableAutoFill(raw_list_of_runs='1,2,4-10,15,16')
        raw_list_runs = maintable.raw_list_of_runs
        self.assertEqual(raw_list_runs, '1,2,4-10,15,16')

    def test_makeSureDataTypeSelectedIsRight_data(self):
        ''' Step0 - checkt that passing nothing will use data as data type'''
        maintable = MainTableAutoFill()
        data_type = maintable.data_type_selected
        self.assertEqual(data_type, 'data')

    def test_makeSureDataTypeSelectedIsRight_norm(self):
        ''' Step0 - check that passing norm will use it as data type'''
        maintable = MainTableAutoFill(data_type_selected='norm')
        data_type = maintable.data_type_selected
        self.assertEqual(data_type, 'norm')

    ## step1 ##
    def test_discreteListOfFiles_Case1(self):
        ''' Step1 - check discrete list of files - [1,2,3,4,5]'''
        maintable = MainTableAutoFill(raw_list_of_runs='1,2,3,4,5')
        data_list = maintable.discrete_list_of_runs
        self.assertEqual(data_list, [1,2,3,4,5])
        
    def test_discreteListOfFiles_Case2(self):
        ''' Step1 - check discrete list of files - [1,2,3,5-10,15,16]'''
        maintable = MainTableAutoFill(raw_list_of_runs='1,2,3,5-10,15,16')
        data_list = maintable.discrete_list_of_runs
        self.assertEqual(data_list, [1,2,3,5,6,7,8,9,10,15,16])

    def test_discreteListOfFiles_Case3(self):
        ''' Step1 - check discrete list of files - [1,5-10,15,16,20-22]'''
        maintable = MainTableAutoFill(raw_list_of_runs='1,5-10,15,16,20-22')
        data_list = maintable.discrete_list_of_runs
        self.assertEqual(data_list, [1,5,6,7,8,9,10,15,16,20,21,22])

    ## step2 ##
    def test_mainGuiEmpty(self):
        ''' Step2 - check that there are no pre-loaded data in BigTableData (3rd column)'''
        main_gui = None
        maintable = MainTableAutoFill(main_gui = main_gui)
        program_main_gui = maintable.main_gui
        self.assertEqual(main_gui, program_main_gui)

    def test_mainGuiBigTableDataEmptyPassed(self):
        ''' Step2 - check that there are no pre-loaded data in BigTableData (3rd column)'''
        main_gui = MagicMock()
        main_gui.BigTableData = empty((20,3), dtype=object)
        maintable = MainTableAutoFill(main_gui= main_gui)
        program_main_gui = maintable.main_gui
        self.assertEqual(main_gui, program_main_gui)
    
    def test_mainGuiBigTableDataNoEmpty3rdColumn(self):
        ''' Ste2 - Make sure that if data have been loaded, the 3rd column of bigTable is not empty'''
        main_gui = MagicMock()
        main_gui.bigTableData = empty((20,3), dtype=object)
        main_gui.bigTableData[0:5,2] = LConfigDataset()
        maintable = MainTableAutoFill(main_gui= main_gui)
        _maintable_big_table_data = maintable.big_table_data
        _maintable_big_table_data_3rd_column = _maintable_big_table_data[0,2]
        self.assertIsInstance(_maintable_big_table_data_3rd_column, LConfigDataset)
        
    def test_mainGuiBigTableDataNoEmpty3rdColumnWithRunSpecified_rightCase1(self): 
        ''' Ste2 - Make sure that if data have been loaded, the 3rd column of bigTable is not empty
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
        self.assertEqual(_first_data_set,'123')
        
    def test_mainGuiBigTableDataNoEmpty3rdColumnWithRunSpecified_wrongCase1(self): 
        ''' Ste2 - Make sure that if data have been loaded, the 3rd column of bigTable is not empty
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
        self.assertNotEqual(_first_data_set,'222')
    
    def test_mainGuiBigTableDataNoEmpty3rdColumnWithRunSpecified_rightCase2(self): 
        ''' Ste2 - Make sure that if data have been loaded, the 3rd column of bigTable is not empty
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
        self.assertEqual(_first_data_set,'456')
        
    def test_mainGuiBigTableDataNoEmpty3rdColumnWithRunSpecified_wrongCase2(self): 
        ''' Ste2 - Make sure that if data have been loaded, the 3rd column of bigTable is not empty
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
        self.assertNotEqual(_first_data_set,'123')
    
        
    
    
if __name__ == '__main__':
    unittest.main()