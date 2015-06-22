from PyQt4 import QtCore
import time
import mantid
import sys
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
import nexus_utilities
import qreduce


class LocateRunThread(QtCore.QThread):

    def setup(self, parent, run_number, index):   
        self.parent = parent
        self.run_number = run_number
        self.index = index
    
    def run(self):
        full_file_name = nexus_utilities.findNeXusFullPath(self.run_number)
        self.parent.list_full_file_name[self.index] = full_file_name
        self.parent.runs_found += 1
            
    def stop(self):
        pass
        
    def pause(self):
        pass
        

class LoadRunThread(QtCore.QThread):
    
    def setup(self, parent, file_name, index):
        self.parent = parent
        self.file_name = file_name
        self.index = index
        
    def run(self):
        nxs = qreduce.NXSData(self.file_name, metadata_only=True)
        self.parent.list_nxs[self.index] = nxs
        self.parent.runs_loaded += 1
        print 'here'