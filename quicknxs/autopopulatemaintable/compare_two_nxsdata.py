#pylint: disable=w0231
class MyError(Exception):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

#pylint: disable=w0702
class CompareTwoNXSData(object):
    '''
    will return -1, 0 or 1 according to the position of the nexusToPosition in relation to the
    nexusToCompareWith based on the following criteria
    '''
    nexus_to_compare_with_run = None
    nexus_to_position_run = None
    result_comparison = 0

    def __init__(self,
                 nxsdata_to_compare_with=None,
                 nxsdata_to_position=None,
                 criteria1=None,
                 criteria2=None):

        if (nxsdata_to_compare_with is None) or \
           (nxsdata_to_position is None) or \
           (criteria1 is None) or \
           (criteria2 is None):
            raise MyError("Missing arguments")

        self.nexus_to_compare_with_run = nxsdata_to_compare_with.active_data.nxs.getRun()
        self.nexus_to_position_run = nxsdata_to_position.active_data.nxs.getRun()

        compare1 = self.compare_parameter(criteria1[0], criteria1[1])
        if compare1 != 0:
            self.result_comparison = compare1
            return

        compare2 = self.compare_parameter(criteria2[0], criteria2[1])
        if compare2 != 0:
            self.result_comparison = compare2
            return

    def compare_parameter(self, param, order, param_backup=None):
        _nexus_to_compare_with_run = self.nexus_to_compare_with_run
        _nexus_to_position_run = self.nexus_to_position_run

        try:
            _param_nexus_to_compare_with = float(_nexus_to_compare_with_run.getProperty(param).value[0])
            _param_nexus_to_position = float(_nexus_to_position_run.getProperty(param).value[0])
        except:
            _param_nexus_to_compare_with = float(_nexus_to_compare_with_run.getProperty(param_backup).value[0])
            _param_nexus_to_position = float(_nexus_to_position_run.getProperty(param_backup).value[0])

        self.param_nexus_to_compare_with = _param_nexus_to_compare_with
        self.param_nexus_to_position = _param_nexus_to_position

        if order == 'ascending':
            result_less_than = -1
            result_more_than = 1
        else:
            result_less_than = 1
            result_more_than = -1

        if _param_nexus_to_position < _param_nexus_to_compare_with:
            return result_less_than
        elif _param_nexus_to_position > _param_nexus_to_compare_with:
            return result_more_than
        else:
            return 0

    def result(self):
        return self.result_comparison
    