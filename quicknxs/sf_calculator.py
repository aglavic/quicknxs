from PyQt4 import QtGui, QtCore
from sf_calculator_interface import Ui_MainWindow
from run_sequence_breaker import RunSequenceBreaker
from mantid.simpleapi import *
from load_and_sort_nxsdata_for_sf_calculator import LoadAndSortNXSDataForSFcalculator
from display_metadata import DisplayMetadata
from logging import info
from utilities import touch, import_ascii_file, makeSureFileHasExtension, convertTOF
from create_sf_config_xml_file import CreateSFConfigXmlFile
from load_sf_config_and_populate_gui import LoadSFConfigAndPopulateGUI
from fill_sf_gui_table import FillSFGuiTable
from load_nx_data import LoadNXData

import colors
import numpy as np
import os

class SFcalculator(QtGui.QMainWindow):
	_open_instances = []
	main_gui = None
	data_list = []
	big_table = None
	big_table_nxdata = []
	is_using_si_slits = False
	loaded_list_of_runs = []
	list_nxsdata_sorted = []
	window_title = 'SF Calculator - '
	
	def __init__(cls, main_gui, parent=None):
		cls.main_gui = main_gui
		QtGui.QMainWindow.__init__(cls)
		cls._open_instances.append(cls)
		cls.ui = Ui_MainWindow()
		cls.ui.setupUi(cls)
		cls.initGui()
		cls.checkGui()
		
	def initGui(cls):
		palette = QtGui.QPalette()
		palette.setColor(QtGui.QPalette.Foreground, colors.VALUE_BAD)
		cls.ui.back1_error.setPalette(palette)
		cls.ui.back2_error.setPalette(palette)
		cls.ui.peak1_error.setPalette(palette)
		cls.ui.peak2_error.setPalette(palette)
		cls.ui.error_label.setPalette(palette)
	
	def checkGui(cls):
		if (cls.loaded_list_of_runs != []) or (cls.big_table != []):
			wdg_enabled = True
		else:
			wdg_enabled = False
		cls.enabledWidgets(wdg_enabled)
		cls.testPeakBackErrorWidgets()
		cls.ui.actionSavingConfiguration.setEnabled(wdg_enabled)
		cls.ui.tableWidget.setEnabled(wdg_enabled)
				
	def testPeakBackErrorWidgets(cls):
		if cls.list_nxsdata_sorted == []:
			_show_widgets_1 = False
			_show_widgets_2 = False
		else:
			back_to = int(cls.ui.dataBackToValue.text())
			back_from = int(cls.ui.dataBackFromValue.text())
			peak_to = int(cls.ui.dataPeakToValue.text())
			peak_from = int(cls.ui.dataPeakFromValue.text())
			back_flag = cls.ui.dataBackgroundFlag.isChecked()
			
			_show_widgets_1 = False
			_show_widgets_2 = False
			
			if back_flag:
				if back_from > peak_from:
					_show_widgets_1 = True
				if back_to < peak_to:
					_show_widgets_2 = True
					
		cls.ui.back1_error.setVisible(_show_widgets_1)
		cls.ui.peak1_error.setVisible(_show_widgets_1)
		cls.ui.back2_error.setVisible(_show_widgets_2)
		cls.ui.peak2_error.setVisible(_show_widgets_2)
		cls.ui.error_label.setVisible(_show_widgets_1 or _show_widgets_2)
		
	def enabledWidgets(cls, is_enabled):
		cls.ui.yi_plot.setEnabled(is_enabled)
		cls.ui.yt_plot.setEnabled(is_enabled)
		cls.ui.dataBackFromLabel.setEnabled(is_enabled)
		cls.ui.dataBackToLabel.setEnabled(is_enabled)
		cls.ui.dataBackFromValue.setEnabled(is_enabled)
		cls.ui.dataBackToValue.setEnabled(is_enabled)
		cls.ui.dataPeakFromLabel.setEnabled(is_enabled)
		cls.ui.dataPeakToLabel.setEnabled(is_enabled)
		cls.ui.dataPeakFromValue.setEnabled(is_enabled)
		cls.ui.dataPeakToValue.setEnabled(is_enabled)
		cls.ui.dataBackgroundFlag.setEnabled(is_enabled)
		cls.ui.tableWidget.setEnabled(is_enabled)
		
	def runSequenceLineEditEvent(cls):
		run_sequence = cls.ui.runSequenceLineEdit.text()
		oListRuns = RunSequenceBreaker(run_sequence)
		_new_runs = oListRuns.getFinalList()
		_old_runs = cls.loaded_list_of_runs
		_list_runs = np.unique(np.hstack([_old_runs, _new_runs]))
		o_load_and_sort_nxsdata = LoadAndSortNXSDataForSFcalculator(_list_runs)
		_big_table = o_load_and_sort_nxsdata.getTableData()
		if _big_table != [] :
			cls.big_table = _big_table
			cls.list_nxsdata_sorted = o_load_and_sort_nxsdata.getListNXSDataSorted()
			cls.loaded_list_of_runs = o_load_and_sort_nxsdata.getListOfRunsLoaded()
			cls.is_using_si_slits = o_load_and_sort_nxsdata.is_using_si_slits
			cls.fillGuiTable()
		else:
			info('No Files loaded!')
		cls.ui.runSequenceLineEdit.setText("")
		cls.checkGui()
		
	def fillGuiTable(cls):
		_fill_gui_object = FillSFGuiTable(parent=cls, table=cls.big_table, is_using_si_slits=cls.is_using_si_slits)
	
	def tableWidgetRightClick(cls):
		menu = QtGui.QMenu(cls)
		removeRow = menu.addAction("Delete Row")
		removeAll = menu.addAction("Clear Table")
		menu.addSeparator()
		displayMeta = menu.addAction("Display Metadata ...")
		action = menu.exec_(QtGui.QCursor.pos())
		
		if action == removeRow:
			cls.removeRow()
		elif action == removeAll:
			cls.removeAll()
		elif action  == displayMeta:
			cls.displayMetadata()
			
	def removeRow(cls):
		print 'removeRow'
		
	def removeAll(cls):
		print 'removeAll'
		
	def displayMetadata(cls):
		[row,col] = cls.getCurrentRowColumnSelected()
		list_nxsdata_sorted = cls.list_nxsdata_sorted
		_active_data = list_nxsdata_sorted[row].active_data
		_displayMeta = DisplayMetadata(cls.main_gui, _active_data)
		_displayMeta.show()
		
	def getCurrentRowColumnSelected(cls):
		rangeSelected = cls.ui.tableWidget.selectedRanges()
		col = rangeSelected[0].leftColumn()
		row = rangeSelected[0].topRow()
		return [row, col]
	
	def browseFile(cls):
		_filter = u'SF config (*.txt);;All (*.*)'
		fileSelector = QtGui.QFileDialog()
		fileSelector.setFileMode(QtGui.QFileDialog.AnyFile)
		fileSelector.setFilter(_filter)
		fileSelector.setViewMode(QtGui.QFileDialog.List)
		fileSelector.setDirectory(cls.main_gui.path_ascii)
		if (fileSelector.exec_()):
			file_name = str(fileSelector.selectedFiles()[0])
			if not os.path.isfile(file_name):
				touch(file_name)
			cls.displayConfigFile(file_name)
			cls.ui.sfFileNameLabel.setText(file_name)
		else:
			cls.ui.sfFileNameLabel.setText("N/A")
			
	def displayConfigFile(cls, file_name):
		data = import_ascii_file(file_name)
		if not data:
			data = 'EMPTY FILE'
		cls.ui.sfFileNamePreview.setPlainText(data)
		cls.ui.sfFileNamePreview.setEnabled(True)

	def loadingConfiguration(cls):
		_path = cls.main_gui.path_config
		filename = QtGui.QFileDialog.getOpenFileName(cls,
		                                            'Load SF Configuration File',
		                                            _path,
		                                            "XML files (*.xml);;All files (*.*)")
		
		if not(filename == ''):
			cls.main_gui.path_config = os.path.dirname(filename)
			status = cls.importConfiguration(filename)
			if status:
				cls.setWindowTitle(cls.window_title + filename)
			cls.checkGui()

	def savingConfiguration(cls):
		_path = cls.main_gui.path_config
		filename = QtGui.QFileDialog.getSaveFileName(cls,
		                                             'Save SF Configuration File',
		                                             _path,
		                                             "XML files (*.xml);;All files (*.*)")
		if not(filename == ''):
			cls.main_gui.path_config = os.path.dirname(filename)
			filename = makeSureFileHasExtension(filename)
			cls.exportConfiguration(filename)
			cls.setWindowTitle(cls.window_title + filename)
			
	def exportConfiguration(cls, filename):
		_configObject= CreateSFConfigXmlFile(parent=cls, filename=filename)
		
	def importConfiguration(cls, filename):
		_configObject = LoadSFConfigAndPopulateGUI(parent=cls, filename=filename)
		return _configObject.getLoadingStatus()
		
	def selectAutoTOF(cls):
		cls.manualTOFWidgetsEnabled(False)
	
	def selectManualTOF(cls):
		cls.manualTOFWidgetsEnabled(True)

	def manualTOFWidgetsEnabled(cls, status):
		cls.ui.TOFmanualFromLabel.setEnabled(status)
		cls.ui.TOFmanualFromUnitsValue.setEnabled(status)
		cls.ui.TOFmanualFromValue.setEnabled(status)
		cls.ui.TOFmanualToLabel.setEnabled(status)
		cls.ui.TOFmanualToUnitsValue.setEnabled(status)
		cls.ui.TOFmanualToValue.setEnabled(status)
		
	def tableWidgetCellSelected(cls, row, col):
		rangeSelected = QtGui.QTableWidgetSelectionRange(row, 0, row, 15)
		cls.ui.tableWidget.setRangeSelected(rangeSelected, True)
		cls.displaySelectedRow(row)
