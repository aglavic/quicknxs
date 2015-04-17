from PyQt4 import QtGui, QtCore
from sf_calculator_interface import Ui_MainWindow
from run_sequence_breaker import RunSequenceBreaker
from mantid.simpleapi import *
from load_and_sort_nxsdata_for_sf_calculator import LoadAndSortNXSDataForSFcalculator
from display_metadata import DisplayMetadata
from logging import info
from utilities import touch, import_ascii_file, makeSureFileHasExtension, convertTOF, str2bool, output_2d_ascii_file, write_ascii_file
from create_sf_config_xml_file import CreateSFConfigXmlFile
from load_sf_config_and_populate_gui import LoadSFConfigAndPopulateGUI
from fill_sf_gui_table import FillSFGuiTable
from load_nx_data import LoadNXData
from sf_single_plot_click import SFSinglePlotClick
from check_sf_run_reduction_button_status import CheckSfRunReductionButtonStatus
from incident_medium_list_editor import IncidentMediumListEditor
from reduction_sf_calculator import ReductionSfCalculator
from init_sfcalculator_file_menu import InitSFCalculatorFileMenu
from reduced_sfcalculator_config_files_handler import ReducedSFCalculatorConfigFilesHandler
from sf_calculator_config_file_launcher import SFCalculatorConfigFileLauncher

import colors
import numpy as np
import os
import time

