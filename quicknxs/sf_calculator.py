from PyQt4 import QtGui, QtCore
from sf_calculator_interface import Ui_MainWindow
from run_sequence_breaker import RunSequenceBreaker
from mantid.simpleapi import *
from load_and_sort_nxsdata_for_sf_calculator import LoadAndSortNXSDataForSFcalculator
from display_metadata import DisplayMetadata
from logging import info
from utilities import touch, import_ascii_file, makeSureFileHasExtension
from create_sf_config_xml_file import CreateSFConfigXmlFile

import numpy as np
import os

class SFcalculator(QtGui.QMainWindow):
	
	_open_instances = []
	main_gui = None
	data_list = []
	big_table = None
	is_using_Si_slits = False
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
		palette.setColor(QtGui.QPalette.Foreground, QtCore.Qt.red)
		cls.ui.back1_error.setPalette(palette)
		cls.ui.back2_error.setPalette(palette)
		cls.ui.peak1_error.setPalette(palette)
		cls.ui.peak2_error.setPalette(palette)
		cls.ui.error_label.setPalette(palette)
	
	def checkGui(cls):
		if cls.loaded_list_of_runs == []:
			wdg_enabled = False
		else:
			wdg_enabled = True
		cls.enabledWidgets(wdg_enabled)
		cls.testPeakBackErrorWidgets()
		cls.ui.actionSavingConfiguration.setEnabled(wdg_enabled)
		
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
			cls.is_using_Si_slits = o_load_and_sort_nxsdata.is_using_Si_slits
			cls.fillGuiTable()
		else:
			info('No Files loaded!')
		cls.ui.runSequenceLineEdit.setText("")
		cls.checkGui()
		
	def clearTable(cls):
		nbrRow = cls.ui.tableWidget.rowCount()
		if nbrRow > 0:
			for _row in range(nbrRow):
				cls.ui.tableWidget.removeRow(0)
		
	def fillGuiTable(cls):
		if cls.is_using_Si_slits:
			s2ih = 'SiH'
			s2iw = 'SiW'
		else:
			s2ih = 'S2H'
			s2iw = 'S2W'
		verticalHeader = ["Run #","Nbr. Attenuator",u"\u03bbmin(\u00c5)",
		                  u"\u03bbmax(\u00c5)",
		                  "p Charge (mC)",
		                  u"\u03bb requested (\u00c5)",
		                  "S1W","S1H",s2iw, s2ih,
		                  "Peak1","Peak2",
		                  "Back1", "Back2",
		                  "TOF1 (ms)", "TOF2 (ms)"]
		cls.ui.tableWidget.setHorizontalHeaderLabels(verticalHeader)

		cls.clearTable()
		_big_table = cls.big_table
		[nbr_row, nbr_column] = _big_table.shape
		for r in range(nbr_row):
			_row = _big_table[r,:]
			
			cls.ui.tableWidget.insertRow(r)
			
			_run_number = str(int(_row[0]))
			_brush = QtGui.QBrush()
			_brush.setColor(QtCore.Qt.red)
			_item = QtGui.QTableWidgetItem(_run_number)
			_item.setForeground(_brush)
			cls.ui.tableWidget.setItem(r, 0, _item)
			
			_atte = int(_row[1])
			_widget = QtGui.QSpinBox()
			_widget.setMinimum(0)
			_widget.setMaximum(20)
			_widget.setValue(_atte)
			cls.ui.tableWidget.setCellWidget(r,1,_widget)
			
			_lambda_min = str(float(_row[2]))
			_item = QtGui.QTableWidgetItem(_lambda_min)
			cls.ui.tableWidget.setItem(r,2,_item)
			
			_lambda_max = str(float(_row[3]))
			_item = QtGui.QTableWidgetItem(_lambda_max)
			cls.ui.tableWidget.setItem(r,3,_item)
			
			_proton_charge = ("%.2e"%(float(_row[4])))
			_item = QtGui.QTableWidgetItem(_proton_charge)
			cls.ui.tableWidget.setItem(r,4,_item)
			
			_lambda_req = ("%.2f" %(float(_row[5])))
			_item = QtGui.QTableWidgetItem(_lambda_req)
			cls.ui.tableWidget.setItem(r,5,_item)
			
			_s1w = ("%.2f"%(float(_row[6])))
			_item = QtGui.QTableWidgetItem(_s1w)
			cls.ui.tableWidget.setItem(r,6,_item)
			
			_s1h = ("%.2f"%(float(_row[7])))
			_item = QtGui.QTableWidgetItem(_s1h)
			cls.ui.tableWidget.setItem(r,7,_item)

			_s2iw = ("%.2f"%(float(_row[8])))
			_item = QtGui.QTableWidgetItem(_s2iw)
			cls.ui.tableWidget.setItem(r,8,_item)

			_s2ih = ("%.2f"%(float(_row[9])))
			_item = QtGui.QTableWidgetItem(_s2ih)
			cls.ui.tableWidget.setItem(r,9,_item)
			
			for k in range(10,16):
				_brush = QtGui.QBrush()
				_brush.setColor(QtCore.Qt.red)				
				_item = QtGui.QTableWidgetItem("N/A")
				_item.setForeground(_brush)
				cls.ui.tableWidget.setItem(r,k,_item)
	
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
			
	def displayConfigFile(cls, file_name):
		data = import_ascii_file(file_name)
		if not data:
			data = 'EMPTY FILE'
		cls.ui.sfFileNamePreview.setPlainText(data)
		cls.ui.sfFileNamePreview.setEnabled(True)

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
		_configFile = CreateSFConfigXmlFile(parent=cls, filename=filename)
		
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
		
		