#		cls.updatePeakBackTofWidgets(row)
		
	def updatePeakBackTofWidgets(cls, row):
		_list_nxsdata_sorted = cls.list_nxsdata_sorted
		_nxsdata_row = _list_nxsdata_sorted[row]
		[peak1, peak2] = _nxsdata_row.active_data.peak
		cls.ui.dataPeakFromValue.setValue(int(peak1))
		cls.ui.dataPeakToValue.setValue(int(peak2))
		
		[back1, back2] = _nxsdata_row.active_data.back
		cls.ui.dataBackFromValue.setValue(int(back1))
		cls.ui.dataBackToValue.setValue(int(back2))

		[tof1, tof2] = _nxsdata_row.active_data.tof_range_auto
		[tof1ms, tof2ms] = convertTOF([tof1, tof2])
		cls.ui.TOFmanualFromValue.setText("%.2f"%float(tof1ms))
		cls.ui.TOFmanualToValue.setText("%.2f"%float(tof2ms))

	def displaySelectedRow(cls, row):
		_list_nxsdata_sorted = cls.list_nxsdata_sorted
		_nxsdata_row = _list_nxsdata_sorted[row]
		if _nxsdata_row is None:
			cls.loadSelectedNxsRuns(row)
		cls.displayPlot(_nxsdata_row, yt_plot=True, yi_plot=True)

	def loadSelectedNxsRuns(cls, row):
		list_runs = cls.getListOfRunsFromSelectedCell(row)
		cls.ui.tableWidget.item(row,0).text()
		is_auto_peak_finder = cls.isPeakOrBackFullyDefined(row=row)
		_loadNXData = LoadNXData(list_runs, is_auto_peak_finder=(not is_auto_peak_finder))
		_nxdata = _loadNXData.getNXData

	def getListOfRunsFromSelectedCell(cls, row):
		str_runs = str(cls.ui.tableWidget.item(row,0).text())
		list_runs = str_runs.split(',')
		return list_runs

	def isPeakOrBackFullyDefined(cls, row=-1):
		if row == -1:
			return False
		for col in range(10,14):
			_value = cls.ui.tableWidget.item(row, col).text()
			if _value == 'N/A':
				return False
		return True

	def displayPlot(cls, nxsdata=None, yt_plot=True, yi_plot=True):
		cls.clearPlot(yt_plot=True, yi_plot=True)
		if nxsdata is None:
			return
		if yt_plot:
			pass
		if yi_plot:
			pass
		
		

	def clearPlot(cls, yt_plot=True, yi_plot=True):
		if yt_plot:
			cls.ui.yt_plot.clear()
			cls.ui.yt_plot.draw()
		if yi_plot:
			cls.ui.yi_plot.clear()
			cls.ui.yi_plot.draw()
