from runsequencebreaker import RunSequenceBreaker

class MainTableAutoFill(object):

    def __init__(cls, main_gui = None, raw_list_of_runs = '', data_type_selected = 'data', reset_table = False):
        if data_type_selected != 'data':
            cls.data_type_selected = 'norm'
        else:
            cls.data_type_selected = 'data'
        if raw_list_of_runs == '':
            cls.sorted_list_of_runs = []
        cls.raw_list_of_runs = raw_list_of_runs
        cls.main_gui = main_gui

        cls.discrete_list_of_runs = ['']
        cls.calculate_discrete_list_of_runs() # step1

        cls.big_table_data = None
        if not reset_table:
            cls.retrieve_bigtable_list_data_loaded() # step2

        

    def calculate_discrete_list_of_runs(cls):
        _raw_list_of_runs = cls.raw_list_of_runs
        sequence_breaker = RunSequenceBreaker(_raw_list_of_runs)
        cls.discrete_list_of_runs = sequence_breaker.getFinalList()

    def retrieve_bigtable_list_data_loaded(cls):
        main_gui = cls.main_gui
        if main_gui is None:
            return
        cls.big_table_data = main_gui.bigTableData

if __name__ == "__main__":
    maintable = MainTableAutoFill('1,2,3,5-10,15,16', reset_table=True)
    
    