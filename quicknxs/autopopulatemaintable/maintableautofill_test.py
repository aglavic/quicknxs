import unittest
from numpy import empty
from maintableautofill import MainTableAutoFill
from mock import MagicMock
#from quicknxs.qreduce import LConfigDataset

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
        pass
        #main_gui = MagicMock()
        #main_gui.BigTableData = empty((20,3), dtype=object)
        #main_gui.BigTableData[0:5,3] = LConfigDataset()
    
    
    
if __name__ == '__main__':
    unittest.main()