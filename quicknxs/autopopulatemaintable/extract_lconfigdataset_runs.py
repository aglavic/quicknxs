class ExtractLConfigDataSetRuns(object):
    ''' This class get an array of LConfigDataSet and extract the data sets
    and append them in a list that is returned
    '''
    
    def __init__(self, lconfigdataset = None):
        self.lconfigdataset = lconfigdataset
    
    def list_runs(self):
        _data_set = self.lconfigdataset
        list_runs = []
        i=0
        
        for _lconfig in _data_set:
            if _lconfig is not None:
                _run = _lconfig.data_sets
                if _run is not '':
                    int_run = int(_run)
                    list_runs.append(int_run)
                
        return list_runs