import mantid.simpleapi as mantid

class CalculateSF(object):
    '''
    This class will determine the best scaling factor (SF) to apply to the data to stitch them
    '''

    bigTableData = []

    def __init__(self, bigTableData, main_gui):
        self.bigTableData = bigTableData

        if bigTableData is not None:
            #Take the first data set as the LHS
            lhs_workspace = self._createWorkspace("_stitch_lhs", self.bigTableData[0,0])
            self.bigTableData[0,0].sf_auto = 1.0

            #For all the remaining data sets, stitch them into our LHS in order.
            #The result of the stitching is discarded, but we record the scalefactor calculated by Stitch1D
            for i in range(1,main_gui.ui.reductionTable.rowCount()):
                rhs_workspace = self._createWorkspace("_stitch_rhs", self.bigTableData[i, 0])
                lhs_workspace, sf = mantid.Stitch1D(lhs_workspace, rhs_workspace, OutputWorkspace="_stitch_lhs")
                self.bigTableData[i,0].sf_auto = sf

    def getAutoScaledData(self):
        return self.bigTableData

    def _createWorkspace(self, name, dataSet):
        pointData = mantid.CreateWorkspace(DataX = dataSet.reduce_q_axis.flatten(),
                                           DataY = dataSet.reduce_y_axis.flatten(),
                                           DataE = dataSet.reduce_e_axis.flatten(),
                                           NSpec = 1,
                                           OutputWorkspace = name)
        return mantid.ConvertToHistogram(pointData, OutputWorkspace = name)
