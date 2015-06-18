import sys
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from quicknxs.run_sequence_breaker import RunSequenceBreaker
from quicknxs.autopopulatemaintable.extract_lconfigdataset_runs import ExtractLConfigDataSetRuns
from thread import AThread

class MainTableAutoFill(object):

    def __init__(self, main_gui = None, list_of_run_from_input = '', data_type_selected = 'data', reset_table = True):
        if data_type_selected != 'data':
            self.data_type_selected = 'norm'
        else:
            self.data_type_selected = 'data'
        if list_of_run_from_input == '':
            self.sorted_list_of_runs = []
            return
            
        self.raw_run_from_input = list_of_run_from_input
        self.list_of_run_from_input = None
        self.main_gui = main_gui
        self.list_of_run_from_lconfig = None
        self.full_list_of_runs = None

        self.calculate_discrete_list_of_runs() # step1 -> list_new_runs
        
        self.big_table_data = None
        if not reset_table:
            self.retrieve_bigtable_list_data_loaded() # step2 -> list_old_runs
        
        _full_list_of_runs = []
        if self.list_of_run_from_input is not None:
            for _run in self.list_of_run_from_input:
                _full_list_of_runs.append(int(_run))
        if self.list_of_run_from_lconfig is not None:
            for _run in self.list_of_run_from_lconfig:      
                _full_list_of_runs.append(int(_run))
        self.full_list_of_runs = _full_list_of_runs
        
    def loading_all_runs(self):
        _list_of_runs = self.full_list_of_runs
        for _run in _list_of_runs:
            thread = AThread(_run)
            thread.start()
            
        
    def calculate_discrete_list_of_runs(self):
        _raw_run_from_input = self.raw_run_from_input
        sequence_breaker = RunSequenceBreaker(_raw_run_from_input)
        self.list_of_run_from_input = sequence_breaker.final_list

    def retrieve_bigtable_list_data_loaded(self):
        main_gui = self.main_gui
        if main_gui is None:
            return
        _big_table_data = main_gui.bigTableData
        self.big_table_data = _big_table_data
        _extract_runs = ExtractLConfigDataSetRuns(_big_table_data[:,2])
        self.list_of_run_from_lconfig = _extract_runs.list_runs()

if __name__ == "__main__":
    maintable = MainTableAutoFill('1,2,3,5-10,15,16', reset_table=True)
    print mantable.discrete_list_of_runs
    
    