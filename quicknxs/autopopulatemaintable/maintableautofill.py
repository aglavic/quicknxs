from runsequencebreaker import RunSequenceBreaker

class MainTableAutoFill(object):

    raw_list_of_runs = ''
    data_type_selected = 'data' # 'data' or 'norm'
    
    discrete_list_of_runs = [''] # step1
    sorted_list_of_runs = []
    
    big_table_data = None
    
    def __init__(cls, main_gui = None, raw_list_of_runs = '', data_type_selected = 'data'):
        if data_type_selected != 'data':
            cls.data_type_selected = 'norm'
        if raw_list_of_runs == '':
            cls.sorted_list_of_runs = []
        cls.raw_list_of_runs = raw_list_of_runs
        cls.main_gui = main_gui

        cls.calculateDiscreteListOfRuns() # step1
        cls.retrieveBigTableListDataLoaded() # step2
        

    def calculateDiscreteListOfRuns(cls):
        _raw_list_of_runs = cls.raw_list_of_runs
        sequence_breaker = RunSequenceBreaker(_raw_list_of_runs)
        cls.discrete_list_of_runs = sequence_breaker.getFinalList()

    def retrieveBigTableListDataLoaded(cls):
        main_gui = cls.main_gui
        if main_gui is None:
            return
        cls.big_table_data = main_gui.bigTableData
        

if __name__ == "__main__":
    maintable = MainTableAutoFill('1,2,3,5-10,15,16')
    print maintable.getDiscreteListOfRuns()
    