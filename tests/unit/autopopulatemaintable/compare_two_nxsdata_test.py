import unittest
import sys
from os import path
from mock import MagicMock
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from quicknxs.autopopulatemaintable.compare_two_nxsdata import CompareTwoNXSData, MyError


class TestCompareTwoNXSData(unittest.TestCase):

    def setUp(self):
        ''''setup variables used by tests '''
        self.nxsdata_to_compare_with = MagicMock()
        self.nxsdata_to_position = MagicMock()
        self.criteria1 = ['arg1', 'ascending']
        self.criteria2 = ['arg2', 'descending']

    def test_missing_4_arguments(self):
        ''' Assert error is raised when all arguments are missing '''
        self.assertRaises(MyError, CompareTwoNXSData)

    def test_missing_3_arguments(self):
        ''' Assert error is raised when 3 arguments are missing '''
        _nxsdata_to_compare_with = self.nxsdata_to_compare_with
        self.assertRaises(MyError, CompareTwoNXSData,
                          nxsdata_to_compare_with=_nxsdata_to_compare_with)
        self.assertRaises(MyError, CompareTwoNXSData,
                          nxsdata_to_position=self.nxsdata_to_position)
        self.assertRaises(MyError, CompareTwoNXSData,
                          criteria1=self.criteria1)
        self.assertRaises(MyError, CompareTwoNXSData,
                          criteria2=self.criteria2)

    def test_missing_2_arguments(self):
        ''' Assert error is raised when 2 arguments are missing '''
        self.assertRaises(MyError, CompareTwoNXSData,
                          nxsdata_to_compare_with=self.nxsdata_to_compare_with,
                          nxsdata_to_position=self.nxsdata_to_position)
        self.assertRaises(MyError, CompareTwoNXSData,
                          nxsdata_to_compare_with=self.nxsdata_to_compare_with,
                          criteria1=self.criteria1)
        self.assertRaises(MyError, CompareTwoNXSData,
                          nxsdata_to_compare_with=self.nxsdata_to_compare_with,
                          criteria2=self.criteria2)
        self.assertRaises(MyError, CompareTwoNXSData,
                          nxsdata_to_position=self.nxsdata_to_position,
                          criteria1=self.criteria1)
        self.assertRaises(MyError, CompareTwoNXSData,
                          nxsdata_to_position=self.nxsdata_to_position,
                          criteria2=self.criteria2)
        self.assertRaises(MyError, CompareTwoNXSData,
                          criteria1=self.criteria1,
                          criteria2=self.criteria2)

    def test_missing_1_argument(self):
        ''' Assert error is raised when 1 argument is missing '''
        self.assertRaises(MyError, CompareTwoNXSData,
                          nxsdata_to_compare_with=self.nxsdata_to_compare_with,
                          nxsdata_to_position=self.nxsdata_to_position,
                          criteria1=self.criteria1)
        self.assertRaises(MyError, CompareTwoNXSData,
                          nxsdata_to_position=self.nxsdata_to_position,
                          criteria1=self.criteria1,
                          criteria2=self.criteria2)
        self.assertRaises(MyError, CompareTwoNXSData,
                          nxsdata_to_compare_with=self.nxsdata_to_compare_with,
                          criteria1=self.criteria1,
                          criteria2=self.criteria2)
        self.assertRaises(MyError, CompareTwoNXSData,
                          nxsdata_to_compare_with=self.nxsdata_to_compare_with,
                          nxsdata_to_position=self.nxsdata_to_position,
                          criteria2=self.criteria2)

    def test_getRun_to_compare_with(self):
        ''' Assert getRun() of nexus_to_compare_with_run is correctly
        retrieved from active_data.nxs object
        '''
        nxsdata_to_compare_with = MagicMock()
        mock2 = MagicMock()
        mock2.getProperty.value = MagicMock(return_value='arg1')
        nxsdata_to_compare_with.active_data.nxs.getRun = MagicMock(return_value=mock2)
        nxsdata_to_position = MagicMock()
        cmp_two_nxs = CompareTwoNXSData(nxsdata_to_compare_with=nxsdata_to_compare_with,
                                        nxsdata_to_position=nxsdata_to_position,
                                        criteria1=self.criteria1,
                                        criteria2=self.criteria2)
        self.assertEqual(mock2, cmp_two_nxs.nexus_to_compare_with_run)

    def test_getRun_to_position(self):
        ''' Assert getRun() of nexus_to_position_run is correctly
        retrieved from active_data.nxs object
        '''
        nxsdata_to_position = MagicMock()
        mock2 = MagicMock()
        mock2.getProperty.value = MagicMock(return_value='arg1')
        nxsdata_to_position.active_data.nxs.getRun = MagicMock(return_value=mock2)
        nxsdata_to_compare_with = MagicMock()
        cmp_two_nxs = CompareTwoNXSData(nxsdata_to_compare_with=nxsdata_to_compare_with,
                                        nxsdata_to_position=nxsdata_to_position,
                                        criteria1=self.criteria1,
                                        criteria2=self.criteria2)
        self.assertEqual(mock2, cmp_two_nxs.nexus_to_position_run)

    def test_getValue_to_compare_with(self):
        ''' Assert retrieve value of getRun object for nexusToCompareWith'''
        mock1 = MagicMock()
        mock1.value = [10, 'units']

        mock_run_object = MagicMock()
        mock_run_object.getProperty = MagicMock(return_value=mock1)
        nxsdata_to_compare_with = MagicMock()
        nxsdata_to_compare_with.active_data.nxs.getRun = MagicMock(return_value=mock_run_object)
        cmp_nxs_data = CompareTwoNXSData(nxsdata_to_compare_with=nxsdata_to_compare_with,
                                         nxsdata_to_position=mock1,
                                         criteria1=self.criteria1,
                                         criteria2=self.criteria2)
        _param_nexus_to_compare = cmp_nxs_data.param_nexus_to_compare_with
        self.assertEqual(10, _param_nexus_to_compare)

    def test_getValue_to_position(self):
        ''' Assert retrieve value of getRun object for nexusToPosition '''
        mock1 = MagicMock()
        mock1.value = [10, 'units']

        mock_run_object = MagicMock()
        mock_run_object.getProperty = MagicMock(return_value=mock1)
        nxsdata_to_position = MagicMock()
        nxsdata_to_position.active_data.nxs.getRun = MagicMock(return_value=mock_run_object)
        cmp_nxs_data = CompareTwoNXSData(nxsdata_to_compare_with=mock1,
                                         nxsdata_to_position=nxsdata_to_position,
                                         criteria1=self.criteria1,
                                         criteria2=self.criteria2)
        _param_nexus_to_position = cmp_nxs_data.param_nexus_to_position
        self.assertEqual(10, _param_nexus_to_position)

    def test_result_ascending_order(self):
        mock1 = MagicMock()
        mock1.value = [10, 'units']
        mock1_run_object = MagicMock()
        mock1_run_object.getProperty = MagicMock(return_value=mock1)
        nxsdata_to_compare_with = MagicMock()
        nxsdata_to_compare_with.active_data.nxs.getRun = MagicMock(return_value=mock1_run_object)

        mock2 = MagicMock()
        mock2.value = [20, 'units']
        mock2_run_object = MagicMock()
        mock2_run_object.getProperty = MagicMock(return_value=mock2)
        nxsdata_to_position = MagicMock()
        nxsdata_to_position.active_data.nxs.getRun = MagicMock(return_value=mock2_run_object)

        criteria1 = ['arg1', 'ascending']
        criteria2 = ['arg2', 'ascending']

        cmp_nxs_data = CompareTwoNXSData(nxsdata_to_compare_with=nxsdata_to_compare_with,
                                         nxsdata_to_position=nxsdata_to_position,
                                         criteria1=criteria1,
                                         criteria2=criteria2)

        self.assertEqual(1, cmp_nxs_data.result())

    def test_result_descending_order(self):
        mock1 = MagicMock()
        mock1.value = [10, 'units']
        mock1_run_object = MagicMock()
        mock1_run_object.getProperty = MagicMock(return_value=mock1)
        nxsdata_to_compare_with = MagicMock()
        nxsdata_to_compare_with.active_data.nxs.getRun = MagicMock(return_value=mock1_run_object)

        mock2 = MagicMock()
        mock2.value = [20, 'units']
        mock2_run_object = MagicMock()
        mock2_run_object.getProperty = MagicMock(return_value=mock2)
        nxsdata_to_position = MagicMock()
        nxsdata_to_position.active_data.nxs.getRun = MagicMock(return_value=mock2_run_object)

        criteria1 = ['arg1', 'descending']
        criteria2 = ['arg2', 'descending']

        cmp_nxs_data = CompareTwoNXSData(nxsdata_to_compare_with=nxsdata_to_compare_with,
                                         nxsdata_to_position=nxsdata_to_position,
                                         criteria1=criteria1,
                                         criteria2=criteria2)

        self.assertEqual(-1, cmp_nxs_data.result())

    def test_result_ascending_order_with_same_value(self):
        mock1 = MagicMock()
        mock1.value = [20, 'units']
        mock1_run_object = MagicMock()
        mock1_run_object.getProperty = MagicMock(return_value=mock1)
        nxsdata_to_compare_with = MagicMock()
        nxsdata_to_compare_with.active_data.nxs.getRun = MagicMock(return_value=mock1_run_object)

        mock2 = MagicMock()
        mock2.value = [20, 'units']
        mock2_run_object = MagicMock()
        mock2_run_object.getProperty = MagicMock(return_value=mock2)
        nxsdata_to_position = MagicMock()
        nxsdata_to_position.active_data.nxs.getRun = MagicMock(return_value=mock2_run_object)

        criteria1 = ['arg1', 'descending']
        criteria2 = ['arg2', 'descending']

        cmp_nxs_data = CompareTwoNXSData(nxsdata_to_compare_with=nxsdata_to_compare_with,
                                         nxsdata_to_position=nxsdata_to_position,
                                         criteria1=criteria1,
                                         criteria2=criteria2)

        self.assertEqual(0, cmp_nxs_data.result())


if __name__ == '__main__':
    unittest.main()
    