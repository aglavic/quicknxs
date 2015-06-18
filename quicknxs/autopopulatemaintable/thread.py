from PyQt4 import QtCore

class AThread(QtCore.QThread):

    def __init__(self, run_number):
        super(AThread, self).__init__()
        self.run_number = run_number
        pass
    
    def run(self):
        print("I'm looking for this run number %d" %run_number)
            
    def stop(self):
        pass
        
    def pause(self):
        pass
        