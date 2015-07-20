from PyQt4 import QtCore
import time
from mantid.simpleapi import *
import mantid

class REFLReductionThread(QtCore.QThread):
    
    parent = None
    
    def setupReduction(cls, parent=None,
                       row= 0,
                       RunNumbers='',
                       NormalizationRunNumber='',
                       SignalPeakPixelRange='',
                       SubtractSignalBackground='', 
                       SignalBackgroundPixelRange='',
                       NormFlag='',
                       NormPeakPixelRange='',
                       NormBackgroundPixelRange='',
                       SubtractNormBackground='',
                       LowResDataAxisPixelRangeFlag='',
                       LowResDataAxisPixelRange='',
                       LowResNormAxisPixelRangeFlag='',
                       LowResNormAxisPixelRange='',
                       TOFRange='',
                       IncidentMediumSelected='',
                       GeometryCorrectionFlag='',
                       QMin='',
                       QStep='',
                       ScalingFactorFile='',
                       CropFirstAndLastPoints = '',
                       SlitsWidthFlag='',
                       OutputWorkspace=''):

	cls.parent = parent
	cls.row= row
	cls.RunNumbers=RunNumbers
	cls.NormalizationRunNumber=NormalizationRunNumber
	cls.SignalPeakPixelRange=SignalPeakPixelRange
	cls.SubtractSignalBackground=SubtractSignalBackground
	cls.SignalBackgroundPixelRange=SignalBackgroundPixelRange
	cls.NormFlag=NormFlag
	cls.NormPeakPixelRange=NormPeakPixelRange
	cls.NormBackgroundPixelRange=NormBackgroundPixelRange
	cls.SubtractNormBackground=SubtractNormBackground
	cls.LowResDataAxisPixelRangeFlag=LowResDataAxisPixelRangeFlag
	cls.LowResDataAxisPixelRange=LowResDataAxisPixelRange
	cls.LowResNormAxisPixelRangeFlag=LowResNormAxisPixelRangeFlag
	cls.LowResNormAxisPixelRange=LowResNormAxisPixelRange
	cls.TOFRange=TOFRange
	cls.IncidentMediumSelected=IncidentMediumSelected
	cls.GeometryCorrectionFlag=GeometryCorrectionFlag
	cls.QMin=QMin
	cls.QStep=QStep
	cls.ScalingFactorFile=ScalingFactorFile
	cls.CropFirstAndLastPoints = CropFirstAndLastPoints
	cls.SlitsWidthFlag=SlitsWidthFlag
	cls.OutputWorkspace=OutputWorkspace
        
    def run(cls):
	LiquidsReflectometryReduction(RunNumbers=cls.RunNumbers,
                              NormalizationRunNumber=cls.NormalizationRunNumber,
                              SignalPeakPixelRange=cls.SignalPeakPixelRange,
                              SubtractSignalBackground=cls.SubtractSignalBackground,
                              SignalBackgroundPixelRange=cls.SignalBackgroundPixelRange,
                              NormFlag=cls.NormFlag,
                              NormPeakPixelRange=cls.NormPeakPixelRange,
                              NormBackgroundPixelRange=cls.NormBackgroundPixelRange,
                              SubtractNormBackground=cls.SubtractNormBackground,
                              LowResDataAxisPixelRangeFlag=cls.LowResDataAxisPixelRangeFlag,
                              LowResDataAxisPixelRange=cls.LowResDataAxisPixelRange,
                              LowResNormAxisPixelRangeFlag=cls.LowResNormAxisPixelRangeFlag,
                              LowResNormAxisPixelRange=cls.LowResNormAxisPixelRange,
                              TOFRange=cls.TOFRange,
                              IncidentMediumSelected=cls.IncidentMediumSelected,
                              GeometryCorrectionFlag=cls.GeometryCorrectionFlag,
                              QMin=cls.QMin,
                              QStep=cls.QStep,
                              ScalingFactorFile=cls.ScalingFactorFile,
                              CropFirstAndLastPoints = cls.CropFirstAndLastPoints,
                              SlitsWidthFlag=cls.SlitsWidthFlag,
                              OutputWorkspace=cls.OutputWorkspace)
	
	configObject = cls.parent.bigTableData[cls.row, 2]
	configObject = cls.saveReducedData(configObject, outputWorkspace)
	cls.parent.bigTableData[cls.row,2] = configObject
	
	#AnalysisDataService.remove(outputWorkspace)
	
	cls.parent.reductionThreadDone()
	cls.parent.checkIfAllDone()
	
    def saveReducedData(cls, configObject, outputWorkspace):
	    configObject.proton_charge = float(mtd[outputWorkspace].getRun().getProperty('gd_prtn_chrg').value)
	    configObject.reduce_q_axis = mtd[outputWorkspace].readX(0)[:]
	    configObject.reduce_y_axis = mtd[outputWorkspace].readY(0)[:]
	    configObject.reduce_e_axis = mtd[outputWorkspace].readE(0)[:]
	    configObject.q_axis_for_display = mtd[outputWorkspace].readX(0)[:]
	    configObject.y_axis_for_display = mtd[outputWorkspace].readY(0)[:]
	    configObject.e_axis_for_display = mtd[outputWorkspace].readE(0)[:]
	    configObject.sf_auto_found_match = mtd[outputWorkspace].getRun().getProperty('isSFfound').value
	    
	    return configObject

