from PyQt4 import QtCore
import time

class AThread(QtCore.QThread):

    def setup(self, parent, run_number):   
        self.run_number = run_number
        self.parent = parent
    
    def run(self):
        print("I'm looking for this run number %d" %self.run_number)
        self.parent.runs_loaded += 1
            
    def stop(self):
        pass
        
    def pause(self):
        pass
        