class SFcalculator(QtGui.QMainWindow):
	_open_instances = []
	main_gui = None
	data_list = []
	big_table = None
	big_table_status = None  # only a fully True table will validate the GO_REDUCTION button
	big_table_nxdata = []
	is_using_si_slits = False
	loaded_list_of_runs = []
	list_nxsdata_sorted = []
	window_title = 'SF Calculator - '
	current_table_row_selected = -1
	current_loaded_file = 'tmp.xml'
	time_click1 = -1
	bin_size = 200 #micros
	file_menu_action_list = []
	file_menu_object = None
	list_action = []
	reduced_files_loaded_object = None
	event_progressbar = None
	
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
		cls.ui.yt_plot.singleClick.connect(cls.singleYTPlot)
		cls.ui.yt_plot.toolbar.homeClicked.connect(cls.homeYtPlot)
		cls.ui.yt_plot.toolbar.exportClicked.connect(cls.exportYtPlot)
		cls.ui.yt_plot.leaveFigure.connect(cls.leaveYtPlot)
		
		cls.ui.yi_plot.singleClick.connect(cls.singleYIPlot)
		cls.ui.yi_plot.toolbar.homeClicked.connect(cls.homeYiPlot)
		cls.ui.yi_plot.toolbar.exportClicked.connect(cls.exportYiPlot)
		cls.ui.yi_plot.leaveFigure.connect(cls.leaveYiPlot)
		cls.ui.yi_plot.logtogx.connect(cls.logxToggleYiPlot)
		
	def initGui(cls):
		palette = QtGui.QPalette()
		palette.setColor(QtGui.QPalette.Foreground, colors.VALUE_BAD)
		cls.ui.back1_error.setPalette(palette)
		cls.ui.back2_error.setPalette(palette)
		cls.ui.peak1_error.setPalette(palette)
		cls.ui.peak2_error.setPalette(palette)
		cls.ui.error_label.setPalette(palette)
		cls.initFileMenu()
		cls.reduced_files_loaded_object = ReducedSFCalculatorConfigFilesHandler(cls)
		cls.initConfigGui()
		cls.event_progressbar = QtGui.QProgressBar(cls.ui.statusbar)
		cls.event_progressbar.setMinimumSize(20,14)
		cls.event_progressbar.setMaximumSize(140,100)
		cls.ui.statusbar.addPermanentWidget(cls.event_progressbar)
		cls.event_progressbar.setVisible(False)

	def updateProgressBar(cls, progress):
		cls.event_progressbar.setVisible(True)
		cls.event_progressbar.setValue(progress*100)
		cls.event_progressbar.update()
		if progress == 1:
			time.sleep(2)
			cls.event_progressbar.setVisible(False)
			cls.event_progressbar.setValue(0)
			cls.event_progressbar.update()

	def initConfigGui(cls):
		from quicknxs.config import reflsfcalculatorlastloadedfiles
		reflsfcalculatorlastloadedfiles.switch_config('config_files')
		if reflsfcalculatorlastloadedfiles.config_files_path != '':
			cls.main_gui.path_config =  reflsfcalculatorlastloadedfiles.config_files_path
		
	def initFileMenu(cls):
		cls.file_menu_object = InitSFCalculatorFileMenu(cls)
		
	def launchConfigFile1(cls):
		SFCalculatorConfigFileLauncher(cls, 0)
	def launchConfigFile2(cls):
		SFCalculatorConfigFileLauncher(cls, 1)
	def launchConfigFile3(cls):
		SFCalculatorConfigFileLauncher(cls, 2)
	def launchConfigFile4(cls):
		SFCalculatorConfigFileLauncher(cls, 3)
	def launchConfigFile5(cls):
		SFCalculatorConfigFileLauncher(cls, 4)
	def launchConfigFile6(cls):
		SFCalculatorConfigFileLauncher(cls, 5)
	def launchConfigFile7(cls):
		SFCalculatorConfigFileLauncher(cls, 6)
	def launchConfigFile8(cls):
		SFCalculatorConfigFileLauncher(cls, 7)
	def launchConfigFile9(cls):
		SFCalculatorConfigFileLauncher(cls, 8)
	def launchConfigFile10(cls):
		SFCalculatorConfigFileLauncher(cls, 9)
		
	def logxToggleYiPlot(cls, checked):
		row = cls.current_table_row_selected
		list_nxsdata = cls.list_nxsdata_sorted
		if list_nxsdata == []:
			return
		data = list_nxsdata[row]
		if checked == 'log':
			isLog = True
		else:
			isLog = False
		data.active_data.all_plot_axis.is_yi_xlog = isLog
		list_nxsdata[row] = data
		cls.list_nxsdata_sorted = list_nxsdata
	
	def leaveYtPlot(cls):
		row = cls.current_table_row_selected
		list_nxsdata = cls.list_nxsdata_sorted
		if list_nxsdata == []:
			return
		data = list_nxsdata[row]
		[xmin,xmax] = cls.ui.yt_plot.canvas.ax.xaxis.get_view_interval()
		[ymin,ymax] = cls.ui.yt_plot.canvas.ax.yaxis.get_view_interval()
		cls.ui.yt_plot.canvas.ax.xaxis.set_data_interval(xmin, xmax)
		cls.ui.yt_plot.canvas.ax.yaxis.set_data_interval(ymin, ymax)
		cls.ui.yt_plot.draw()
		data.active_data.all_plot_axis.yt_view_interval = [xmin, xmax, ymin, ymax]
		list_nxsdata[row] = data
		cls.list_nxsdata_sorted = list_nxsdata
	
	def leaveYiPlot(cls):
		row = cls.current_table_row_selected
		list_nxsdata = cls.list_nxsdata_sorted
		if list_nxsdata == []:
			return
		data = list_nxsdata[row]
		[xmin,xmax] = cls.ui.yi_plot.canvas.ax.xaxis.get_view_interval()
		[ymin,ymax] = cls.ui.yi_plot.canvas.ax.yaxis.get_view_interval()
		cls.ui.yi_plot.canvas.ax.xaxis.set_data_interval(xmin, xmax)
		cls.ui.yi_plot.canvas.ax.yaxis.set_data_interval(ymin, ymax)
		cls.ui.yi_plot.draw()
		data.active_data.all_plot_axis.yi_view_interval = [xmin, xmax, ymin, ymax]
		list_nxsdata[row] = data
		cls.list_nxsdata_sorted = list_nxsdata
	
	def exportYtPlot(cls):
		row = cls.current_table_row_selected
		list_nxsdata_sorted = cls.list_nxsdata_sorted
		_data = list_nxsdata_sorted[row]
		_active_data = _data.active_data
		run_number = _active_data.run_number
		default_filename = 'REFL_' + run_number + '_2dPxVsTof.txt'
		path = cls.main_gui.path_ascii
		default_filename = path + '/' + default_filename
		filename = QtGui.QFileDialog.getSaveFileName(cls, 'Create 2D Pixel VS TOF', default_filename)
		
		if str(filename).strip() == '':
			info('User Canceled Outpout ASCII')
			return
		  
		cls.main_gui.path_ascii = os.path.dirname(filename)
		image = _active_data.ytofdata
		output_2d_ascii_file(filename, image)
	
	def exportYiPlot(cls):
		row = cls.current_table_row_selected
		list_nxsdata = cls.list_nxsdata_sorted
		_data = list_nxsdata[row]
		_active_data = _data.active_data
		run_number = _active_data.run_number
		default_filename = 'REFL_' + run_number + '_rpx.txt'
		path = cls.main_gui.path_ascii
		default_filename = path + '/' + default_filename
		filename = QtGui.QFileDialog.getSaveFileName(cls, 'Create Counts vs Pixel ASCII File', default_filename)
		
		if str(filename).strip() == '':
			info('User Canceled Output ASCII')
			return
		
		cls.main_gui.path_ascii = os.path.dirname(filename)
	      
		ycountsdata = _active_data.ycountsdata
		pixelaxis = range(len(ycountsdata))
		
		text = ['#Counts vs Pixels','#Pixel - Counts']
		sz = len(pixelaxis)
		for i in range(sz):
			_line = str(pixelaxis[i]) + ' ' + str(ycountsdata[i])
			text.append(_line)
		write_ascii_file(filename, text)
		
	def homeYtPlot(cls):
		[xmin, xmax, ymin, ymax] = cls.ui.yt_plot.toolbar.home_settings
		cls.ui.yt_plot.canvas.ax.set_xlim([xmin, xmax])
		cls.ui.yt_plot.canvas.ax.set_ylim([ymin, ymax])
		cls.ui.yt_plot.canvas.draw()
	
	def homeYiPlot(cls):
		[xmin, xmax, ymin, ymax] = cls.ui.yi_plot.toolbar.home_settings
		cls.ui.yi_plot.canvas.ax.set_xlim([xmin, xmax])
		cls.ui.yi_plot.canvas.ax.set_ylim([ymin, ymax])
		cls.ui.yi_plot.canvas.draw()
	
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
		cls.testPeakBackErrorWidgets()
		cls.ui.actionSavingAsConfiguration.setEnabled(wdg_enabled)
		cls.ui.actionSavingConfiguration.setEnabled(wdg_enabled)
		cls.ui.tableWidget.setEnabled(wdg_enabled)
		cls.checkRunReductionButton()
		cls.enabledWidgets(wdg_enabled)

	def checkRunReductionButton(cls):
		_check_status_object = CheckSfRunReductionButtonStatus(parent=cls)
		_is_everything_ok_to_go = _check_status_object.isEverythingReady()
		cls.ui.generateSFfileButton.setEnabled(_is_everything_ok_to_go)
		
	def fileHasBeenModified(cls):
		dialog_title = cls.window_title + cls.current_loaded_file
		new_dialog_title = dialog_title + '*'
		cls.setWindowTitle(new_dialog_title)
		cls.checkGui()
		
	def resetFileHasBeenModified(cls):
		dialog_title = cls.window_title + cls.current_loaded_file
		cls.setWindowTitle(dialog_title)
		
	def singleYTPlot(cls, is_pan_or_zoom_activated):
		SFSinglePlotClick(cls, 'yt', is_pan_or_zoom_activated = is_pan_or_zoom_activated)
		
	def singleYIPlot(cls, is_pan_or_zoom_activated):
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
		cls.ui.toolButton.setEnabled(is_enabled)
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
		o_load_and_sort_nxsdata = LoadAndSortNXSDataForSFcalculator(_list_runs, parent=cls)
		_big_table = o_load_and_sort_nxsdata.getTableData()
		if _big_table != [] :
			cls.big_table = _big_table
			cls.list_nxsdata_sorted = o_load_and_sort_nxsdata.getListNXSDataSorted()
			cls.loaded_list_of_runs = o_load_and_sort_nxsdata.getListOfRunsLoaded()
			cls.is_using_si_slits = o_load_and_sort_nxsdata.is_using_si_slits
			cls.fillGuiTable()
			cls.ui.runSequenceLineEdit.setText("")
			cls.checkGui()
			cls.tableWidgetCellSelected(0, 0)
			cls.fileHasBeenModified()					
		else:
			ret = QtGui.QMessageBox.information(cls, "No Files Loaded!","Check The list of runs")
