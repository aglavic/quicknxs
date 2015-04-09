from PyQt4 import QtGui, QtCore
from sf_calculator_interface import Ui_MainWindow
from run_sequence_breaker import RunSequenceBreaker
from mantid.simpleapi import *
from load_and_sort_nxsdata_for_sf_calculator import LoadAndSortNXSDataForSFcalculator
from display_metadata import DisplayMetadata
from logging import info
from utilities import touch, import_ascii_file, makeSureFileHasExtension, convertTOF, str2bool
from create_sf_config_xml_file import CreateSFConfigXmlFile
from load_sf_config_and_populate_gui import LoadSFConfigAndPopulateGUI
from fill_sf_gui_table import FillSFGuiTable
from load_nx_data import LoadNXData
from sf_single_plot_click import SFSinglePlotClick

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
	current_table_row_selected = -1
	current_loaded_file = 'tmp.xml'
	time_click1 = -1
	
	def __init__(cls, main_gui, parent=None):
		cls.main_gui = main_gui
		QtGui.QMainWindow.__init__(cls)
		cls._open_instances.append(cls)
		cls.ui = Ui_MainWindow()
		cls.ui.setupUi(cls)
		cls.initCurrentLoadedFile()
		cls.initGui()
		cls.checkGui()
		cls.initConnections()
		
	def initConnections(cls):
		cls.ui.yt_plot.singleClick.connect(cls.single_yt_plot)
		cls.ui.yi_plot.singleClick.connect(cls.single_yi_plot)
		
	def initGui(cls):
		palette = QtGui.QPalette()
		palette.setColor(QtGui.QPalette.Foreground, colors.VALUE_BAD)
		cls.ui.back1_error.setPalette(palette)
		cls.ui.back2_error.setPalette(palette)
		cls.ui.peak1_error.setPalette(palette)
		cls.ui.peak2_error.setPalette(palette)
		cls.ui.error_label.setPalette(palette)
	
	def initCurrentLoadedFile(cls):
		_current_loaded_file = cls.current_loaded_file
		_home_path = os.path.expanduser('~')
		cls.current_loaded_file = _home_path + '/' +  _current_loaded_file
	
	def checkGui(cls):
		if (cls.loaded_list_of_runs != []) or (cls.big_table != None):
			wdg_enabled = True
		else:
			wdg_enabled = False
			cls.setWindowTitle(cls.window_title + cls.current_loaded_file)
		cls.enabledWidgets(wdg_enabled)
		cls.testPeakBackErrorWidgets()
		cls.ui.actionSavingAsConfiguration.setEnabled(wdg_enabled)
		cls.ui.actionSavingConfiguration.setEnabled(wdg_enabled)
		cls.ui.tableWidget.setEnabled(wdg_enabled)
		
	def fileHasBeenModified(cls):
		dialog_title = cls.window_title + cls.current_loaded_file
		new_dialog_title = dialog_title + '*'
		cls.setWindowTitle(new_dialog_title)
		
	def resetFileHasBeenModified(cls):
		dialog_title = cls.window_title + cls.current_loaded_file
		cls.setWindowTitle(dialog_title)
		
	def single_yt_plot(cls, is_pan_or_zoom_activated):
		SFSinglePlotClick(cls, 'yt', is_pan_or_zoom_activated = is_pan_or_zoom_activated)
		
	def single_yi_plot(cls, is_pan_or_zoom_activated):
		SFSinglePlotClick(cls, 'yi', is_pan_or_zoom_activated = is_pan_or_zoom_activated)
				
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
		cls.ui.incidentMediumComboBox.setEnabled(is_enabled)
		cls.ui.dataTOFautoMode.setEnabled(is_enabled)
		cls.ui.dataTOFmanualMode.setEnabled(is_enabled)
		if is_enabled:
			cls.manualTOFWidgetsEnabled(cls.ui.dataTOFmanualMode.isChecked())
		else:
			cls.manualTOFWidgetsEnabled(False)
		
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
		cls.tableWidgetCellSelected(0, 0)
		cls.fileHasBeenModified()					
		
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
		_row = cls.current_table_row_selected
		_list_nxsdata_sorted = cls.list_nxsdata_sorted
		nbr_entries = len(_list_nxsdata_sorted)
		if nbr_entries <= 1:
			cls.removeAll()
		else:
			cls.removeRowNumber(_row)
		cls.selectNewRowAfterRemovingRow()
		cls.fillGuiTable()
		cls.tableWidgetCellSelected(cls.current_table_row_selected, 0)
		cls.checkGui()
		
	def selectNewRowAfterRemovingRow(cls):
		_row = cls.current_table_row_selected
		_list_nxsdata_sorted = cls.list_nxsdata_sorted
		nbr_entries = len(_list_nxsdata_sorted)
		
		if nbr_entries == 0:
			cls.current_table_row_selected = -1
		elif nbr_entries == 1:
			cls.current_table_row_selected = 0
		else:
			if _row == nbr_entries:
				cls.current_table_row_selected -= 1
			elif _row < nbr_entries:
				cls.current_table_row_selected = _row
			else:
				cls.current_table_row_selected -= 1
			
	def removeRowNumber(cls, row):
		_big_table  = cls.big_table
		_list_nxsdata_sorted = cls.list_nxsdata_sorted
		nbr_entries = len(_list_nxsdata_sorted)
		
		new_big_table = np.delete(_big_table, row, 0)
		cls.big_table = new_big_table
		
		del(_list_nxsdata_sorted[row])
		cls.list_nxsdata_sorted = _list_nxsdata_sorted
		
	def removeAll(cls):
		cls.big_table = None
		cls.list_nxsdata_sorted = []
		cls.selectNewRowAfterRemovingRow()
		cls.fillGuiTable()
		cls.tableWidgetCellSelected(cls.current_table_row_selected, 0)
		cls.checkGui()
		
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
			cls.fileHasBeenModified()			
			
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
			cls.current_loaded_file = filename
			cls.resetFileHasBeenModified()			
			cls.main_gui.path_config = os.path.dirname(filename)
			status = cls.importConfiguration(filename)
			if status:
				cls.setWindowTitle(cls.window_title + filename)
			cls.checkGui()
			cls.tableWidgetCellSelected(0, 0)

	def savingAsConfiguration(cls):
		_path = cls.main_gui.path_config
		filename = QtGui.QFileDialog.getSaveFileName(cls,
		                                             'Save SF Configuration File',
		                                             _path,
		                                             "XML files (*.xml);;All files (*.*)")
		if not(filename == ''):
			cls.current_loaded_file = filename
			cls.resetFileHasBeenModified()
			cls.main_gui.path_config = os.path.dirname(filename)
			filename = makeSureFileHasExtension(filename)
			cls.exportConfiguration(filename)
			cls.setWindowTitle(cls.window_title + filename)
			
	def savingConfiguration(cls):
		filename = cls.current_loaded_file
		cls.resetFileHasBeenModified()
		cls.main_gui.path_config = os.path.dirname(filename)
		filename = makeSureFileHasExtension(filename)
		cls.exportConfiguration(filename)
		cls.setWindowTitle(cls.window_title + filename)
					
	def exportConfiguration(cls, filename):
		_configObject= CreateSFConfigXmlFile(parent=cls, filename=filename)
		
	def importConfiguration(cls, filename):
		_configObject = LoadSFConfigAndPopulateGUI(parent=cls, filename=filename)
		return _configObject.getLoadingStatus()
		
	def displaySelectedTOFandUpdateTable(cls, mode='auto'):
		_list_nxsdata_sorted = cls.list_nxsdata_sorted
		_nxdata  = _list_nxsdata_sorted[cls.current_table_row_selected]
		if mode == 'auto':
			[tof1, tof2] = _nxdata.active_data.tof_range_auto
		else:
			[tof1, tof2] = _nxdata.active_data.tof_range
		tof1 = float(tof1) * 1e-3
		tof2 = float(tof2) * 1e-3
		
		cls.updateTableWithTOFinfos(tof1, tof2)
		cls.ui.TOFmanualFromValue.setText("%.2f"%tof1)
		cls.ui.TOFmanualToValue.setText("%.2f"%tof2)
	
	def tofValidation(cls, tof_auto_switch, tof1, tof2):	
		cls.ui.dataTOFautoMode.setChecked(tof_auto_switch)
		cls.ui.dataTOFmanualMode.setChecked(not tof_auto_switch)
		cls.manualTOFWidgetsEnabled(not tof_auto_switch)
		cls.ui.TOFmanualFromValue.setText("%.2f"%tof1)
		cls.ui.TOFmanualToValue.setText("%.2f"%tof2)
		cls.manualTOFtextFieldValidated()
	
	def saveManualTOFmode(cls):
		tof1 = float(cls.ui.TOFmanualFromValue.text())
		tof2 = float(cls.ui.TOFmanualToValue.text())
		tof_min = min([tof1, tof2])
		tof_max = max([tof1, tof2])
		_list_nxsdata_sorted = cls.list_nxsdata_sorted
		_nxdata  = _list_nxsdata_sorted[cls.current_table_row_selected]
		tof1 = 1000 * tof_min
		tof2 = 1000 * tof_max
		_nxdata.active_data.tof_range = [tof1, tof2]
		_nxdata.active_data.tof_auto_flag = True
		_list_nxsdata_sorted[cls.current_table_row_selected] = _nxdata
		cls.list_nxsdata_sorted = _list_nxsdata_sorted

	def selectAutoTOF(cls):
		cls.manualTOFWidgetsEnabled(False)
		cls.saveManualTOFmode()
		cls.saveTOFautoFlag(auto_flag = True)
		cls.displaySelectedTOFandUpdateTable(mode='auto')
		cls.displayPlot(row=cls.current_table_row_selected, yi_plot=False)
		cls.fileHasBeenModified()
	
	def saveTOFautoFlag(cls, auto_flag = False):
		_list_nxsdata_sorted = cls.list_nxsdata_sorted
		_nxdata  = _list_nxsdata_sorted[cls.current_table_row_selected]
		_nxdata.active_data.tof_auto_flag = auto_flag
		_list_nxsdata_sorted[cls.current_table_row_selected] = _nxdata
		cls.list_nxsdata_sorted = _list_nxsdata_sorted
		_big_table = cls.big_table
		_big_table[cls.current_table_row_selected, 16] = str(auto_flag)
		cls.big_table = _big_table
	
	def selectManualTOF(cls):
		cls.manualTOFWidgetsEnabled(True)
		cls.saveTOFautoFlag(auto_flag = False)
		cls.displaySelectedTOFandUpdateTable(mode='manual')
		cls.displayPlot(row=cls.current_table_row_selected, yi_plot=False)
		cls.fileHasBeenModified()

	def updateTableWithTOFinfos(cls, tof1_ms, tof2_ms):
		_row = cls.current_table_row_selected
		_item = QtGui.QTableWidgetItem("%.2f"%tof1_ms)
		_item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
		_brush_OK = QtGui.QBrush()
		_brush_OK.setColor(colors.VALUE_OK)			
		_item.setForeground(_brush_OK)
		cls.ui.tableWidget.setItem(_row, 14, _item)
		_item = QtGui.QTableWidgetItem("%.2f"%tof2_ms)
		_item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
		_brush_OK = QtGui.QBrush()
		_brush_OK.setColor(colors.VALUE_OK)			
		_item.setForeground(_brush_OK)
		cls.ui.tableWidget.setItem(_row, 15, _item)

	def manualTOFWidgetsEnabled(cls, status):
		cls.ui.TOFmanualFromLabel.setEnabled(status)
		cls.ui.TOFmanualFromUnitsValue.setEnabled(status)
		cls.ui.TOFmanualFromValue.setEnabled(status)
		cls.ui.TOFmanualToLabel.setEnabled(status)
		cls.ui.TOFmanualToUnitsValue.setEnabled(status)
		cls.ui.TOFmanualToValue.setEnabled(status)

	def manualTOFtextFieldValidated(cls):
		tof1 = float(cls.ui.TOFmanualFromValue.text())
		tof2 = float(cls.ui.TOFmanualToValue.text())
		cls.updateTableWithTOFinfos(tof1, tof2)
		
		tof_min = min([tof1, tof2]) * 1000
		tof_max = max([tof1, tof2]) * 1000
		_list_nxsdata_sorted = cls.list_nxsdata_sorted
		_nxdata  = _list_nxsdata_sorted[cls.current_table_row_selected]
		_nxdata.active_data.tof_range = [tof_min, tof_max]
		_list_nxsdata_sorted[cls.current_table_row_selected] = _nxdata
		cls.list_nxsdata_sorted = _list_nxsdata_sorted
		cls.displayPlot(row=cls.current_table_row_selected, yi_plot=False)
		cls.fileHasBeenModified()
		
	def tableWidgetCellSelected(cls, row, col):
		cls.current_table_row_selected = row
		rangeSelected = QtGui.QTableWidgetSelectionRange(row, 0, row, 15)
		cls.ui.tableWidget.setRangeSelected(rangeSelected, True)
		cls.displaySelectedRow(row)
		cls.updateTableWidgetPeakBackTof(row)
		cls.displayPlot(row, yt_plot=True, yi_plot=True)

	def incidentMediumComboBoxChanged(cls):
		cls.fileHasBeenModified()
		
	def updateTableWidgetPeakBackTof(cls, row, force_spinbox_source=False):
		if row == -1:
			return
		is_peak_back_fully_defined = cls.isPeakOrBackFullyDefined(row=row)
		_list_nxsdata_sorted = cls.list_nxsdata_sorted
		_nxdata  = _list_nxsdata_sorted[row]
		if (not is_peak_back_fully_defined) or force_spinbox_source:
			cls.updatePeakBackTofWidgets(row)
			_at_least_one_bad = False

			[peak1, peak2] = _nxdata.active_data.peak
			[back1, back2]  = _nxdata.active_data.back
			
			_item = QtGui.QTableWidgetItem(peak1)
			_item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
			if back1 > peak1:
				_brush_BAD = QtGui.QBrush()
				_brush_BAD.setColor(colors.VALUE_BAD)
				_item.setForeground(_brush_BAD)
				_font = QtGui.QFont()
				_font.setBold(True)
				_font.setItalic(True)
				_item.setFont(_font)
				_at_least_one_bad = True
			else:
				_brush_OK = QtGui.QBrush()
				_brush_OK.setColor(colors.VALUE_OK)
				_item.setForeground(_brush_OK)
			cls.ui.tableWidget.setItem(row, 10, _item)
			
			_item = QtGui.QTableWidgetItem(peak2)
			_item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
			if back2 < peak2:
				_brush_BAD = QtGui.QBrush()
				_brush_BAD.setColor(colors.VALUE_BAD)
				_item.setForeground(_brush_BAD)
				_font = QtGui.QFont()
				_font.setBold(True)
				_font.setItalic(True)
				_item.setFont(_font)
				_at_least_one_bad = True
			else:
				_brush_OK = QtGui.QBrush()
				_brush_OK.setColor(colors.VALUE_OK)
				_item.setForeground(_brush_OK)
			cls.ui.tableWidget.setItem(row, 11, _item)
			
			_item = QtGui.QTableWidgetItem(back1)
			_item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
			if back1 > peak1:
				_brush_BAD = QtGui.QBrush()				
				_brush_BAD.setColor(colors.VALUE_BAD)
				_font = QtGui.QFont()
				_font.setBold(True)
				_font.setItalic(True)
				_item.setFont(_font)
				_item.setForeground(_brush_BAD)
			else:
				_brush_OK = QtGui.QBrush()
				_brush_OK.setColor(colors.VALUE_OK)
				_item.setForeground(_brush_OK)
			cls.ui.tableWidget.setItem(row, 12, _item)

			_item = QtGui.QTableWidgetItem(back2)
			_item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
			if back2 < peak2:
				_brush_BAD = QtGui.QBrush()
				_brush_BAD.setColor(colors.VALUE_BAD)
				_font = QtGui.QFont()
				_font.setBold(True)
				_font.setItalic(True)
				_item.setFont(_font)
				_item.setForeground(_brush_BAD)
			else:
				_brush_OK = QtGui.QBrush()
				_brush_OK.setColor(colors.VALUE_OK)
				_item.setForeground(_brush_OK)
			cls.ui.tableWidget.setItem(row, 13, _item)

			tof_auto_flag = _nxdata.active_data.tof_auto_flag
			cls.ui.dataTOFautoMode.setChecked(tof_auto_flag)
			cls.ui.dataTOFmanualMode.setChecked(not tof_auto_flag)
			if tof_auto_flag:
				[tof1, tof2] = _nxdata.active_data.tof_range_auto
			else:
				[tof1, tof2] = _nxdata.active_data.tof_range

			if float(tof1) > 1000:
				tof1 = "%.2f" % (float(tof1)/1000)
				tof2 = "%.2f" % (float(tof2)/1000)
			_item = QtGui.QTableWidgetItem(tof1)
			_item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
			_brush_OK = QtGui.QBrush()
			_brush_OK.setColor(colors.VALUE_OK)			
			_item.setForeground(_brush_OK)
			cls.ui.tableWidget.setItem(row, 14, _item)
			_item = QtGui.QTableWidgetItem(tof2)
			_item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
			_brush_OK = QtGui.QBrush()
			_brush_OK.setColor(colors.VALUE_OK)			
			_item.setForeground(_brush_OK)
			cls.ui.tableWidget.setItem(row, 15, _item)
			
			_item = cls.ui.tableWidget.item(row,0)
			if _at_least_one_bad:
				_brush_BAD = QtGui.QBrush()
				_brush_BAD.setColor(colors.VALUE_BAD)
				_font = QtGui.QFont()
				_font.setBold(True)
				_font.setItalic(True)
				_item.setFont(_font)
				_item.setForeground(_brush_BAD)
			else:
				_brush_OK = QtGui.QBrush()
				_brush_OK.setColor(colors.VALUE_OK)			
				_item.setForeground(_brush_OK)
			cls.ui.tableWidget.setItem(row,0,_item)

		else:
			peak1 = cls.ui.tableWidget.item(row, 10).text()
			peak2 = cls.ui.tableWidget.item(row, 11).text()
			back1 = cls.ui.tableWidget.item(row, 12).text()
			back2 = cls.ui.tableWidget.item(row, 13).text()
			tof1 = cls.ui.tableWidget.item(row, 14).text()
			tof2 = cls.ui.tableWidget.item(row, 15).text()
			peak = [peak1, peak2]
			back = [back1, back2]
			if float(tof1) < 1000:
				tof1 = str(float(tof1)*1000)
				tof2 = str(float(tof2)*1000)
			tof = [tof1, tof2]
			_nxdata.active_data.peak = peak
			_nxdata.active_data.back = back
			_nxdata.active_data.tof_range_auto = tof

			_big_table = cls.big_table
			tof_auto_flag = str2bool(_big_table[row, 16])
			_nxdata.active_data.tof_auto_flag = tof_auto_flag
			cls.ui.dataTOFautoMode.setChecked(tof_auto_flag)
			cls.ui.dataTOFmanualMode.setChecked(not tof_auto_flag)

			_list_nxsdata_sorted[row] = _nxdata
			cls.list_nxsdata_sorted = _list_nxsdata_sorted
			cls.updatePeakBackTofWidgets(row)
		
	def updatePeakBackTofWidgets(cls, row):
		_list_nxsdata_sorted = cls.list_nxsdata_sorted
		_nxsdata_row = _list_nxsdata_sorted[row]
		if _nxsdata_row == None:
			return
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
		if _list_nxsdata_sorted == []:
			cls.clearPlot()
			return
		_nxsdata_row = _list_nxsdata_sorted[row]
		if _nxsdata_row is None:
			cls.loadSelectedNxsRuns(row)

	def loadSelectedNxsRuns(cls, row):
		list_runs = cls.getListOfRunsFromSelectedCell(row)
		cls.ui.tableWidget.item(row,0).text()
		is_auto_peak_finder = cls.isPeakOrBackFullyDefined(row=row)
		_loadNXData = LoadNXData(list_runs, is_auto_peak_finder=(not is_auto_peak_finder))
		_nxdata = _loadNXData.getNXData()
		_list_nxsdata_sorted = cls.list_nxsdata_sorted
		_list_nxsdata_sorted[row] = _nxdata
		cls.list_nxsdata_sorted = _list_nxsdata_sorted

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

	def displayPlot(cls, row=-1, yt_plot=True, yi_plot=True):
		if row == -1:
			cls.clearPlot()
			return
		list_nxsdata_sorted = cls.list_nxsdata_sorted
		nxsdata = list_nxsdata_sorted[row]
		cls.clearPlot(yt_plot=yt_plot, yi_plot=yi_plot)
		if nxsdata is None:
			return
		if yt_plot:
			cls.plotYT(nxsdata)
		if yi_plot:
			cls.plotYI(nxsdata)
			
	def plotYT(cls, nxsdata):
		ytof = nxsdata.active_data.ytofdata
		tof_min_ms = float(nxsdata.active_data.tof_axis_auto_with_margin[0])/1000
		tof_max_ms = float(nxsdata.active_data.tof_axis_auto_with_margin[-1])/1000
		cls.ui.yt_plot.imshow(ytof, log=True, aspect='auto',origin='lower',extent=[tof_min_ms, tof_max_ms, 0, nxsdata.active_data.y.shape[0]-1])
		cls.ui.yt_plot.set_xlabel(u't (ms)')
		cls.ui.yt_plot.set_ylabel(u'y (pixel)')
