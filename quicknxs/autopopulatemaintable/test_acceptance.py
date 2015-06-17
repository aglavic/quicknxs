''' Integration test for the peakfinderderivation algorithm '''

# -*- coding: utf-8 -*-
from lettuce import *
from nose.tools import assert_equals
import os
import sys
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from autopopulatemaintable.maintableautofill import MainTableAutoFill


# -*- coding: utf-8 -*-
from lettuce import step

@step(u'Given the sequence of runs "([^"]*)"')
def given_the_sequence_of_runs_group1(step, group1):
    assert False, 'This step must be implemented'
@step(u'Then the sorted list of files will be "([^"]*)"')
def then_the_sorted_list_of_files_will_be_group1(step, group1):
    assert False, 'This step must be implemented'

    