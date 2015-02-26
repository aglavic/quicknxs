import math
from mantid.simpleapi import *
import numpy as np

class CalculateSF(object):
	'''
	This class will determine the best scaling factor (SF) to apply to the data to stitch them
	'''
	
	bigTableData = []
	main_gui = None
	
	def __init__(self, bigTableData, main_gui):
		self.bigTableData = bigTableData
		self.main_gui = main_gui

		if bigTableData is None:
			return
		
		self.calculateAutoSF()
		
	def calculateAutoSF(self):
		'''
		main part of the program that will calculate the various SF
		'''
		self.autoSFofFirstDataSet()
		self.autoSFAllOtherDataSet()
		
	def autoSFofFirstDataSet(self):
		'''
		Critical edge set must be brought to 0
		'''
		self.logbook('-> Calculate scaling factor of Critical Edge file:')

		dataSet = self.bigTableData[0,0]
		configObject = self.bigTableData[0,2]
		
		_y_axis = dataSet.reduce_y_axis
		_e_axis = dataSet.reduce_e_axis
		error_0 = 1./configObject.proton_charge
		[data_mean, mean_error] = self.weightedMean(_y_axis, _e_axis, error_0)
		_sf = 1./data_mean 
		
		data_CE = self.bigTableData[0,0]
		data_CE.sf_auto = _sf
		self.bigTableData[0,0] = data_CE
	
		self.logbook('--> SF = ' + str(_sf))
	
	def autoSFAllOtherDataSet(self):
		'''
		the data set #2 will be scaled according to first one, etc
		fit will be performed by using a fit of the overlap regions and comparing them
		'''
		self.logbook('-> Calculate scaling factor of all other data sets:')

		nbr_row = self.main_gui.ui.reductionTable.rowCount()
		for j in range(1,nbr_row):
			left_set = self.applyLeftSF(self.bigTableData[j-1, 0])
			right_set = self.bigTableData[j, 0]

			_sf = 1./self.fitDataOfOverlapRange(left_set, right_set)

			right_set.sf_auto = _sf
			self.bigTableData[j,0] = right_set
			
			self.logbook('--> SF of data set #' + str(j) + ' = ' + str(_sf))
	

	def fitDataOfOverlapRange(self, left_set, right_set):
		'''
		fit data of the overlaping region between left and right sets
		'''
		left_x_axis = left_set.reduce_q_axis
		right_x_axis = right_set.reduce_q_axis
		[min_x, max_x, index_min_in_left, index_max_in_right, noOverlap] = self.calculateOverlapAxis(left_x_axis, right_x_axis)
		if noOverlap:
			_sf = 1

		else:
			[a_left, b_left] = self.fitData(left_set, index_min_in_left, type='left')
			[a_right, b_right] = self.fitData(right_set, index_max_in_right, type='right')

			nbr_points = 10
			fit_range_to_use = self.getFittingOverlapRange(min_x, max_x, nbr_points)

			_sf = self.scaleToApplyForBestOverlap(fit_range_to_use, a_left, b_left, a_right, b_right)

		return _sf
	

	def calculateRatioOfLeftRightMean(self, left_set, right_set):
		'''
		calculate ratio of left and right mean
		'''
		left_x_axis = left_set.reduce_q_axis
		right_x_axis = right_set.reduce_q_axis
		[min_x, max_x, noOverlap] = self.calculateOverlapAxis(left_x_axis, right_x_axis)
		if noOverlap:
			_sf = 1
		else:
			left_mean = self.calculateLeftWeightedMean(min_x, max_x, left_set.tmp_y_axis, tmp_e_axis)
			right_mean = self.calculateRightWeightedMean(min_x, max_x, right_set.reduce_y_axis, right_set.reduce_e_axis)
			

	def applyLeftSF(self, left_set):
		'''
		In order to calculate the right SF, we must apply the previously calculated left SF
		'''
		y_axis = left_set.reduce_y_axis
		e_axis = left_set.reduce_e_axis
		sf = left_set.sf_auto
		y_axis = y_axis * sf
		e_axis = e_axis * sf
		
		left_set.tmp_y_axis = y_axis
		left_set.tmp_e_axis = e_axis
		
		return left_set
			
		
	def  calculateLeftWeightedMean(self, min_x, max_x, x_axis, y_axis, e_axis):
		pass
			
			
	def fitData(self, data_set, threshold_index, type='right'):
		'''
		will fit the data with linear fitting y=ax + b
		'''
		a = 0
		b = 0
		
		if type == 'left':
			x_axis = data_set.reduce_q_axis[threshold_index:-1]
			y_axis = data_set.tmp_y_axis[threshold_index:-1]
			e_axis = data_set.tmp_e_axis[threshold_index:-1]
		else:
			x_axis = data_set.reduce_q_axis[0:threshold_index]
			y_axis = data_set.reduce_y_axis[0:threshold_index]
			e_axis = data_set.reduce_e_axis[0:threshold_index]
		
		dataToFit = CreateWorkspace(DataX = x_axis,
		                            DataY = y_axis,
		                            DataE = e_axis,
		                            Nspec = 1)
		
		dataToFit = ReplaceSpecialValues(InputWorkspace = dataToFit, 
		                                 NaNValue = 0,
		                                 NaNError = 0,
		                                 InfinityValue = 0,
		                                 InfinityError = 0)
		
		Fit(InputWorkspace = dataToFit, 
		    Function = "name=UserFunction, Formula=a+b*x, a=1, b=2",
		    Output='res')
		
		res = mtd['res_Parameters']
		
		b = res.cell(0,1)
		a = res.cell(1,1)
		
		return [a,b]

		
	def scaleToApplyForBestOverlap(self, fit_range_to_use, a_left, b_left, a_right, b_right):
		'''
		This function will use the same overlap region and will determine the scaling to apply to 
		the second fit to get the best match
		'''
			
		left_mean = self.calculateMeanOfFctOverRange(fit_range_to_use, a_left, b_left)
		right_mean = self.calculateMeanOfFctOverRange(fit_range_to_use, a_right, b_right)
			
		_sf =  right_mean / left_mean

		return _sf

		
	def calculateOverlapAxis(self, left_axis, right_axis):
		'''
		calculate the overlap region of the two axis
		'''
		global_min = min([left_axis[0], right_axis[0]])
		global_max = max([left_axis[-1], right_axis[-1]])
		
		_min_x = -1
		_max_x = -1
		noOverlap = True
		left_min_index = 0
		right_max_index = -1
		
		if left_axis[-1] < right_axis[0]: # no overlap
			return [_min_x, _max_x, left_min_index, right_max_index, noOverlap]
			
		_min_x = right_axis[0]
		_max_x = left_axis[-1]
		noOverlap = False

		left_min_index = self.find_nearest(left_axis, _min_x)
		right_max_index = self.find_nearest(right_axis, _max_x)
		
		return [_min_x, _max_x, left_min_index, right_max_index, noOverlap]

	
	def find_nearest(self, array, value):
		idx = (np.abs(array-value)).argmin()
		return idx
	
	
	def getFittingOverlapRange(self, min_x, max_x, nbr_points):
		
		step = (float(max_x) - float(min_x)) / float(nbr_points)
		_fit_range = np.arange(min_x, max_x + step, step)
		return _fit_range
	

	def calculateMeanOfFctOverRange(self, range_to_use, a, b):
		'''
		will return the average value of the function over the given range
		'''
		sz_range = range_to_use.size
		_sum = 0
		for i in range(sz_range):
			_value = self.fct(a=a, b=b, x=range_to_use[i])
			_sum += _value

		_mean = float(_sum) / float(sz_range)
		return _mean
		
	def fct(self, a, b, x):
		_value = a * x + b
		return _value

		
	def weightedMean(self, data_array, error_array, error_0):
		
		sz = len(data_array)
	    
		# calculate the numerator of mean
		dataNum = 0;
		for i in range(sz):
			if (error_array[i] == 0):
				error_array[i] = error_0
	    
			tmpFactor = float(data_array[i]) / float((pow(error_array[i],2)))
			dataNum += tmpFactor
	    
		# calculate denominator
		dataDen = 0;
		for i in range(sz):
			if (error_array[i] == 0):
				error_array[i] = error_0
			tmpFactor = 1./float((pow(error_array[i],2)))
			dataDen += tmpFactor
	    
		if dataDen == 0:
			data_mean = np.nan
			mean_error = np.nan
		else:
			data_mean = float(dataNum) / float(dataDen)
			mean_error = math.sqrt(1/dataDen)
	    
		return [data_mean, mean_error]
		
		
	def getAutoScaledData(self):
		return self.bigTableData
	
	def logbook(self, text, appendFlag=True):
		if appendFlag:
			self.main_gui.ui.logbook.append(text)
		else:
		    self.main_gui.ui.logbook.undo()
		    self.main_gui.ui.logbook.append(text)