#		cls.ui.yt_plot.canvas.ax.set_yscale('log')

		[peak1, peak2] = nxsdata.active_data.peak
		peak1 = int(peak1)
		peak2 = int(peak2)
		
		[back1, back2] = nxsdata.active_data.back
		back1 = int(back1)
		back2 = int(back2)
		
		if cls.ui.dataTOFautoMode.isChecked():
			[tof1, tof2] = nxsdata.active_data.tof_range_auto
		else:
			[tof1, tof2] = nxsdata.active_data.tof_range
		tof1 = float(tof1) * 1e-3
		tof2 = float(tof2) * 1e-3

		cls.ui.yt_plot.canvas.ax.axvline(tof1, color=colors.TOF_SELECTION_COLOR)
		cls.ui.yt_plot.canvas.ax.axvline(tof2, color=colors.TOF_SELECTION_COLOR)
		
		cls.ui.yt_plot.canvas.ax.axhline(peak1, color=colors.PEAK_SELECTION_COLOR)
		cls.ui.yt_plot.canvas.ax.axhline(peak2, color=colors.PEAK_SELECTION_COLOR)
		
		cls.ui.yt_plot.canvas.ax.axhline(back1, color=colors.BACK_SELECTION_COLOR)
		cls.ui.yt_plot.canvas.ax.axhline(back2, color=colors.BACK_SELECTION_COLOR)

		cls.ui.yt_plot.canvas.draw()
	
	def plotYI(cls, nxsdata):
		ycountsdata = nxsdata.active_data.ycountsdata
		xaxis = range(len(ycountsdata))
		cls.ui.yi_plot.canvas.ax.plot(ycountsdata, xaxis)
		cls.ui.yi_plot.canvas.ax.set_xlabel(u'counts')
		cls.ui.yi_plot.canvas.ax.set_ylabel(u'y (pixel)')
		cls.ui.yi_plot.canvas.ax.set_xscale('log')

		[peak1, peak2] = nxsdata.active_data.peak
		peak1 = int(peak1)
		peak2 = int(peak2)
		
		[back1, back2] = nxsdata.active_data.back
		back1 = int(back1)
		back2 = int(back2)
		
		cls.ui.yi_plot.canvas.ax.axhline(peak1, color=colors.PEAK_SELECTION_COLOR)
		cls.ui.yi_plot.canvas.ax.axhline(peak2, color=colors.PEAK_SELECTION_COLOR)
		
		cls.ui.yi_plot.canvas.ax.axhline(back1, color=colors.BACK_SELECTION_COLOR)
		cls.ui.yi_plot.canvas.ax.axhline(back2, color=colors.BACK_SELECTION_COLOR)

		cls.ui.yi_plot.canvas.draw()
		
	def clearPlot(cls, yt_plot=True, yi_plot=True):
		if yt_plot:
			cls.ui.yt_plot.clear()
			cls.ui.yt_plot.draw()
		if yi_plot:
			cls.ui.yi_plot.clear()
			cls.ui.yi_plot.draw()

	def peak1SpinBoxValueChanged(cls):
		cls.peakBackSpinBoxValueChanged('peak1')

	def peak2SpinBoxValueChanged(cls):
		cls.peakBackSpinBoxValueChanged('peak2')

	def back1SpinBoxValueChanged(cls):
		cls.peakBackSpinBoxValueChanged('back1')

	def back2SpinBoxValueChanged(cls):
		cls.peakBackSpinBoxValueChanged('back2')

	def peakBackSpinBoxValueChanged(cls, type):
		if 'peak' in type:
			peak1 = cls.ui.dataPeakFromValue.value()
			peak2 = cls.ui.dataPeakToValue.value()
			peak_min = min([peak1, peak2])
			peak_max = max([peak1, peak2])

			if peak1 == peak_max:
				if type == 'peak1':
					cls.ui.dataPeakToValue.setFocus()
				else:
					cls.ui.dataPeakFromValue.setFocus()
				cls.ui.dataPeakFromValue.setValue(peak_min)
				cls.ui.dataPeakToValue.setValue(peak_max)
		
		if 'back' in type:
			back1 = cls.ui.dataBackFromValue.value()
			back2 = cls.ui.dataBackToValue.value()
			back_min = min([back1, back2])
			back_max = max([back1, back2])
			
			if back1 == back_max:
				if type == 'back1':
					cls.ui.dataBackToValue.setFocus()
				else:
					cls.ui.dataBackFromValue.setFocus()
				cls.ui.dataBackFromValue.setValue(back_min)
				cls.ui.dataBackToValue.setValue(back_max)
		
		cls.testPeakBackErrorWidgets()
		cls.updateNXSData(row=cls.current_table_row_selected, source='spinbox', type=type)
		cls.displayPlot(row=cls.current_table_row_selected, yt_plot=True, yi_plot=True)
		cls.fileHasBeenModified()
		
	def updateNXSData(cls, row=0, source='spinbox', type='peak1'):
		_list_nxsdata_sorted = cls.list_nxsdata_sorted
		_nxsdata_row = _list_nxsdata_sorted[row]
		if 'peak' in type:
			if source == 'spinbox':
				peak1 = str(cls.ui.dataPeakFromValue.value())
				peak2 = str(cls.ui.dataPeakToValue.value())
			else:
				peak1 = cls.ui.tableWidget.item(row, 10).text()
				peak2 = cls.u.tableWidget.item(row, 11).text()
			_nxsdata_row.active_data.peak = [peak1, peak2]
		else:
			if source == 'spinbox':
				back1 = str(cls.ui.dataBackFromValue.value())
				back2 = str(cls.ui.dataBackToValue.value())
			else:
				back1 = cls.ui.tableWidget.item(row, 12).text()
				back2 = cls.ui.tableWidget.item(row, 13).text()
			_nxsdata_row.active_data.back = [back1, back2]
		_list_nxsdata_sorted[row] = _nxsdata_row
		cls.list_nxsdata_sorted = _list_nxsdata_sorted
		cls.updateTableWidgetPeakBackTof(row, force_spinbox_source=(source == 'spinbox'))
		
	def dataPeakAndBackValidation(cls, with_plot_update=True):
		cls.peakBackSpinBoxValueChanged('peak')
		cls.peakBackSpinBoxValueChanged('back')
		cls.testPeakBackErrorWidgets()
	
	def attenuatorValueChanged(cls, value):
		cls.fileHasBeenModified()			
		