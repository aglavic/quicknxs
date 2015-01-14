from PyQt4 import QtGui, QtCore
import colors
from clear_plots import ClearPlots

class DisplayPlots(object):
	
	self = None
	activeData = None

	rowColSelected = None
	filename = ''
	
	peak = None
	back = None
	lowRes = None
	backFlag = True
	lowResFlag = True
	
	incidentAngle = None
	qRange = None
	lambdaRange = None

	useItFlag = True
	
	yt_plot_ui = None
	yi_plot_ui = None
	it_plot_ui = None
	ix_plot_ui = None
	
	xlim = 255
	ylim = 303

	tofAxis = None
	fullTofAxis = None
	tofRangeAuto = None
	xy = None
	ytof = None
	countstofdata = None
	countsxdata = None
	ycountsdata = None

	def __init__(cls, self, plot_yt=True, plot_yi=True, plot_it=True, plot_ix=True, plot_reduced=False, plot_stitched=False):
		cls.self = self
		
		[row,col] = self.getCurrentRowColumnSelected()
		cls.rowColSelected = [row,col]
		_data = self.bigTableData[row,col]
		if _data is None:
			ClearPlots(self, is_data=cls.isDataSelected(), is_norm=not cls.isDataSelected(), all_plots=True)
			return
		
		_active_data = _data.active_data
		cls.activeData = _active_data
		cls.filename = _active_data.filename
		if (not _active_data.new_detector_geometry_flag):
			cls.xlim = 303
			cls.ylim = 255
		
		if self.ui.dataTOFmanualMode.isChecked():
			cls.tofRangeAuto = cls.getTOFrangeInMs(_active_data.tof_range)
		else:
			cls.tofRangeAuto = cls.getTOFrangeInMs(_active_data.tof_range_auto)
		cls.tofAxis = cls.getTOFrangeInMs(_active_data.tof_axis_auto_with_margin)
		cls.fullTofAxis = cls.getFullTOFinMs(_active_data.tof_axis_auto_with_margin)
		
		cls.xy  = _active_data.xydata
		cls.ytof = _active_data.ytofdata
		cls.countstofdata = _active_data.countstofdata
		cls.countsxdata = _active_data.countsxdata
		cls.ycountsdata = _active_data.ycountsdata
		
		cls.peak = cls.sortIntArray(_active_data.peak)
		cls.back = cls.sortIntArray(_active_data.back)
		cls.lowRes = cls.sortIntArray(_active_data.low_res)
		cls.backFlag = bool(_active_data.back_flag)
		cls.lowResFlag = bool(_active_data.low_res_flag)
		
		is_data = True
		is_norm = False
		
		if cls.isDataSelected():
			cls.qRange = _active_data.q_range
			cls.incidentAngle = _active_data.incident_angle
			cls.lambdaRange = _active_data.lambda_range
			cls.workWithData()
		else:
			is_data = False
			is_norm = True
			cls.useItFlag = _active_data.use_it_flag
			cls.workWithNorm()
		
		if plot_yt:
			ClearPlots(cls.self, plot_yt=True, is_data=is_data, is_norm=is_norm)
			cls.plot_yt()

		if plot_it:
			ClearPlots(cls.self, plot_it=True, is_data=is_data, is_norm=is_norm)
			cls.plot_it()
			
		if plot_yi:
			ClearPlots(cls.self, plot_yi=True, is_data=is_data, is_norm=is_norm)
			cls.plot_yi()
			
		if plot_ix:
			ClearPlots(cls.self, plot_ix=True, is_data=is_data, is_norm=is_norm)
			cls.plot_ix()
		
		if plot_yt or plot_it or plot_yi or plot_ix:
			if cls.isDataSelected():
				self.ui.dataNameOfFile.setText('%s'%(cls.filename))
			else:
				self.ui.normNameOfFile.setText('%s'%(cls.filename))
			cls.displayMetadata()
			
	def displayMetadata(cls):
		cls.clearMetadataWidgets()
		d = cls.activeData
		if d is None:
			return
		self = cls.self
		self.ui.metadataProtonChargeValue.setText('%.2e'%d.proton_charge)
		self.ui.metadataProtonChargeUnits.setText('%s'%d.proton_charge_units)
		self.ui.metadataLambdaRequestedValue.setText('%.2f'%d.lambda_requested)
		self.ui.metadataLambdaRequestedUnits.setText('%s'%d.lambda_requested_units)
		self.ui.metadatathiValue.setText('%.2f'%d.thi)
		self.ui.metadatathiUnits.setText('%s'%d.thi_units)
		self.ui.metadatatthdValue.setText('%.2f'%d.tthd)
		self.ui.metadatatthdUnits.setText('%s'%d.tthd_units)
		self.ui.metadataS1WValue.setText('%.2f'%d.S1W)
		self.ui.metadataS1HValue.setText('%.2f'%d.S1H)
		if d.isSiThere:
			self.ui.S2SiWlabel.setText('SiW')
			self.ui.S2SiHlabel.setText('SiH')
			self.ui.metadataS2WValue.setText('%.2f'%d.SiW)
			self.ui.metadataS2HValue.setText('%.2f'%d.SiH)
		else:
			self.ui.S2SiWlabel.setText('S2W')
			self.ui.S2SiHlabel.setText('S2H')
			self.ui.metadataS2WValue.setText('%.2f'%d.S2W)
			self.ui.metadataS2HValue.setText('%.2f'%d.S2H)

	def clearMetadataWidgets(cls):
		self = cls.self
		self.ui.metadataProtonChargeValue.setText('N/A')
		self.ui.metadataLambdaRequestedValue.setText('N/A')
		self.ui.metadataS1HValue.setText('N/A')
		self.ui.metadataS1WValue.setText('N/A')
		self.ui.metadataS2HValue.setText('N/A')
		self.ui.metadataS2WValue.setText('N/A')
		self.ui.metadatathiValue.setText('N/A')
		self.ui.metadatatthdValue.setText('N/A')
			
	def plot_ix(cls):
		_countsxdata = cls.countsxdata
		cls.ix_plot_ui.canvas.ax.plot(_countsxdata)
		cls.ix_plot_ui.canvas.ax.set_xlabel(u'pixels')
		cls.ix_plot_ui.canvas.ax.set_ylabel(u'counts')
		cls.ix_plot_ui.canvas.ax.set_xlim(0, cls.xlim)
		
		if cls.lowResFlag:
			cls.ix_plot_ui.canvas.ax.axvline(cls.lowRes[0], color=colors.LOWRESOLUTION_SELECTION_COLOR)
			cls.ix_plot_ui.canvas.ax.axvline(cls.lowRes[1], color=colors.LOWRESOLUTION_SELECTION_COLOR)
			
		if cls.activeData.all_plot_axis.is_ix_ylog:
			cls.ix_plot_ui.canvas.ax.set_yscale('log')
		else:
			cls.ix_plot_ui.canvas.ax.set_yscale('linear')
			
		if cls.activeData.all_plot_axis.ix_data_interval is None:
			cls.ix_plot_ui.canvas.draw()
			[xmin,xmax] = cls.ix_plot_ui.canvas.ax.xaxis.get_view_interval()
			[ymin,ymax] = cls.ix_plot_ui.canvas.ax.yaxis.get_view_interval()
			cls.activeData.all_plot_axis.ix_data_interval = [xmin,xmax,ymin,ymax]
			cls.activeData.all_plot_axis.ix_view_interval = [xmin,xmax,ymin,ymax]
			cls.ix_plot_ui.toolbar.home_settings = [xmin,xmax,ymin,ymax]
		else:
			[xmin,xmax,ymin,ymax] = cls.activeData.all_plot_axis.ix_view_interval
			cls.ix_plot_ui.canvas.ax.set_xlim([xmin,xmax])
			cls.ix_plot_ui.canvas.ax.set_ylim([ymin,ymax])
			cls.ix_plot_ui.canvas.draw()
			
	def plot_yi(cls):
		_ycountsdata = cls.ycountsdata
		_xaxis = range(len(_ycountsdata))
		cls.yi_plot_ui.canvas.ax.plot(_ycountsdata, _xaxis, color=colors.COLOR_LIST[1])
		cls.yi_plot_ui.canvas.ax.set_xlabel(u'counts')
		cls.yi_plot_ui.canvas.ax.set_ylabel(u'y (pixel)')
		
		if cls.activeData.all_plot_axis.yi_data_interval is None:
			cls.yi_plot_ui.canvas.ax.set_ylim(0, cls.ylim)
		
		cls.yi_plot_ui.canvas.ax.axhline(cls.peak[0], color=colors.PEAK_SELECTION_COLOR)
		cls.yi_plot_ui.canvas.ax.axhline(cls.peak[1], color=colors.PEAK_SELECTION_COLOR)
		
		if cls.backFlag:
			cls.yi_plot_ui.canvas.ax.axhline(cls.back[0], color=colors.BACK_SELECTION_COLOR)
			cls.yi_plot_ui.canvas.ax.axhline(cls.back[1], color=colors.BACK_SELECTION_COLOR)
			
		if cls.activeData.all_plot_axis.is_yi_xlog:
			cls.yi_plot_ui.canvas.ax.set_xscale('log')
		else:
			cls.yi_plot_ui.canvas.ax.set_xscale('linear')
			
		if cls.activeData.all_plot_axis.yi_data_interval is None:
			cls.yi_plot_ui.canvas.draw()
			[xmin, xmax] = cls.yi_plot_ui.canvas.ax.xaxis.get_view_interval()
			[ymin, ymax] = cls.yi_plot_ui.canvas.ax.yaxis.get_view_interval()
			cls.activeData.all_plot_axis.yi_data_interval = [xmin, xmax, ymin, ymax]
			cls.activeData.all_plot_axis.yi_view_interval = [xmin, xmax, ymin, ymax]
			cls.yi_plot_ui.toolbar.home_settings = [xmin, xmax, ymin, ymax]
		else:
			[xmin, xmax, ymin, ymax] = cls.activeData.all_plot_axis.yi_view_interval
			cls.yi_plot_ui.canvas.ax.set_xlim([xmin, xmax])
			cls.yi_plot_ui.canvas.ax.set_ylim([ymin, ymax])
			cls.yi_plot_ui.canvas.draw()

	def plot_it(cls):
		_tof_axis =cls.fullTofAxis
		_countstofdata = cls.countstofdata
		cls.it_plot_ui.canvas.ax.plot(_tof_axis[0:-1], _countstofdata)
		cls.it_plot_ui.canvas.ax.set_xlabel(u't (ms)')
		cls.it_plot_ui.canvas.ax.set_ylabel(u'Counts')

		autotmin = float(cls.tofRangeAuto[0])
		autotmax = float(cls.tofRangeAuto[1])
		cls.it_plot_ui.canvas.ax.axvline(autotmin, color=colors.TOF_SELECTION_COLOR)
		cls.it_plot_ui.canvas.ax.axvline(autotmax, color=colors.TOF_SELECTION_COLOR)
		
		if cls.activeData.all_plot_axis.is_it_ylog:
			cls.it_plot_ui.canvas.ax.set_yscale('log')
		else:
			cls.it_plot_ui.canvas.ax.set_yscale('linear')
			
		if cls.activeData.all_plot_axis.it_data_interval is None:
			cls.it_plot_ui.canvas.draw()
			[xmin,xmax] = cls.it_plot_ui.canvas.ax.xaxis.get_view_interval()
			[ymin,ymax] = cls.it_plot_ui.canvas.ax.yaxis.get_view_interval()
			cls.activeData.all_plot_axis.it_data_interval = [xmin,xmax,ymin,ymax]
			cls.activeData.all_plot_axis.it_view_interval = [xmin,xmax,ymin,ymax]
			cls.it_plot_ui.toolbar.home_settings = [xmin,xmax,ymin,ymax]
		else:
			[xmin,xmax,ymin,ymax]= cls.activeData.all_plot_axis.it_view_interval
			cls.it_plot_ui.canvas.ax.set_xlim([xmin,xmax])
			cls.it_plot_ui.canvas.ax.set_ylim([ymin,ymax])
			cls.it_plot_ui.canvas.draw()
	
	def plot_yt(cls):
		
		_ytof = cls.ytof
		_isLog = True
		_tof_axis = cls.tofAxis
		_extent = [_tof_axis[0], _tof_axis[1],0, cls.ylim]
		cls.yt_plot_ui.imshow(_ytof, log=_isLog, 
		                      aspect='auto', 
		                      origin='lower',
		                      extent=_extent)
		cls.yt_plot_ui.set_xlabel(u't (ms)')
		cls.yt_plot_ui.set_ylabel(u'y (pixel)')
		
		autotmin = float(cls.tofRangeAuto[0])
		autotmax = float(cls.tofRangeAuto[1])
		cls.displayTOFrange(autotmin, autotmax, 'ms')
		[tmin, tmax] = cls.getTOFrangeInMs([autotmin, autotmax])
		cls.yt_plot_ui.canvas.ax.axvline(tmin, color=colors.TOF_SELECTION_COLOR)
		cls.yt_plot_ui.canvas.ax.axvline(tmax, color=colors.TOF_SELECTION_COLOR)
		
		cls.yt_plot_ui.canvas.ax.axhline(cls.peak[0], color=colors.PEAK_SELECTION_COLOR)
		cls.yt_plot_ui.canvas.ax.axhline(cls.peak[1], color=colors.PEAK_SELECTION_COLOR)
		
		if cls.backFlag:
			cls.yt_plot_ui.canvas.ax.axhline(cls.back[0], color=colors.BACK_SELECTION_COLOR)
			cls.yt_plot_ui.canvas.ax.axhline(cls.back[1], color=colors.BACK_SELECTION_COLOR)
		
		if cls.activeData.all_plot_axis.is_yt_ylog:
			cls.yt_plot_ui.canvas.ax.set_yscale('log')
		else:
			cls.yt_plot_ui.canvas.ax.set_yscale('linear')
		
		if cls.activeData.all_plot_axis.yt_data_interval is None:
			cls.yt_plot_ui.canvas.ax.set_ylim(0,cls.ylim)
			cls.yt_plot_ui.canvas.draw()
			[xmin,xmax] = cls.yt_plot_ui.canvas.ax.xaxis.get_view_interval()
			[ymin,ymax] = cls.yt_plot_ui.canvas.ax.yaxis.get_view_interval()
			cls.activeData.all_plot_axis.yt_data_interval = [xmin, xmax, ymin, ymax]
			cls.activeData.all_plot_axis.yt_view_interval = [xmin, xmax, ymin, ymax]
			cls.yt_plot_ui.toolbar.home_settings = [xmin, xmax, ymin, ymax]
		else:
			[xmin,xmax,ymin,ymax] = cls.activeData.all_plot_axis.yt_view_interval
			cls.yt_plot_ui.canvas.ax.set_xlim([xmin,xmax])
			cls.yt_plot_ui.canvas.ax.set_ylim([ymin,ymax])
			cls.yt_plot_ui.canvas.draw()
		
	def displayTOFrange(cls, tmin, tmax, units):
		self = cls.self
	  
		_tmin = 1e-3 * float(tmin)
		_tmax = 1e-3 * float(tmax)
		
		stmin = str("%.2f" % _tmin)
		stmax = str("%.2f" % _tmax)
		
		self.ui.TOFmanualFromValue.setText(stmin)
		self.ui.TOFmanualToValue.setText(stmax)
		
	def workWithNorm(cls):
		self = cls.self
		
		self.ui.useNormalizationFlag.setChecked(cls.useItFlag)
		
		[peak1, peak2] = cls.peak
		self.ui.normPeakFromValue.setValue(peak1)
		self.ui.normPeakToValue.setValue(peak2)
		
		[back1, back2] = cls.back
		self.ui.normBackFromValue.setValue(back1)
		self.ui.normBackToValue.setValue(back2)
		self.ui.normBackgroundFlag.setChecked(cls.backFlag)
		
		[lowRes1, lowRes2] = cls.lowRes
		self.ui.normLowResFromValue.setValue(lowRes1)
		self.ui.normLowResToValue.setValue(lowRes2)
		self.ui.normLowResFlag.setChecked(cls.lowResFlag)
		
		cls.yt_plot_ui = self.ui.norm_yt_plot
		cls.yi_plot_ui = self.ui.norm_yi_plot
		cls.it_plot_ui = self.ui.norm_it_plot
		cls.ix_plot_ui = self.ui.norm_ix_plot
			
	def workWithData(cls):
		self = cls.self
		
		[peak1, peak2] = cls.peak	
		self.ui.dataPeakFromValue.setValue(peak1)
		self.ui.dataPeakToValue.setValue(peak2)

		[back1, back2] = cls.back
		self.ui.dataBackFromValue.setValue(back1)
		self.ui.dataBackToValue.setValue(back2)
		self.ui.dataBackgroundFlag.setChecked(cls.backFlag)
		
		[lowRes1, lowRes2] = cls.lowRes
		self.ui.dataLowResFromValue.setValue(lowRes1)
		self.ui.dataLowResToValue.setValue(lowRes2)
		self.ui.dataLowResFlag.setChecked(cls.lowResFlag)
		
		cls.yt_plot_ui = self.ui.data_yt_plot
		cls.yi_plot_ui = self.ui.data_yi_plot
		cls.it_plot_ui = self.ui.data_it_plot
		cls.ix_plot_ui = self.ui.data_ix_plot
		
		[qmin, qmax] = cls.qRange
		_item_min = QtGui.QTableWidgetItem(str(qmin))
		_item_min.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)      
		_item_max = QtGui.QTableWidgetItem(str(qmax))
		_item_max.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)      

		[lmin, lmax] = cls.lambdaRange
		_item_lmin = QtGui.QTableWidgetItem(str(lmin))
		_item_lmin.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)      
		_item_lmax = QtGui.QTableWidgetItem(str(lmax))
		_item_lmax.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)      

		incident_angle = cls.incidentAngle
		_item_incident = QtGui.QTableWidgetItem(str(incident_angle))
		_item_incident.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)      

		[row, col] = cls.rowColSelected
		self.ui.reductionTable.setItem(row, 4, _item_min)
		self.ui.reductionTable.setItem(row, 5, _item_max)
		self.ui.reductionTable.setItem(row, 2, _item_lmin)
		self.ui.reductionTable.setItem(row, 3, _item_lmax)
		self.ui.reductionTable.setItem(row, 1, _item_incident)
		
	def isDataSelected(cls):
		if cls.self.ui.dataNormTabWidget.currentIndex() == 0:
			return True
		else:
			return False
		
	def sortIntArray(cls, _array):
		[_element1, _element2] = _array
		_element1 = int(_element1)
		_element2 = int(_element2)
		_element_min = min([_element1, _element2])
		_element_max = max([_element1, _element2])
		return [_element_min, _element_max]

	def getTOFrangeInMs(cls, tof_axis):
		if tof_axis[0] > 1000:
			coeff = 1e-3
		else:
			coeff = 1
		return [tof_axis[0] * coeff, tof_axis[-1]*coeff]
		
	def getFullTOFinMs(cls, tof_axis):
		if tof_axis[0] > 1000:
			return tof_axis / float(1000)
		else:
			return tof_axis