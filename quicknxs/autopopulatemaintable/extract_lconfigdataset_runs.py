class ExtractLConfigDataSetRuns(object):
    ''' This class get an array of LConfigDataSet and extract the data sets
    and append them in a list that is returned
    '''
    
    def __init__(self, lconfigdataset = None):
        self.lconfigdataset = lconfigdataset
    
    def list_runs(self):
        _data_set = self.lconfigdataset
        _list_runs = []
        for _lconfig in _data_set:
            if _lconfig is not None:
                _run = _lconfig.data_sets
                _list_runs.append(_run)         
        
        return _list_runs