'''
Just a small test creation script setting up the python environment and running
all collected tests from the tests directory.
'''

import sys
import os
import unittest

# make sure this path is used on imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tests import test_suites

suite=unittest.TestSuite(test_suites.values())

# for pydev test runner
def load_tests(loader, tests, pattern):
  return suite

if __name__=="__main__":
  if len(sys.argv)>1:
    # run a selection of tests
    suite=unittest.TestSuite([test_suites[item+'_test'] for item in sys.argv[1:]])
  unittest.TextTestRunner(verbosity=2).run(suite)
