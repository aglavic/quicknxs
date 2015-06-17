import unittest
from numpy import empty
import sys
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from quicknxs.run_sequence_breaker import RunSequenceBreaker

class TestRunSequenceBreaker(unittest.TestCase):
    
    def setUp(self):
        ''''setup variables used by tests '''
        pass

    def test_easy_sequence_list(self):
        ''' Assert easy sequence "1,2,3,4,5,6" list '''
        run_sequence = "1,2,3,4,5,6"
        _run_sequence = RunSequenceBreaker(run_sequence)
        expected_final_list = _run_sequence.final_list
        self.assertEqual([1,2,3,4,5,6], expected_final_list)
   
    def test_easy_sequence_string(self):
        ''' Assert easy sequence "1,2,3,4,5,6" string list '''
        run_sequence = "1,2,3,4,5,6"
        _run_sequence = RunSequenceBreaker(run_sequence)
        expected_final_list = _run_sequence.str_final_list
        self.assertEqual(['1','2','3','4','5','6'], expected_final_list)
    
    def test_hard_sequence_list(self):
        ''' Assert hard sequence "1,2,5-8,10" list '''
        run_sequence = "1,2,5-8,10"
        _run_sequence = RunSequenceBreaker(run_sequence)
        expected_final_list = _run_sequence.final_list
        self.assertEqual([1,2,5,6,7,8,10], expected_final_list)
   
    def test_hard_sequence_string(self):
        ''' Assert hard sequence "1,2,5-8,10" string list '''
        run_sequence = "1,2,5-8,10"
        _run_sequence = RunSequenceBreaker(run_sequence)
        expected_final_list = _run_sequence.str_final_list
        self.assertEqual(['1','2','5','6','7','8','10'], expected_final_list)
        
    def test_hard2_sequence_list(self):
        ''' Assert typo sequence "1,2,5-8,10," list '''
        run_sequence = "1,2,5-8,10,"
        _run_sequence = RunSequenceBreaker(run_sequence)
        expected_final_list = _run_sequence.final_list
        self.assertEqual([-2], expected_final_list)
   
    def test_hard2_sequence_string(self):
        ''' Assert type sequence "1,2,5-8,10," string list '''
        run_sequence = "1,2,5-8,10,"
        _run_sequence = RunSequenceBreaker(run_sequence)
        expected_final_list = _run_sequence.str_final_list
        self.assertEqual([''], expected_final_list)

    def test_empty_sequence_list(self):
        ''' Assert empty sequence gives final_list None '''
        run_sequence = None
        _run_sequence = RunSequenceBreaker(run_sequence)
        self.assertEqual(None, _run_sequence.final_list)

    def test_empty_sequence_string(self):
        ''' Assert empty sequence gives str_final_list None '''
        run_sequence = None
        _run_sequence = RunSequenceBreaker(run_sequence)
        self.assertEqual(None, _run_sequence.str_final_list)

    def test_no_sequence_list(self):
        ''' Assert no sequence gives final_list None '''
        _run_sequence = RunSequenceBreaker()
        self.assertEqual(None, _run_sequence.final_list)

    def test_no_sequence_string(self):
        ''' Assert no sequence gives str_final_list None '''
        _run_sequence = RunSequenceBreaker()
        self.assertEqual(None, _run_sequence.str_final_list)

    def test_crazy_input_list(self):
        ''' Assert crazy input list from user is [-2] '''
        run_sequence = '1,2,3,abc,4'
        _run_sequence = RunSequenceBreaker(run_sequence)
        self.assertEqual([-2], _run_sequence.final_list)

    def test_crazy_input_string(self):
        ''' Assert crazy input list from user is [''] '''
        run_sequence = '1,2,3,abc,4'
        _run_sequence = RunSequenceBreaker(run_sequence)
        self.assertEqual([''], _run_sequence.str_final_list)
        
    def test_empty_list(self):
        ''' Assert empty string gives empty result'''
        run_sequence = '    '
        _run_sequence = RunSequenceBreaker(run_sequence)
        self.assertEqual([-1], _run_sequence.final_list)

    def test_empty_string(self):
        ''' Assert empty string gives empty string result'''
        run_sequence = '    '
        _run_sequence = RunSequenceBreaker(run_sequence)
        self.assertEqual([''], _run_sequence.str_final_list)


if __name__ == '__main__':
    unittest.main()