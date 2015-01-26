from mantid.simpleapi import *
from glob import glob
import os

def findNeXusFullPath(run_number):
    full_file_name = FileFinder.findRuns("REF_L_%d" % int(run_number))[0]
    return full_file_name