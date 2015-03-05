import mantid
from mantid.simpleapi import *
import logbook
import os, time
import nexus_utilities
from qreduce import NXSData

class ReductionObject(object):

	# data and norm run number (from GUI main table)
	dataCell = None
	normCell = None

	# data, norm and config from bigTableData Array
	oData = None
	oNorm = None
	oConfig = None

	# after integration over low res range
	data_y_axis = None
	data_y_error_axis = None
	norm_y_axis = None
	norm_y_error_axis = None

	# data and norm axis after background subtraction
	data_y_axis = []
	data_y_error_axis = []

	norm_y_axis = []
	norm_y_error_axis = []

	# normalized data (data / normalization file)
	normalized_data = []
	normalized_data_error = []

	# scaled data (after normalization)
	scaled_normalized_data = []
	scaled_normalized_data_error = []

	# after conversion of axis from TOF to Q
	scaled_normalized_data_reverse = []
	scaled_normalized_data_error_reverse = []
	q_axis = []

	q_workspace = None

	main_gui = None

	sf_auto_found_match = False

	final_q_axis = []
	final_y_axis = []
	final_e_axis = []

	def __init__(self, main_gui, dataCell, normCell, oData, oNorm, oConfig):
		'''
		Initialize the reduction object by 
		setting data and normalization files
		'''
		self.main_gui = main_gui

		self.dataCell = dataCell
		self.normCell = normCell

		self.oConfig = oConfig

		self.logbook('Initialize reduction objects (data and norm)')

		# if the oData is empty, retrieve info from oConfig
		if oData is None:
			self.logbook('-> data: oData is None => we need to retrieve it from config object')
			oData = self.populate_data_object(main_gui, oConfig, 'data')
		self.oData = oData

		# retrieve norm if user wants norm and if normCell is not empty
		if normCell != '':
			self.logbook('-> normCell is not empty: %s'% normCell)
			if oNorm is None:
				self.logbook('--> oNorm is None')
				# make sure the norm flag is on in the config file
				if oConfig.norm_flag:
					self.logbook('---> yes, we want to use normalization file')
					oNorm = self.populate_data_object(main_gui, oConfig, 'norm')
				else:
					self.logbook('---> no, we do not want to use normalization file')
			else: # make sure the flag is ON         
				self.logbook('--> oNorm exist')
				if not(oNorm.active_data.use_it_flag):
					self.logbook('---> no, we do not want to use normalization file')
					oNorm = None
				else:
					self.logbook('---> yes, we want to use normalization file')

		self.oNorm = oNorm

	def logbook(self, text, appendFlag=True):
		if appendFlag:
			self.main_gui.ui.logbook.append(text)
		else:
			self.main_gui.ui.logbook.undo()
			self.main_gui.ui.logbook.append(text)

	def populate_data_object(self, main_gui, oConfig, type):
		'''
		will retrieve all the info from the oConfig table and will populate the oData object
		type is either 'data' or 'norm'
		'''

		is_data = True

		# check first if we have a full file name already
		if oConfig is not None:
			if type == 'data':
				full_file_name = oConfig.data_full_file_name
				if full_file_name == u'' or full_file_name == [''] :
					_run_number = oConfig.data_sets
	#                    full_file_name = FileFinder.findRuns("REF_L%d" %int(_run_number))[0]
					full_file_name = nexus_utilities.findNeXusFullPath(int(_run_number))                    
			else:
				is_data = False
				if oConfig.norm_flag:
					full_file_name = oConfig.norm_full_file_name
					if full_file_name == u'' or full_file_name == ['']:
						_run_number = oConfig.norm_sets
	#                        full_file_name = FileFinder.findRuns("REF_L%d" %int(_run_number))[0]
						full_file_name = nexus_utilities.findNeXusFullPath(int(_run_number))                    

			event_split_bins = None
			event_split_index = 0
			bin_type = 0

			oData = NXSData(full_file_name,
			                bin_type = bin_type,
			                bins = main_gui.ui.eventTofBins.value(),
			                callback = None,
			                event_split_bins = event_split_bins,
			                event_split_index = event_split_index,
			                metadata_config_object = oConfig,
			                is_data = is_data)

			return oData

		return None    

class REFLReduction(object):
	'''
	This program will create the script to run the reduction
	'''

	main_gui = None
	script = []

	def logbook(cls, text):
		# add log book message
		cls.main_gui.ui.logbook.append(text)

	def __init__(cls, main_gui):
		'''
		Initialize the REFL reduction
		'''

		cls.main_gui = main_gui
		cls.logbook('Running data reduction ...')
		cls.logbook('')

		# retrive full data to reduce
		bigTableData = main_gui.bigTableData

		# number of reduction process to run
		nbrRow = main_gui.ui.reductionTable.rowCount()

		cls.removePreviousWorkspaces()
		start_time = time.time()

		#from reduction.command_interface import ReductionSingleton
		#ReductionSingleton.clean()

		incidentMediumSelected =  str(main_gui.ui.selectIncidentMediumList.currentText().strip())
		geometryCorrectionFlag = main_gui.ui.geometryCorrectionFlag.isChecked()
		qmin = 0.005
		qstep = float(main_gui.ui.qStep.text())
		scalingFactorFile = ''
		if main_gui.ui.scalingFactorFlag.isChecked():            
			scalingFactorFile = str(main_gui.ui.scalingFactorFile.text())
		slitsWidthFlag = main_gui.ui.scalingFactorSlitsWidthFlag.isChecked()        

		listWorkspaces = []

		for row in range(nbrRow):

			dataCell = main_gui.ui.reductionTable.item(row,0).text()
			if main_gui.ui.reductionTable.item(row,6) is not None:
				normCell = main_gui.ui.reductionTable.item(row,6).text()
			else:
				normCell = ''

			cls.logbook('Working with DATA: %s and NORM: %s' %(dataCell, normCell))

			dataObject = bigTableData[row,0]
