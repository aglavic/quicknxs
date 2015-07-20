from PyQt4 import QtGui, QtCore
from reduced_ascii_loader import reducedAsciiLoader
import colors
import numpy as np

class stitchingAsciiWidgetObject(object):

	loadedAsciiArray = []
	tableUi = None
	stitchingPlot = None
	mainGui = None
	isylog = True
	isxlog = True
	yaxistype = 'RvsQ'
	
	def __init__(self, mainGui, loadedAscii):
		
		self.mainGui = mainGui
		self.loadedAsciiArray.append(loadedAscii)
		self.tableUi = mainGui.ui.reducedAsciiDataSetTable
		self.stitchingPlot = mainGui.ui.data_stitching_plot
		
	def addData(self, newLoadedAscii):
		
		rowOfThisFile = self.getRowOfThisFile(newLoadedAscii)
		if rowOfThisFile == -1:
			#add row
			self.loadedAsciiArray.append(newLoadedAscii)
		else:
			# replace
			self.loadedAsciiArray[rowOfThisFile] = newLoadedAscii
		
	def getRowOfThisFile(self, loadedAscii):
		
		newFilename = loadedAscii.asciiFilename

		nbrRow = len(self.loadedAsciiArray)
		for i in range(nbrRow):
			_tmpObject = self.loadedAsciiArray[i]
			_name = _tmpObject.asciiFilename
			
			if _name == newFilename:
				return i
			
		return -1
			
	def updateStatus(self):
		
		nbrRow = len(self.loadedAsciiArray)
		for i in range(nbrRow):
			
			_data_object = self.loadedAsciiArray[i]
			
			_item_state = self.mainGui.ui.reducedAsciiDataSetTable.cellWidget(i,1).checkState()
			if _item_state == 2:
				_data_object.isEnabled = True
			else:
				_data_object.isEnabled = False
			
			self.loadedAsciiArray[i] = _data_object
			
	def updateDisplay(self, isylog=True, isxlog=True, yaxistype='RvsQ'):
		
		self.isylog = isylog
		self.isxlog = isxlog
		self.yaxistype = yaxistype
		
		self.tableUi.clearContents()
		self.stitchingPlot.clear()
		self.stitchingPlot.draw()
		
		nbrRow = len(self.loadedAsciiArray)
		for i in range(nbrRow):
			self.tableUi.removeRow(i)
		
		for i in range(nbrRow):
			
			_data_object = self.loadedAsciiArray[i]

			self.tableUi.insertRow(i)

			_item = QtGui.QTableWidgetItem(str(_data_object.shortAsciiFilename))
			self.tableUi.setItem(i,0,_item)
			
			_widget = QtGui.QCheckBox()
			if _data_object.isEnabled:
				_status = QtCore.Qt.Checked
			else:
				_status = QtCore.Qt.Unchecked
			_widget.setCheckState(_status)
			self.tableUi.setCellWidget(i, 1, _widget)
			
			if _data_object.isEnabled:
				
				if _data_object.isLiveReduced:
					self.displayLiveData(_data_object)
				else:
					#self.displayLoadedAscii(_data_object)
					_q_axis = _data_object.col1
					_y_axis = _data_object.col2
					_e_axis = _data_object.col3
				
					[_y_axis_red, _e_axis_red] = self.formatDataFromYmodeSelected(_q_axis, 
					                                                              _y_axis,
					                                                              _e_axis)
					
					self.stitchingPlot.errorbar(_q_axis, _y_axis_red, yerr=_e_axis_red)
					if isylog:
						self.stitchingPlot.set_yscale('log')
					else:
						self.stitchingPlot.set_yscale('linear')
						
					if isxlog:
						self.stitchingPlot.set_xscale('log')
					else:
						self.stitchingPlot.set_xscale('linear')
					self.stitchingPlot.draw()


	def displayLiveData(self, _data_object):
		'''
		plot last reduced data set
		'''
		
		bigTableData = _data_object.bigTableData
		_colors = colors.COLOR_LIST
		_colors.append(_colors)
		
		_data0 = bigTableData[0,0]
		
		i=0
		while (bigTableData[i,2] is not None):
			
			_data = bigTableData[i,2]
			_q_axis = _data.q_axis_for_display
			_y_axis = _data.y_axis_for_display
			_e_axis = _data.e_axis_for_display
			
			sf = _data.sf
			
			_y_axis = _y_axis / sf
			_e_axis = _e_axis / sf
			
			[y_axis_red, e_axis_red] = self.formatDataFromYmodeSelected(_q_axis, 
			                                                            _y_axis,
			                                                            _e_axis)
			
			self.stitchingPlot.errorbar(_q_axis, y_axis_red, yerr=e_axis_red, color=_colors[i])
			if self.isylog:
				self.stitchingPlot.set_yscale('log')
			else:
				self.stitchingPlot.set_yscale('linear')
			if self.isxlog:
				self.stitchingPlot.set_xscale('log')
			else:
				self.stitchingPlot.set_xscale('linear')
				
			self.stitchingPlot.draw()

			i+=1
	
		if _data0.active_data.all_plot_axis.reduced_plot_stitching_tab_data_interval is None:
			[xmin,xmax] = self.stitchingPlot.canvas.ax.xaxis.get_view_interval()
			[ymin,ymax] = self.stitchingPlot.canvas.ax.yaxis.get_view_interval()
			_data0.active_data.all_plot_axis.reduced_plot_stitching_tab_data_interval = [xmin,xmax,ymin,ymax]
			_data0.active_data.all_plot_axis.reduced_plot_stitching_tab_view_interval = [xmin,xmax,ymin,ymax]
			self.stitchingPlot.toolbar.home_settings = [xmin,xmax,ymin,ymax]
		else:
			[xmin,xmax,ymin,ymax] = _data0.active_data.all_plot_axis.reduced_plot_stitching_tab_view_interval
			self.stitchingPlot.canvas.ax.set_xlim([xmin,xmax])
			self.stitchingPlot.canvas.ax.set_ylim([ymin,ymax])
			self.stitchingPlot.draw()
			
		bigTableData[0,0] = _data0
		self.mainGui.bigTableData = bigTableData

		self.stitchingPlot.set_xlabel(u'Q (1/Angstroms)')
		type = self.getSelectedReducedOutput()
		if type == 'RvsQ':
			self.stitchingPlot.set_ylabel(u'R')
		elif type == 'RQ4vsQ':
			self.stitchingPlot.set_ylabel(u'RQ4')
		else:
			self.stitchingPlot.set_ylabel(u'Log(Q))')
		self.stitchingPlot.draw()
		
				
	def formatDataFromYmodeSelected(self, q_axis, y_axis, e_axis):
		
		type = self.getSelectedReducedOutput()
		[final_y_axis, final_e_axis] = self.getFormatedOutput(type, q_axis, y_axis, e_axis)
		return [final_y_axis, final_e_axis]
		
		
	def getFormatedOutput(self, type, _q_axis, _y_axis, _e_axis):

		# R vs Q selected
		if type == 'RvsQ':
			return [_y_axis, _e_axis]
		
		# RQ4 vs Q selected
		if type == 'RQ4vsQ':
			_q_axis_4 = _q_axis ** 4
			_final_y_axis = _y_axis * _q_axis_4
			_final_e_axis = _e_axis * _q_axis_4
			return [_final_y_axis, _final_e_axis]
	    
		# Log(R) vs Q
		_final_y_axis = np.log(_y_axis)
		#    _final_e_axis = np.log(_e_axis)
		_final_e_axis = _e_axis  ## FIXME
		return [_final_y_axis, _final_e_axis]
		

	def getSelectedReducedOutput(self):
		return self.yaxistype

	def 	displayLoadedAscii(self, _data_object):
		'''
		plot data coming from ascii file loaded
		'''
		_q_axis = _data_object.col1
		_y_axis = _data_object.col2
		_e_axis = _data_object.col3
	
		self.stitchingPlot.errorbar(_q_axis, _y_axis, yerr=_e_axis)
		self.stitchingPlot.draw()
