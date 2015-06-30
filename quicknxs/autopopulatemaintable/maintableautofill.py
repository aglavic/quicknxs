import sys
import time
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from quicknxs.run_sequence_breaker import RunSequenceBreaker
from quicknxs.autopopulatemaintable.extract_lconfigdataset_runs import ExtractLConfigDataSetRuns
from quicknxs.autopopulatemaintable.thread import LocateRunThread, LoadRunThread
from quicknxs.autopopulatemaintable.sort_nexus_list import SortNexusList

class MainTableAutoFill(object):

    list_full_file_name = []
    list_nxs = []

    def __init__(self, main_gui=None, list_of_run_from_input='',
                 data_type_selected='data', reset_table=True):

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
        self.list_nx_sorted = None

        self.runs_found = 0
        self.runs_loaded = 0

        self.number_of_runs = None
        self.filename_thread_array = None
        self.number_of_runs = None
        self.list_nxs_sorted = None
        self.loaded_thread_array = None

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

    def run(self):
        self.locate_runs()
        self.loading_runs()
        self.sorting_runs()

    def locate_runs(self):
        _list_of_runs = self.full_list_of_runs
        self.number_of_runs = len(_list_of_runs)
        self.runs_found = 0
        self.init_filename_thread_array(len(_list_of_runs))
        for index, _run in enumerate(_list_of_runs):
            _thread = self.filename_thread_array[index]
            _thread.setup(self, _run, index)
            _thread.start()

        while self.runs_found < self.number_of_runs:
            time.sleep(0.5)

    def loading_runs(self):
        _list_full_file_name = self.list_full_file_name
        if len(_list_full_file_name) < 2:
            return

        self.runs_loaded = 0
        self.number_of_runs = len(_list_full_file_name)
        self.init_loaded_thread_array(len(_list_full_file_name))
        for index, _file_name in enumerate(_list_full_file_name):
            _thread = self.loaded_thread_array[index]
            _thread.setup(self, _file_name, index)
            _thread.start()

        while self.runs_loaded < self.number_of_runs:
            time.sleep(0.5)

    def sorting_runs(self):
        _list_full_file_name = self.list_full_file_name
        if len(_list_full_file_name) < 2:
            self.list_nxs_sorted = self.list_nxs

        else:
            sort_list = SortNexusList(parent=self.main_gui,
                                     list_nxs=self.list_nxs,
                                     criteria1=['lambda_requested', 'decrease'],
                                     criteria2=['theta', 'increase'])
            _list_nxs_sorted = sort_list.list_nxs_sorted
            self.list_nxs_sorted = _list_nxs_sorted

    def init_filename_thread_array(self, sz):
        _filename_thread_array = []
        _list_full_file_name = []
        for i in range(sz):
            _filename_thread_array.append(LocateRunThread())
            _list_full_file_name.append('')
        self.filename_thread_array = _filename_thread_array
        self.list_full_file_name = _list_full_file_name

    def init_loaded_thread_array(self, sz):
        _loaded_thread_array = []
        _list_nxs = []
        for i in range(sz):
            _loaded_thread_array.append(LoadRunThread())
            _list_nxs.append(None)
        self.loaded_thread_array = _loaded_thread_array
        self.list_nxs = _list_nxs

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
        _extract_runs = ExtractLConfigDataSetRuns(_big_table_data[:, 2])
        self.list_of_run_from_lconfig = _extract_runs.list_runs()

if __name__ == "__main__":
    maintable = MainTableAutoFill('1, 2, 3, 5-10, 15, 16', reset_table=True)