#            normObject = bigTableData[row,1]
			configObject = bigTableData[row,2]

#            red1 = ReductionObject(main_gui, dataCell, normCell, dataObject, normObject, configObject)
#            bigTableData[row,0] = red1.oData
#            bigTableData[row,1] = red1.oNorm

			runNumbers = [int(configObject.data_sets)]
			normalizationRunNumbers = int(configObject.norm_sets)
			signalPeakPixelRange = [int(configObject.data_peak[0]), int(configObject.data_peak[1])]
			subtractSignalBackground = bool(configObject.data_back_flag)
			signalBackgroundPixelRange = [int(configObject.data_back[0]), int(configObject.data_back[1])]
			normFlag = bool(configObject.norm_flag)
			normPeakPixelRange = [int(configObject.norm_peak[0]), int(configObject.norm_peak[1])]
			normBackgroundPixelRange = [int(configObject.norm_back[0]), int(configObject.norm_back[1])]
			subtractNormBackground = bool(configObject.norm_back_flag)
			lowResDataAxisPixelRangeFlag = bool(configObject.data_low_res_flag)
			lowResDataAxisPixelRange = [int(configObject.data_low_res[0]), int(configObject.data_low_res[1])]
			lowResNormAxisPixelRangeFlag = bool(configObject.norm_low_res_flag)
			lowResNormAxisPixelRange = [int(configObject.norm_low_res[0]), int(configObject.data_low_res[1])]
			tofRange = [float(configObject.tof_range[0]), float(configObject.tof_range[-1])]
#            qmin = str(configObject.q_range[0])
			outputWorkspace = str("reflectivity_%s" % runNumbers)
			listWorkspaces.append(outputWorkspace)

			RefLReduction(RunNumbers=runNumbers,
			              NormalizationRunNumber=normalizationRunNumbers,
			              SignalPeakPixelRange=signalPeakPixelRange,
			              SubtractSignalBackground=subtractSignalBackground,
			              SignalBackgroundPixelRange=signalBackgroundPixelRange,
			              NormFlag=normFlag,
			              NormPeakPixelRange=normPeakPixelRange,
			              NormBackgroundPixelRange=normBackgroundPixelRange,
			              SubtractNormBackground=subtractNormBackground,
			              LowResDataAxisPixelRangeFlag=lowResDataAxisPixelRangeFlag,
			              LowResDataAxisPixelRange=lowResDataAxisPixelRange,
			              LowResNormAxisPixelRangeFlag=lowResNormAxisPixelRangeFlag,
			              LowResNormAxisPixelRange=lowResNormAxisPixelRange,
			              TOFRange=tofRange,
			              IncidentMediumSelected=incidentMediumSelected,
			              GeometryCorrectionFlag=geometryCorrectionFlag,
			              QMin=qmin,
			              QStep=qstep,
			              ScalingFactorFile=scalingFactorFile,
			              SlitsWidthFlag=slitsWidthFlag,
			              OutputWorkspace=outputWorkspace)

			# save data back into bigTableData
			configObject = cls.saveReducedData(configObject, outputWorkspace)
			bigTableData[row,2] = configObject

		cls.removeTempWorkspaces(listWorkspaces)

		### DEBUGGING
		##utilities.output_ascii_file('/mnt/hgfs/j35/Matlab/compareMantidquickNXS/data/quicknxs_after_final_cleaning.txt',
		##red1.final_q_axis,
		##red1.final_y_axis,
		##red1.final_e_axis)

		main_gui.bigTableData = bigTableData

		cls.logbook('')

		## put back the object created in the bigTable to speed up next preview / load
		#main_gui.bigTableData = bigTableData

		end_time = time.time()
		cls.logbook('data reduction ... DONE (in %g seconds)!' % (end_time - start_time))
		cls.logbook('================================================')

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

	def removeTempWorkspaces(cls, listWorkspaces):
		list_mt = AnalysisDataService.getObjectNames()
		for _mt in list_mt:
			if _mt in listWorkspaces:
				continue
			AnalysisDataService.remove(_mt)

	def removePreviousWorkspaces(cls):
		list_mt = AnalysisDataService.getObjectNames()
		for _mt in list_mt:
			if _mt.find('_scaled') != -1:
				AnalysisDataService.remove(_mt)