#			info('No Files loaded!')
		
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
		_selection = cls.ui.tableWidget.selectedRanges()[0]
		_row = _selection.topRow()
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
		cls.loaded_list_of_runs = []
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
			cls.loadingConfigurationFileDefined(filename)
			
	def loadingConfigurationFileDefined(cls, filename):
		cls.current_loaded_file = filename
		cls.resetFileHasBeenModified()			
		cls.main_gui.path_config = os.path.dirname(filename)
		status = cls.importConfiguration(filename)
		if status:
			cls.setWindowTitle(cls.window_title + filename)
		cls.tableWidgetCellSelected(0, 0)
		cls.checkGui()
		
		if cls.reduced_files_loaded_object is None:
			_reduced_files_loaded_object = ReducedSFCalculatorConfigFilesHandler(cls)
		else:
			_reduced_files_loaded_object = cls.reduced_files_loaded_object
		_reduced_files_loaded_object.addFile(filename)
		_reduced_files_loaded_object.updateGui()
		cls.reduced_files_loaded_object = _reduced_files_loaded_object

	def savingConfiguration(cls):
		filename = cls.current_loaded_file
		cls.savingConfigurationFileDefined(filename)

	def savingAsConfiguration(cls):
		_path = cls.main_gui.path_config
		filename = QtGui.QFileDialog.getSaveFileName(cls,
		                                             'Save SF Configuration File',
		                                             _path,
		                                             "XML files (*.xml);;All files (*.*)")
		if not(filename == ''):
			cls.current_loaded_file = filename
			cls.savingConfigurationFileDefined(filename)
			
	def savingConfigurationFileDefined(cls, filename):
		cls.resetFileHasBeenModified()
		cls.main_gui.path_config = os.path.dirname(filename)
		filename = makeSureFileHasExtension(filename)
		cls.exportConfiguration(filename)
		cls.setWindowTitle(cls.window_title + filename)
		if cls.reduced_files_loaded_object is None:
			_reduced_files_loaded_object = ReducedConfigFilesHandler(cls)
		else:
			_reduced_files_loaded_object = cls.reduced_files_loaded_object
		_reduced_files_loaded_object.addFile(filename)
		_reduced_files_loaded_object.updateGui()
		cls.reduced_files_loaded_object = _reduced_files_loaded_object
								
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
	
	def tofValidation(cls, tof_auto_switch, tof1, tof2, with_plot_update=True):	
		cls.ui.dataTOFautoMode.setChecked(tof_auto_switch)
		cls.ui.dataTOFmanualMode.setChecked(not tof_auto_switch)
		cls.manualTOFWidgetsEnabled(not tof_auto_switch)
		cls.ui.TOFmanualFromValue.setText("%.2f"%tof1)
		cls.ui.TOFmanualToValue.setText("%.2f"%tof2)
		cls.manualTOFtextFieldValidated(with_plot_update=with_plot_update)
	
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
		'''update all the rows that have the same lambda requested 
		'''
		list_row = cls.getListRowWithSameLambda()
		for index, _row in enumerate(list_row):
			if index == 0:
				color = cls.ui.tableWidget.item(_row, 0).backgroundColor()
			_item = QtGui.QTableWidgetItem("%.2f"%tof1_ms)
			_item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
			_brush_OK = QtGui.QBrush()
			_brush_OK.setColor(colors.VALUE_OK)			
			_item.setForeground(_brush_OK)
			_item.setBackgroundColor(color)
			cls.ui.tableWidget.setItem(_row, 14, _item)
			_item = QtGui.QTableWidgetItem("%.2f"%tof2_ms)
			_item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
			_brush_OK = QtGui.QBrush()
			_brush_OK.setColor(colors.VALUE_OK)			
			_item.setForeground(_brush_OK)
			_item.setBackgroundColor(color)
			cls.ui.tableWidget.setItem(_row, 15, _item)

	def getListRowWithSameLambda(cls):
		_row = cls.current_table_row_selected
		_lambda_requested = cls.ui.tableWidget.item(_row,5).text()
		nbr_row = cls.ui.tableWidget.rowCount()
		list_row = []
		for i in range(nbr_row):
			_lambda_to_compare_with = cls.ui.tableWidget.item(i, 5).text()
			if _lambda_to_compare_with == _lambda_requested:
				list_row.append(i)
		return list_row

	def manualTOFWidgetsEnabled(cls, status):
		cls.ui.TOFmanualFromLabel.setEnabled(status)
		cls.ui.TOFmanualFromUnitsValue.setEnabled(status)
		cls.ui.TOFmanualFromValue.setEnabled(status)
		cls.ui.TOFmanualToLabel.setEnabled(status)
		cls.ui.TOFmanualToUnitsValue.setEnabled(status)
		cls.ui.TOFmanualToValue.setEnabled(status)

	def manualTOFtextFieldValidated(cls, with_plot_update=True):
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
		if with_plot_update:
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
			_nxdata.active_data.tof_range = tof

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
			row=cls.current_table_row_selected
			if row == -1:
				cls.clearPlot()
				return
		list_nxsdata_sorted = cls.list_nxsdata_sorted
		nxsdata = list_nxsdata_sorted[row]
		cls.clearPlot(yt_plot=yt_plot, yi_plot=yi_plot)
		if nxsdata is None:
			return
		if yt_plot:
			cls.plotYT(nxsdata, row)
		if yi_plot:
			cls.plotYI(nxsdata, row)
			
	def plotYT(cls, nxsdata, row):
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
		
		if nxsdata.active_data.back_flag:
			[back1, back2] = nxsdata.active_data.back
			back1 = int(back1)
			back2 = int(back2)
			cls.ui.yt_plot.canvas.ax.axhline(back1, color=colors.BACK_SELECTION_COLOR)
			cls.ui.yt_plot.canvas.ax.axhline(back2, color=colors.BACK_SELECTION_COLOR)
			
		if nxsdata.active_data.all_plot_axis.is_yt_ylog:
			cls.ui.yt_plot.canvas.ax.set_yscale('log')
		else:
			cls.ui.yt_plot.canvas.ax.set_yscale('linear')
				
		if nxsdata.active_data.all_plot_axis.yt_data_interval is None:
			if (nxsdata.active_data.new_detector_geometry_flag):
				ylim = 303
			else:
				ylim = 255
			cls.ui.yt_plot.canvas.ax.set_ylim(0, ylim)
			cls.ui.yt_plot.canvas.draw()
			[xmin, xmax] = cls.ui.yt_plot.canvas.ax.xaxis.get_view_interval()
			[ymin, ymax] = cls.ui.yt_plot.canvas.ax.yaxis.get_view_interval()
			nxsdata.active_data.all_plot_axis.yt_data_interval = [xmin, xmax, ymin, ymax]
			nxsdata.active_data.all_plot_axis.yt_view_interval = [xmin, xmax, ymin, ymax]
			cls.ui.yt_plot.toolbar.home_settings = [xmin, xmax, ymin, ymax]
			cls.saveNXSdata(nxsdata, row)
		else:
			[xmin, xmax, ymin, ymax] = nxsdata.active_data.all_plot_axis.yt_view_interval
			cls.ui.yt_plot.canvas.ax.set_xlim([xmin, xmax])
			cls.ui.yt_plot.canvas.ax.set_ylim([ymin, ymax])
			cls.ui.yt_plot.canvas.draw()
	
	def plotYI(cls, nxsdata, row):
		ycountsdata = nxsdata.active_data.ycountsdata
		xaxis = range(len(ycountsdata))
		cls.ui.yi_plot.canvas.ax.plot(ycountsdata, xaxis)
		cls.ui.yi_plot.canvas.ax.set_xlabel(u'counts')
		cls.ui.yi_plot.canvas.ax.set_ylabel(u'y (pixel)')
#		cls.ui.yi_plot.canvas.ax.set_xscale('log')
		
		if nxsdata.active_data.all_plot_axis.yi_data_interval is None:
			if (nxsdata.active_data.new_detector_geometry_flag):
				xlim = 255
				ylim = 303
			else:
				xlim = 303
				ylim = 255
			cls.ui.yi_plot.canvas.ax.set_ylim(0, ylim)

		[peak1, peak2] = nxsdata.active_data.peak
		peak1 = int(peak1)
		peak2 = int(peak2)
		cls.ui.yi_plot.canvas.ax.axhline(peak1, color=colors.PEAK_SELECTION_COLOR)
		cls.ui.yi_plot.canvas.ax.axhline(peak2, color=colors.PEAK_SELECTION_COLOR)
		
		if nxsdata.active_data.back_flag:
			[back1, back2] = nxsdata.active_data.back
			back1 = int(back1)
			back2 = int(back2)
			cls.ui.yi_plot.canvas.ax.axhline(back1, color=colors.BACK_SELECTION_COLOR)
			cls.ui.yi_plot.canvas.ax.axhline(back2, color=colors.BACK_SELECTION_COLOR)
			
		if nxsdata.active_data.all_plot_axis.is_yi_xlog:
			cls.ui.yi_plot.canvas.ax.set_xscale('log')
		else:
			cls.ui.yi_plot.canvas.ax.set_xscale('linear')
		
		if nxsdata.active_data.all_plot_axis.yi_data_interval is None:
			cls.ui.yi_plot.canvas.draw()
			[xmin, xmax] = cls.ui.yi_plot.canvas.ax.xaxis.get_view_interval()
			[ymin, ymax] = cls.ui.yi_plot.canvas.ax.yaxis.get_view_interval()
			nxsdata.active_data.all_plot_axis.yi_data_interval = [xmin, xmax, ymin, ymax]
			nxsdata.active_data.all_plot_axis.yi_view_interval = [xmin, xmax, ymin, ymax]
			cls.ui.yi_plot.toolbar.home_settings = [xmin, xmax, ymin, ymax]
			cls.saveNXSdata(nxsdata, row)
		else:
			[xmin, xmax, ymin, ymax] = nxsdata.active_data.all_plot_axis.yi_view_interval
			cls.ui.yi_plot.canvas.ax.set_xlim([xmin, xmax])
			cls.ui.yi_plot.canvas.ax.set_ylim([ymin, ymax])
			cls.ui.yi_plot.canvas.draw()
		
	def saveNXSdata(cls, nxsdata, row):
		list_nxsdata_sorted = cls.list_nxsdata_sorted
		list_nxsdata_sorted[row] = nxsdata
		cls.list_nxsdata_sorted = list_nxsdata_sorted

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

	def peakBackSpinBoxValueChanged(cls, type, with_plot_update=True):
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
		if with_plot_update:
			cls.displayPlot(row=cls.current_table_row_selected, yt_plot=True, yi_plot=True)
		cls.fileHasBeenModified()
		cls.checkGui()
		
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
		cls.peakBackSpinBoxValueChanged('peak', with_plot_update=with_plot_update)
		cls.peakBackSpinBoxValueChanged('back', with_plot_update=with_plot_update)
		cls.testPeakBackErrorWidgets()
	
	def attenuatorValueChanged(cls, value):
		cls.fileHasBeenModified()			
		
	def editIncidentMediumList(cls):
		_incident_medium_object = IncidentMediumListEditor(parent=cls)
		_incident_medium_object.show()
		
	def generateSFfile(cls):
		runReduction = ReductionSfCalculator(parent=cls)
		
	def saveConfigFiles(cls):
		cls.reduced_files_loaded_object.save()
		cls.guiConfig()

	def guiConfig(cls):
		from quicknxs.config import reflsfcalculatorlastloadedfiles
		reflsfcalculatorlastloadedfiles.switch_config('config_files')
		reflsfcalculatorlastloadedfiles.config_files_path = cls.main_gui.path_config
		reflsfcalculatorlastloadedfiles.switch_config('default')
	
	def closeEvent(cls, event=None):
		cls.saveConfigFiles()