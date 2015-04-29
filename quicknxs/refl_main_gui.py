#-*- coding: utf-8 -*-

'''
Module including main GUI class with all signal handling and plot creation.
'''

import os
import sys
import math
from math import radians, fabs
from glob import glob
from numpy import where, pi, newaxis, log10, array, empty, shape
from matplotlib.lines import Line2D
from PyQt4 import QtGui, QtCore
from mantid.simpleapi import *
from xml.dom import minidom
from distutils.util import strtobool
import numpy as np
import time
from distutils.util import strtobool
#import pickle
#QtWebKit

#from logging import info, debug
from .advanced_background import BackgroundDialog
from .compare_plots import CompareDialog
from .config import paths, instrument, gui, export
from .decorators import log_call, log_input, log_both, waiting_effects
from .default_interface_refl import Ui_MainWindow
#from .default_interface_refl import *
from .gui_logging import install_gui_handler, excepthook_overwrite
from .gui_utils import DelayedTrigger, ReduceDialog, Reducer
from .nxs_gui import NXSDialog
from .point_picker import PointPicker
from .polarization_gui import PolarizationDialog
from .qcalc import get_total_reflection, get_scaling, get_xpos, get_yregion
from .qio import HeaderParser, HeaderCreator
from .qreduce import NXSData, NXSMultiData, Reflectivity, OffSpecular, time_from_header, GISANS, DETECTOR_X_REGION, LRDataset, LConfigDataset
from .rawcompare_plots import RawCompare
from .separate_plots import ReductionPreviewDialog
from logging import info, warning, debug
from reduction_mantid import REFLReduction
from utilities import convert_angle
import utilities
import constants
import colors
import nexus_utilities

from calculate_SF import CalculateSF
#from isis_calculate_sf import CalculateSF
from reduced_ascii_loader import reducedAsciiLoader
from stitching_ascii_widget import stitchingAsciiWidgetObject
from peakfinder import PeakFinder
from plot_dialog_refl import PlotDialogREFL
from plot2d_dialog_refl import Plot2dDialogREFL
#from all_plot_axis import AllPlotAxis
from output_reduced_data import OutputReducedData
from export_stitching_ascii_settings import ExportStitchingAsciiSettings
from display_metadata import DisplayMetadata
from make_gui_connections import MakeGuiConnections
from initialize_gui import InitializeGui
from check_peak_back_error_widgets import CheckErrorWidgets
from export_plot_ascii import ExportPlotAscii
from home_plot_button_clicked import HomePlotButtonClicked
from mouse_leave_plot import MouseLeavePlot
from single_plot_click import SinglePlotClick
from log_plot_toggle import LogPlotToggle
from config_file_launcher import ConfigFileLauncher
from open_run_number import OpenRunNumber
from display_plots import DisplayPlots
from selection_bigTable_changed import SelectionBigTableChanged
from populate_reductionTable import PopulateReductionTable
from loading_configuration import LoadingConfiguration
from metadata_finder import MetadataFinder
from sf_calculator import SFcalculator
from table_reduction_run_editor import TableReductionRunEditor
from export_xml_quicknxs_config import ExportXMLquickNXSConfig
from import_xml_quicknxs_config import ImportXMLquickNXSConfig

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
from matplotlib.figure import Figure


class MainGUI(QtGui.QMainWindow):
    '''
    The program top level window with all direct event handling.
    '''
    active_folder=instrument.data_base
    active_file=u''
    last_mtime=0. #: Stores the last time the current file has been modified
    _active_data=None
    current_loaded_file = '~/tmp.xml'
    window_title = 'QuickNXS for REF_L - '

    # will save the data and norm objects according to their position in the bigTable
    # [data, norm, metadata from config file]
    bigTableData = empty((20,3), dtype=object)

    # keep last folder used as default for next access
    path_config = '.'
    path_ascii = '.'

    # will be on when the user double click an editable cell
    editing_flag = False

    ref_list_channels=[] #: Store which channels are available for stored reflectivities
    _refl=None #: Reflectivity of the active dataset
    ref_norm={} #: Store normalization data with extraction information
    cut_areas={'fan': (0, 0)} #: store cut points options for each normalization file used
    auto_change_active=False
    reduction_list=[] #: Store information and data of reflectivities from different files
    color=None
    open_plots=[] #: to keep non modal dialogs open when their caller is destroyed
    channels=[] #: Available channels of the active dataset
    active_channel='x' #: Selected channel for the overview and projection plots
    _control_down=False
    y_bg=0.
    background_dialog=None
    # threads
    _gisansThread=None
    _pending_header=None
    # keep the direct beam selection for one file here
    _norm_selected=None
    # plot line storages
    _x_projection=None
    _y_projection=None
    _picked_line=None
    proj_lines=None
    overview_lines=None
    # colors for the reflecitivy lines
    _refl_color_list=['blue', 'red', 'green', 'purple', '#aaaa00', 'cyan']

    # interaction with big table
    _prev_row_selected = 0
    _prev_col_selected = 0

    _cur_row_selected = 0
    _cur_column_selected = 0

    # current TOF status
    _auto_tof_flag = True
    _ms_tof_flag = True

    # live selection of peak, back and low_res
    _live_selection = None # 'peak_min','peak_max','back_min','back_max','lowres_min','lowres_max'

    # to skip data_norm_tab_changed when user clicked table
    userClickedInTable = False

    # log/linear status of yi_plot
    isReducedPlotLog = True

    stitchingAsciiWidgetObject = None
    reducedFilesLoadedObject = None
    listAction = [] # in Menu File
    fileMenuObject = None

    # for double click of yi plot
    timeClick1 = -1

    allPlotAxis = None

    exportStitchingAsciiSettings = None
    reduction_table_copied_field = ''
    redcution_table_copied_row_col = []

    fileLoaded=QtCore.pyqtSignal()
    initiateProjectionPlot=QtCore.pyqtSignal(bool)
    initiateReflectivityPlot=QtCore.pyqtSignal(bool)
    reflectivityUpdated=QtCore.pyqtSignal(bool)

    def __init__(self, argv=[], parent=None):
        if parent is None:
            QtGui.QMainWindow.__init__(self)
        else:
            QtGui.QMainWindow.__init__(self, parent, QtCore.Qt.Window)
        self.auto_change_active=True
        exec 'from .default_interface_refl import Ui_MainWindow'
        self.ui=Ui_MainWindow()
        self.ui.setupUi(self)
        install_gui_handler(self)
        InitializeGui(self)
        MakeGuiConnections(self)

        ## open file after GUI is shown
        #if '-ipython' in argv:
            #self.run_ipython()
        #else:
            #self.ipython=None
        #if len(argv)>0:
            #if sys.version_info[0]<3:
                ## if non ascii character in filenames interprete it as utf8
                #argv=[unicode(argi, 'utf8', 'ignore') for argi in argv]
            ## delay action to be run within event loop, this allows the error handling to work
            #if argv[0][-4:]=='.dat':
                #self.trigger('loadExtraction', argv[0])
            #elif len(argv)==1:
                #if argv[0][-4:]=='.nxs':
                    #self.trigger('fileOpen', argv[0])
                #else:
                    #self.trigger('openByNumber', argv[0])
            #else:
                #self.trigger('automaticExtraction', argv)
        #else:

    #def logtoggle(self, checked):
        #self.isLog = checked
        #self.plot_overview_REFL(plot_yt=True, plot_yi=True, plot_it=True, plot_ix=True)

    def fileHasBeenModified(self):
	dialog_title = self.window_title + self.current_loaded_file
	new_dialog_title = dialog_title + '*'
	self.setWindowTitle(new_dialog_title)
		
    def resetFileHasBeenModified(self):
	dialog_title = self.window_title + self.current_loaded_file
	self.setWindowTitle(dialog_title)

    def eventTofBinsEvent(self):
	self.fileHasBeenModified()
    def qStepEvent(self):
	self.fileHasBeenModified()
    def autoBackSelectionWidthEvent(self):
	self.fileHasBeenModified()
    def autoTofFlagEvent(self):
	self.fileHasBeenModified()
    def selectIncidentMediumListEvent(self, value):
	self.fileHasBeenModified()
	
    # export plot into ascii files
    def export_ix(self):
        ExportPlotAscii(self, type='ix')
    def export_it(self):
        ExportPlotAscii(self, type='it')
    def export_yt(self):
        ExportPlotAscii(self, type='yt')
    def export_yi(self):
        ExportPlotAscii(self, type='yi')
    def export_stitching_data(self):
        ExportPlotAscii(self, type='stitched')

    # home button of plots
    def home_clicked_yi_plot(self):
        HomePlotButtonClicked(self, type='yi')
    def home_clicked_yt_plot(self):
        HomePlotButtonClicked(self, type='yt')
    def home_clicked_it_plot(self):
        HomePlotButtonClicked(self, type='it')
    def home_clicked_ix_plot(self):
        HomePlotButtonClicked(self, type='ix')
    def home_clicked_data_stitching_plot(self):
        HomePlotButtonClicked(self, type='stitching')

    # leave figure 
    def leave_figure_yi_plot(self):
        MouseLeavePlot(self, type='yi')
    def leave_figure_yt_plot(self):
        MouseLeavePlot(self, type='yt')
    def leave_figure_it_plot(self):
        MouseLeavePlot(self, type='it')
    def leave_figure_ix_plot(self):
        MouseLeavePlot(self, type='ix')
    def leave_figure_data_stitching_plot(self):
        MouseLeavePlot(self, type='stitching')

    # single click
    def single_click_data_yi_plot(self, isPanOrZoomActivated):
        SinglePlotClick(self, 'data','yi')
    def single_click_norm_yi_plot(self, isPanOrZoomActivated):
        SinglePlotClick(self,'norm','yi')
    def single_click_norm_yt_plot(self, isPanOrZoomActivated):
        SinglePlotClick(self,'norm','yt')
    def single_click_data_yt_plot(self, isPanOrZoomActivated):
        SinglePlotClick(self,'data','yt')
    def single_click_norm_it_plot(self, isPanOrZoomActivated):
        SinglePlotClick(self, 'norm','it')
    def single_click_data_it_plot(self, isPanOrZoomActivated):
        SinglePlotClick(self,'data','it')
    def single_click_norm_ix_plot(self, isPanOrZoomActivated):
        SinglePlotClick(self,'norm','ix')
    def single_click_data_ix_plot(self, isPanOrZoomActivated):
        SinglePlotClick(self,'data','ix')
    def single_click_data_stitching_plot(self, isPanOrZoomActivated):
        SinglePlotClick(self,'data','stitching')

    # toggle log
    def logy_toggle_yt_plot(self, checked):
        LogPlotToggle(self,checked,'yt',is_y_log=True)
    def logy_toggle_it_plot(self, checked):
        LogPlotToggle(self,checked,'it',is_y_log=True)
    def logy_toggle_ix_plot(self, checked):
        LogPlotToggle(self,checked,'ix',is_y_log=True)
    def logx_toggle_yi_plot(self, checked):
        LogPlotToggle(self,checked,'yi',is_y_log=False)
    def logx_toggle_data_stitching(self, checked):
        LogPlotToggle(self,checked,'stitching',is_y_log=False)
    def logy_toggle_data_stitching(self, checked):
        LogPlotToggle(self,checked,'stitching',is_y_log=True)

    def launch_config_file1(self):
        ConfigFileLauncher(self, 0)
    def launch_config_file2(self):
        ConfigFileLauncher(self, 1)
    def launch_config_file3(self):
        ConfigFileLauncher(self, 2)
    def launch_config_file4(self):
        ConfigFileLauncher(self, 3)
    def launch_config_file5(self):
        ConfigFileLauncher(self, 4)
    def launch_config_file6(self):
        ConfigFileLauncher(self, 5)
    def launch_config_file7(self):
        ConfigFileLauncher(self, 6)
    def launch_config_file8(self):
        ConfigFileLauncher(self, 7)
    def launch_config_file9(self):
        ConfigFileLauncher(self, 8)
    def launch_config_file10(self):
        ConfigFileLauncher(self, 9)

    def launch_SFcalculator(self):
        sfCalculator = SFcalculator(self)
        sfCalculator.show()

    def raiseError(self):
        '''
          Just for testing of loggin etc.
        '''
        raise RuntimeError, 'Test error from GUI'

    def set_debug(self):
        '''
          Switch on debug mode logging during normal execuation.
        '''
        from logging import getLogger, DEBUG
        logger=getLogger()
        logger.setLevel(DEBUG)
        for handler in logger.handlers:
            if handler.__class__.__name__=='FileHandler':
                handler.setLevel(DEBUG)
        info('Logger debug mode is now active')

    def _install_exc(self):
        '''
        Installs excepthook overwrite in GUI process for IPython.
        '''
        sys.excepthook=excepthook_overwrite
        debug('Installed excepthook overwrite')
        # set matplotlib fonts back to default
        from mplwidget import _set_default_rc
        _set_default_rc()

    @log_input
    def processDelayedTrigger(self, item, args):
        '''
        Calls private method after delay action was
        triggered.
        '''
        attrib=getattr(self, str(item))
        if type(attrib) is type(self.initiateProjectionPlot):
            attrib.emit(*args)
        else:
            attrib(*args)

    def metadataFinderEvent(self):
        _meta_finder = MetadataFinder(self)
        _meta_finder.show()

    @log_input
    def fileOpen(self, filename, do_plot=True, do_add=False):
        '''
        Open a new datafile and plot the data.
        Also will add those new files to previously loaded files if do_add flag is provided
        '''

        # check if we have a string or a string array
        if type(filename) == type(u"") or type(filename) == type(""):
            _filename = filename
        else:
            _filename = filename[0]

        folder, base=os.path.split(_filename)
        if folder!=self.active_folder:
            self.onPathChanged(base, folder)
        else:
            pass
            self.updateFileList(base, folder)
        self.active_file=base

        event_split_bins=None
        event_split_index=0      
        bin_type=0

        if do_add:

            # get list of previously loaded runs
#      [r,c] = self.getCurrentRowColumnSelected()
            row = self._cur_row_selected
            col = self._cur_column_selected
            if c is not 0:
                c=1

            data = self.bigTableData[r,c]
            _prevLoadedFullFile = data.active_data.filename
            filename = [_prevLoadedFullFile, filename]

        self._norm_selected=None
        if type(filename) == type(u"") or type(filename) == type(""):
            info(u"Reading file %s ..." % filename)
        else: # more than 1 file
            strFilename = ", ".join(filename)
            info(u"Reading files %s ..." % strFilename)

        if self.ui.dataNormTabWidget.currentIndex() == 0: #data
            isData = True
        else:
            isData = False

        backOffsetFromPeak = self.ui.autoBackSelectionWidth.value()
        if self.ui.actionAutomaticPeakFinder.isChecked():
            isAutoPeakFinder = True
        else:
            isAutoPeakFinder = False

        isAutoTofFinder = self.ui.autoTofFlag.isChecked()

        data=NXSData(filename,
                     bin_type=bin_type,
                     bins=self.ui.eventTofBins.value(),
                     callback=self.updateEventReadout,
                     event_split_bins=event_split_bins,
                     event_split_index=event_split_index,
                     angle_offset= self.ui.angleOffsetValue.text(),
                     isData = isData,
                     isAutoPeakFinder = isAutoPeakFinder,
                     backOffsetFromPeak = backOffsetFromPeak,
                     isAutoTofFinder = isAutoTofFinder
                     )

        if data is not None:
            # save the data in the right spot (row, column)
            if do_add:
                r = self._cur_row_selected
                c = self._cur_column_selected        
                # [r,c] = self.getCurrentRowColumnSelected()
            else:
                [r,c] = self.getRowColumnNextDataSet()

            if c is not 0:
                c=1
            self.bigTableData[r,c] = data
            self._prev_row_selected = r
            self._prev_col_selected = c

            self.enableWidgets(status=True)

            self._fileOpenDoneREFL(data, filename, do_plot)

    @log_input
    def fileOpenSum(self, filenames, do_plot=True):
        '''
        Open and sum up several datafiles and plot the data.
        '''
        folder, base=os.path.split(filenames[0])
        if folder!=self.active_folder:
            self.onPathChanged(base, folder)
        self.active_file=base
        info(u"Reading files %s..."%(filenames[0]))
        try:
            data=NXSMultiData(filenames,
                              bin_type=self.ui.eventBinMode.currentIndex(),
                              bins=self.ui.eventTofBins.value(),
                              callback=self.updateEventReadout)
        except:
            warning('Could not open files to sum them up:', exc_info=True)
            return
        self._fileOpenDone(data, filenames[0], do_plot)

    @log_call
    def _fileOpenDoneREFL(self, data=None, filename=None, do_plot=True, update_table=True):
        if data is None:
            info('Data file is empty!')
            return

        self.active_data = data.active_data
#    self.active_data = data
        self.filename = data.origin

        info(u"%s loaded"%(filename))
        self.cache_indicator.setText('Cache Size: %.1fMB'%(NXSData.get_cachesize()/1024.**2))    

        self.fileLoaded.emit()

        #populate table
        if update_table:
            self.populateReflectivityTable(data)
            #self.ui.addRunNumbers.setEnabled(True)
        else: #update gui
            pass

        if do_plot:
            self.plot_overview_REFL()
            #self.initiateProjectionPlot.emit(False)
            #self.initiateReflectivityPlot.emit(False)    

    def allTabWidgetsEnabler(self, enableFlag = False):
        self.ui.tab.setEnabled(enableFlag)
        self.ui.tab_2.setEnabled(enableFlag)

    def clearMetadataWidgets(self):
        self.ui.metadataProtonChargeValue.setText('N/A')
        self.ui.metadataLambdaRequestedValue.setText('N/A')
        self.ui.metadataS1HValue.setText('N/A')
        self.ui.metadataS1WValue.setText('N/A')
        self.ui.metadataS2HValue.setText('N/A')
        self.ui.metadataS2WValue.setText('N/A')
        self.ui.metadatathiValue.setText('N/A')
        self.ui.metadatatthdValue.setText('N/A')

    def enableWidgets(self, status=False, checkStatus=False):
        '''
        Will enable or not the widgets of the curren tab. 
        If checkStatus is True, will overwrite the status flag and
        will check itself what should be done (enable or not).
        '''
        isData = False
        if self.ui.dataNormTabWidget.currentIndex() == 0: #data
            isData = True

        if checkStatus:
#      [r,c] = self.getCurrentRowColumnSelected()
            r = self._cur_row_selected
            c = self._cur_column_selected
            if c > 0:
                c= 1
            data = self.bigTableData[r,c]
            if data is None:
                status = False
            else:
                status = True

        if isData:
            self.ui.tab.setEnabled(status)
        else:
            self.ui.tab_2.setEnabled(status)

        if self.bigTableData[0,0] is None:
            bigTableStatus = False
        else:
            bigTableStatus = True
        self.ui.reductionTable.setEnabled(bigTableStatus)

    def getRowColumnNextDataSet(self):
        _selected_row = self.ui.reductionTable.selectedRanges()

        # add new row each time a data is selected
        if self.ui.dataNormTabWidget.currentIndex() == 0: #data
            _column = 0
        else:
            _column = 6

        # empty table, let's add a row
        if _selected_row == []:
            _selected_row = 0
        else:
            _selected_row = _selected_row[0].bottomRow()

        # if run is normalization, do not create a new row
        if _column == 6:
            _row = _selected_row
        else:
            # if selected row has already a data run number -> create a new row
            _current_item = self.ui.reductionTable.item(_selected_row, 0)
            if _current_item is None:
                # insert new item (data or normalization run number)
                _row = _selected_row
            else:
                # find out last row
                _row = self.ui.reductionTable.rowCount()

        return [_row, _column]

    def reduction_table_cell_modified(self, item):
        return
        if self.editing_flag:
            OpenRunNumber(self, item, replaced_data=True)
            self.editing_flag = False
        #  DisplayPlots(self)

    def reduction_table_cell_double_clicked(self, row, column):
        if column == 0 or column == 6:
            self.editing_flag = True

    def reduction_table_cell_single_clicked(self, item):
        pass
#    self.editing_flag = True
    #  self.reductionTable_manual_entry(item)

    @waiting_effects
    def reductionTable_manual_entry(self, item):
#    OpenRunNumber(self, item)
        return

        if not self.editing_flag:
            return
        self.editing_flag = False

        row = item.row()
        column = item.column()
        cell_content = str(item.text())

        # data or norm
        bigTableCol = 0
        if column == 0:
            isData = True
        else:
            isData = False
            bigTableCol = 1

        bigTableData = self.bigTableData

        # if norm field is empty, clear data
        # check if only 1 run number, or more
        str_split = cell_content.split(',')
        if str_split == [''] and (not isData):
            bigTableData[row,1] = None
            self.bigTableData = bigTableData
            self.plot_overview_REFL()
            self.enableWidgets(status=False)
            self._prev_row_selected = -1
            self._prev_col_selected = -1
            return

        #make sure we are dealing with a number or a list of numbers
        try:
            isNumber = int(str_split[0])
        except ValueError:
            msgBox = QtGui.QMessageBox.critical(self, 'INVALID FIELD!', 'MAKE SURE YOU ENTERED A NUMBER!')
            if isData:
                _data = bigTableData[row,0]
                run_number = _data.active_data.run_number
                _item = QtGui.QTableWidgetItem(run_number)
                _item.setForeground(QtGui.QColor(250,0,0))
                self.ui.reductionTable.setItem(row, 0, _item)
            return

        # keep going only for data and norm columns
        if (column != 0) and (column != 6):
            return

        if str_split == [''] and isData:
            msgBox = QtGui.QMessageBox.critical(self, 'INVALID FIELD!','THIS BOX CAN NOT BE EMPTY !')
            # put back previous data run number
            _data = bigTableData[row,0]
            run_number = _data.active_data.run_number
            _item = QtGui.QTableWidgetItem(run_number)
            _item.setForeground(QtGui.QColor(250,0,0))
            self.ui.reductionTable.setItem(row, 0, _item)
            return

        if len(str_split) == 1:
            # load object
            info('Trying to locate file number %s...'% cell_content)
            fullFileName = nexus_utilities.findNeXusFullPath(int(cell_content))
#      fullFileName = FileFinder.findRuns("REF_L_%d" % int(cell_content))[0]
        else:
            fullFileName = []
            for _run in str_split:
#        _fullFileName = FileFinder.findRuns("REF_L_%d" % int(_run))[0]
                _fullFileName = nexus_utilities.findNeXusFullPath(int(_run))
                fullFileName.append(_fullFileName)

        data = NXSData(fullFileName,
                       bin_type = 0,
                       bins = self.ui.eventTofBins.value(),
                       callback = self.updateEventReadout,
                       event_split_bins = None,
                       event_split_index = 0,
                       angle_offset = self.ui.angleOffsetValue.text(),
                       isData = isData)
#    self.enableWidgets(status=True)

        # if previously entry has been loaded, then recover metadata info (peak, back...etc)
        # otherwise get them from config file bigTable[row,2]
        data_active = data.active_data
        if self.bigTableData[row, bigTableCol] is None: # use config file to populate metadata of file

            config_file = self.bigTableData[row, 2]

            if isData:
                data_active.peak = config_file.data_peak
                data_active.back = config_file.data_back
                data_active.low_res = config_file.data_low_res
                data_active.back_flag = config_file.data_back_flag
                data_active.low_res_flag = config_file.data_low_res_flag

            else:
                data_active.peak = config_file.norm_peak
                data_active.back = config_file.norm_back
                data_active.low_res = config_file.norm_low_res
                data_active.back_flag = config_file.norm_back_flag
                data_active.low_res_flag = config_file.norm_low_res_flag

            data_active.tof_range = config_file.tof_range
            data_active.tof_units = config_file.tof_units
            data_active.tof_auto_flag = config_file.tof_auto_flag

        else: # use previously loaded data object
            prev_data = self.bigTableData[row, bigTableCol]
            prev_active = prev_data.active_data
            data_active.peak = prev_active.peak
            data_active.back = prev_active.back
            data_active.low_res = prev_active.low_res
            data_active.back_flag = prev_active.back_flag
            data_active.low_res_flag = prev_active.low_res_flag
            data_active.tof_range = prev_active.tof_range
            data_active.tof_units = prev_active.tof_units
            data_active.tof_auto_flag = prev_active.tof_auto_flag
            data_active.tof_range_auto = prev_active.tof_range_auto

        # replace entry in bigTable with new loaded object and display new data
        data.active_data = data_active
        self.bigTableData[row,bigTableCol] = data

        self._prev_row_selected = -1
        self._prev_col_selected = -1

        self.bigTable_selection_changed(row, column)

    def removeRowReductionTable(self):
        nbrRow = self.ui.reductionTable.rowCount()
        if nbrRow == 0:
            return

        # remove row from table
        #[row,col] = self.getCurrentRowColumnSelected()
        row = self._cur_row_selected
        col = self._cur_column_selected
        self.ui.reductionTable.removeRow(row)
        self.ui.reductionTable.show()

        self.ui.reductionTable.setRangeSelected(QtGui.QTableWidgetSelectionRange(0,0,
                                                                                 row,6), False)
        # update bigTableData
        bigTableData = self.bigTableData
        bigTableData = np.delete(bigTableData, (row), axis=0)
        self.bigTableData = bigTableData

        nbrRow = self.ui.reductionTable.rowCount()
        if nbrRow == 0:
            self.clear_plot_overview_REFL(True)
            self.allTabWidgetsEnabler(enableFlag=False)
            self.clearMetadataWidgets()
            return
        if nbrRow == 1:
            self.ui.reductionTable.setRangeSelected(QtGui.QTableWidgetSelectionRange(0,0,
                                                                                     0,0), True)
        elif row == (nbrRow-1): # last row selected => select previous row
            self.ui.reductionTable.setRangeSelected(QtGui.QTableWidgetSelectionRange(row-1,0,
                                                                                     row-1,0), True)
        else: # select same row
            self.ui.reductionTable.setRangeSelected(QtGui.QTableWidgetSelectionRange(row,0,
                                                                                     row,0), True)

        # force update of plot
        self._prev_row_selected = -1
        self._prev_col_selected = -1
        self.bigTable_selection_changed(row, col)   

    def populateReflectivityTable(self, data):
        return
        # will populate the recap table

        _selected_row = self.ui.reductionTable.selectedRanges()

        # are we replacing or adding a new entry
        do_add = False
        #if self.ui.addRunNumbers.isEnabled() and self.ui.addRunNumbers.isChecked():
            #do_add = True

        if do_add:
            #[r,c] = self.getCurrentRowColumnSelected()
            r = self._cur_row_selected
            c = self._cur_column_selected

            if c !=0:
                _column = 6
            else:
                _column = 0

            _row = r

            _run_number = data.list_run_numbers.join(',')
            _item = QtGui.QTableWidgetItem(data._run_number)
            _item.setForeground(QtGui.QColor(13,24,241))
#      _item.setFlags(QtCore.Qt.ItemIsEditable or QtCore.Qt.ItemIsSelectable or QtCore.Qt.ItemIsEnabled)
            self.ui.reductionTable.setItem(r, _column, _item)

            self._prev_row_selected = _row
            self._prev_col_selected = _column      

        else:
            # add new row each time a data is selected
            if self.ui.dataNormTabWidget.currentIndex() == 0: #data
                _column = 0
            else:
                _column = 6

            # empty table, let's add a row
            if _selected_row == []:
                self.ui.reductionTable.insertRow(0)
                _selected_row = 0
            else:
                _selected_row = _selected_row[0].bottomRow()
                self.ui.reductionTable.setRangeSelected(QtGui.QTableWidgetSelectionRange(_selected_row,0,
                                                                                         _selected_row,0), False)
                self.ui.reductionTable.setRangeSelected(QtGui.QTableWidgetSelectionRange(_selected_row,6,
                                                                                         _selected_row,6), False)

            _item = QtGui.QTableWidgetItem(data.active_data.run_number)

            # if run is normalization, do not create a new row
            if _column == 6:
                _row = _selected_row
            else:
                # if selected row has already a data run number -> create a new row
                _current_item = self.ui.reductionTable.item(_selected_row, 0)
                if _current_item is None:
                    # insert new item (data or normalization run number)
                    _row = _selected_row
                else:
                    # find out last row
                    _row = self.ui.reductionTable.rowCount()
                    self.ui.reductionTable.insertRow(_row)

#      _item.setFlags(QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
            _item.setForeground(QtGui.QColor(13,24,241))
            self.ui.reductionTable.setItem(_row, _column, _item)
#      self.ui.reductionTable.editItem(_row, _column, _item)
            self.ui.reductionTable.setRangeSelected(QtGui.QTableWidgetSelectionRange(_row,
                                                                                     _column,
                                                                                     _row,
                                                                                     _column), True)
            self._prev_row_selected = _row
            self._prev_col_selected = _column

        if _column == 0:

            color = QtGui.QColor(100,100,150)

            # add incident angle
            incident_angle = data.active_data.incident_angle
            _item_angle = QtGui.QTableWidgetItem(incident_angle)
            _item_angle.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
            _item_angle.setForeground(color)
            self.ui.reductionTable.setItem(_row,1,_item_angle)

            [from_l, to_l] = data.active_data.lambda_range
            _item_from_l = QtGui.QTableWidgetItem(str(from_l))
            _item_from_l.setForeground(color)
            _item_from_l.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
            self.ui.reductionTable.setItem(_row, 2, _item_from_l)
            _item_to_l = QtGui.QTableWidgetItem(str(to_l))
            _item_to_l.setForeground(color)
            _item_to_l.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
            self.ui.reductionTable.setItem(_row, 3, _item_to_l)

            [from_q, to_q] = data.active_data.q_range
            _item_from_q = QtGui.QTableWidgetItem(str(from_q))
            _item_from_q.setForeground(color)
            _item_from_q.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
            self.ui.reductionTable.setItem(_row, 4, _item_from_q)
            _item_to_q = QtGui.QTableWidgetItem(str(to_q))
            _item_to_q.setForeground(color)
            _item_to_q.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
            self.ui.reductionTable.setItem(_row, 5, _item_to_q)


    @log_call
    def _fileOpenDone(self, data=None, filename=None, do_plot=None):
        base=os.path.basename(filename)
        if data is None:
            self.ui.currentChannel.setText(u'<b>!!!NO DATA IN FILE %s!!!</b>'%base)
            return
        self.channels=data.keys()

        currentChannel=0
        for i in range(12):
            if getattr(self.ui, 'selectedChannel%i'%i).isChecked():
                currentChannel=i

        if currentChannel<len(self.channels):
            self.active_channel=self.channels[currentChannel]
        else:
            self.active_channel=self.channels[0]
            self.ui.selectedChannel0.setChecked(True)
        for i, channel in enumerate(self.channels):
            getattr(self.ui, 'selectedChannel%i'%i).show()
            getattr(self.ui, 'selectedChannel%i'%i).setText(channel)
        for i in range(len(self.channels), 12):
            getattr(self.ui, 'selectedChannel%i'%i).hide()

        self.active_data=data
        self.last_mtime=os.path.getmtime(filename)
        info(u"%s loaded"%(filename))
        self.cache_indicator.setText('Cache Size: %.1fMB'%(NXSData.get_cachesize()/1024.**2))

        norm=self.getNorm()
        self.auto_change_active=True
        if self.ui.fanReflectivity.isChecked():
            self.ui.rangeStart.setValue(self.cut_areas['fan'][0])
            self.ui.rangeEnd.setValue(self.cut_areas['fan'][1])
        elif norm in self.cut_areas:
            self.ui.rangeStart.setValue(self.cut_areas[norm][0])
            self.ui.rangeEnd.setValue(self.cut_areas[norm][1])
        else:
            self.ui.rangeStart.setValue(0)
            self.ui.rangeEnd.setValue(0)
        self.auto_change_active=False

        self.fileLoaded.emit()
        if do_plot:
            self.initiateProjectionPlot.emit(False)
            self.initiateReflectivityPlot.emit(False)

    def empty_cache(self):
        """
        Empty the NXSData readout cache.
        """
        NXSData._cache=[]
        self.cache_indicator.setText('Cache Size: 0.0MB')

####### Plot related methods
    @log_call
    def plotActiveTab(self):
        '''
        Select the appropriate function to plot all visible images.
        '''

        # FIXME
        if instrument.NAME == 'REF_L': #TODO HARDCODED INSTRUMENT
            return

        if self.auto_change_active or not self.active_data:
            return
        color=str(self.ui.color_selector.currentText())
        if color!=self.color and self.color is not None:
            self.color=color
            plots=[self.ui.xy_pp, self.ui.xy_mp, self.ui.xy_pm, self.ui.xy_mm,
                   self.ui.xtof_pp, self.ui.xtof_mp, self.ui.xtof_pm, self.ui.xtof_mm,
                   self.ui.xy_overview, self.ui.xtof_overview]
            for plot in plots:
                plot.clear_fig()
        elif self.color is None:
            self.color=color
        if self.ui.plotTab.currentIndex()!=4 and self._gisansThread:
            self._gisansThread.finished.disconnect()
            self._gisansThread.terminate()
            self._gisansThread.wait(100)
            self._gisansThread=None
        if self.ui.plotTab.currentIndex()==0:
            self.plot_overview()
        if self.ui.plotTab.currentIndex()==1:
            self.plot_xy()
        if self.ui.plotTab.currentIndex()==2:
            self.plot_xtof()
        if self.ui.plotTab.currentIndex()==3:
            self.plot_offspec()
        if self.ui.plotTab.currentIndex()==4:
            self.plot_gisans()
        if self.ui.plotTab.currentIndex()==5:
            self.update_daslog()

    @log_call
    def plot_overview(self):
        '''
        X vs. Y and X vs. Tof for main channel.
        '''
        if instrument.NAME == "REF_M": #TODO HARDCODED INSTRUMENT
            self.plot_overview_REFM()
        else:
            self.plot_overview_REFL()

    def clear_plot_overview_REFL(self, isData, plot_yt=True, plot_yi=True, plot_it=True, plot_ix=True):
        if isData:
            if plot_yt:
                self.ui.data_yt_plot.clear()
                self.ui.data_yt_plot.draw()

            if plot_yi:
                self.ui.data_yi_plot.clear()
                self.ui.data_yi_plot.draw()

            if plot_it:
                self.ui.data_it_plot.clear()
                self.ui.data_it_plot.draw()

            if plot_ix:
                self.ui.data_ix_plot.clear()
                self.ui.data_ix_plot.draw()

        else:
            if plot_yt:
                self.ui.norm_yt_plot.clear()
                self.ui.norm_yt_plot.draw()

            if plot_yi:
                self.ui.norm_yi_plot.clear()
                self.ui.norm_yi_plot.draw()

            if plot_it:
                self.ui.norm_it_plot.clear()
                self.ui.norm_it_plot.draw()

            if plot_ix:
                self.ui.norm_ix_plot.clear()
                self.ui.norm_ix_plot.draw()

    #@log_call
    def plot_overview_REFL(self, plot_yt=True, plot_yi=True, plot_it=True, plot_ix=True):

        # check witch tab is activated (data or norm)
        if self.ui.dataNormTabWidget.currentIndex() == 0: #data
            isDataSelected = True
        else:
            isDataSelected = False

        # clear previous plot
        self.clear_plot_overview_REFL(isDataSelected, 
                                      plot_yt=plot_yt, 
                                      plot_yi=plot_yi, 
                                      plot_it=plot_it, 
                                      plot_ix=plot_ix)

        #[r,c] = self.getCurrentRowColumnSelected()
        r = self._cur_row_selected
        c = self._cur_column_selected
        if c>0:
            c=1
        _data = self.bigTableData[r,c]
        if _data is None:
            return
        data = _data.active_data
        filename = data.filename

        if self.ui.dataTOFmanualMode.isChecked(): # manual mode
            tof_range_auto = data.tof_range

        else: # auto mode
            tof_range_auto = data.tof_range_auto

        tof_axis = data.tof_axis_auto_with_margin
        tof_axis_ms = tof_axis / float(1000)

        xy = data.xydata
        ytof = data.ytofdata
        countstofdata = data.countstofdata
        countsxdata = data.countsxdata
        ycountsdata = data.ycountsdata

        [peak1, peak2] = data.peak
        [back1, back2] = data.back
        [lowRes1, lowRes2] = data.low_res
        back_flag = bool(data.back_flag)
        low_res_flag = bool(data.low_res_flag)

        if isDataSelected: # data
            self.ui.dataNameOfFile.setText('%s'%filename)

            # repopulate the tab
            peak1 = int(peak1)
            peak2 = int(peak2)
            peak_min = min([peak1, peak2])
            peak_max = max([peak1, peak2])
            self.ui.dataPeakFromValue.setValue(peak_min)
            self.ui.dataPeakToValue.setValue(peak_max)

            back1 = int(back1)
            back2 = int(back2)
            back_min = min([back1, back2])
            back_max = max([back1, back2])
            self.ui.dataBackFromValue.setValue(back_min)
            self.ui.dataBackToValue.setValue(back_max)

            lowRes1 = int(lowRes1)
            lowRes2 = int(lowRes2)
            lowRes_min = min([lowRes1, lowRes2])
            lowRes_max = max([lowRes1, lowRes2])
            self.ui.dataLowResFromValue.setValue(lowRes_min)
            self.ui.dataLowResToValue.setValue(lowRes_max)
            self.ui.dataBackgroundFlag.setChecked(back_flag)

            self.ui.dataLowResFlag.setChecked(low_res_flag)

            yt_plot = self.ui.data_yt_plot
            yi_plot = self.ui.data_yi_plot
            it_plot = self.ui.data_it_plot
            ix_plot = self.ui.data_ix_plot

            incident_angle = data.incident_angle
            [qmin,qmax] = data.q_range
            [lmin,lmax] = data.lambda_range

            _item_min = QtGui.QTableWidgetItem(str(qmin))
            _item_min.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)      
            _item_max = QtGui.QTableWidgetItem(str(qmax))
            _item_max.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)      
            _item_lmin = QtGui.QTableWidgetItem(str(lmin))
            _item_lmin.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)      
            _item_lmax = QtGui.QTableWidgetItem(str(lmax))
            _item_lmax.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)      
            _item_incident = QtGui.QTableWidgetItem(str(incident_angle))
            _item_incident.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)      

#      [row, column] = self.getCurrentRowColumnSelected()
            row = self._cur_row_selected
            column = self._cur_column_selected

            self.ui.reductionTable.setItem(row, 4, _item_min)
            self.ui.reductionTable.setItem(row, 5, _item_max)
            self.ui.reductionTable.setItem(row, 2, _item_lmin)
            self.ui.reductionTable.setItem(row, 3, _item_lmax)
            self.ui.reductionTable.setItem(row, 1, _item_incident)

        else: # normalization

            self.ui.normNameOfFile.setText('%s'%filename)

            flag = data.use_it_flag
            self.ui.useNormalizationFlag.setChecked(flag)

            peak1 = int(peak1)
            peak2 = int(peak2)
            peak_min = min([peak1, peak2])
            peak_max = max([peak1, peak2])
            self.ui.normPeakFromValue.setValue(peak_min)
            self.ui.normPeakToValue.setValue(peak_max)

            back1 = int(back1)
            back2 = int(back2)
            back_min = min([back1, back2])
            back_max = max([back1, back2])
            self.ui.normBackFromValue.setValue(back_min)
            self.ui.normBackToValue.setValue(back_max)

            lowRes1 = int(lowRes1)
            lowRes2 = int(lowRes2)
            lowRes_min = min([lowRes1, lowRes2])
            lowRes_max = max([lowRes1, lowRes2])
            self.ui.normLowResFromValue.setValue(lowRes_min)
            self.ui.normLowResToValue.setValue(lowRes_max)

            self.ui.normLowResFlag.setChecked(low_res_flag)

            self.ui.normBackgroundFlag.setChecked(back_flag)

            yt_plot = self.ui.norm_yt_plot
            yi_plot = self.ui.norm_yi_plot
            it_plot = self.ui.norm_it_plot
            ix_plot = self.ui.norm_ix_plot

        if data.new_detector_geometry_flag:
            ylim = 303 #TODO MAGIC NUMBER
            xlim = 255 #TODO MAGIC NUMBER
        else:
            ylim = 255 #TODO MAGIC NUMBER
            xlim = 303 #TODO MAGIC NUMBER

        # display yt
        if plot_yt:

            yt_plot.imshow(ytof, log=True,
                           aspect='auto', cmap=self.color, origin='lower',
                           extent=[tof_axis_ms[0], tof_axis_ms[-1], 0, data.y.shape[0]-1])
            yt_plot.set_xlabel(u't (ms)')
            yt_plot.set_ylabel(u'y (pixel)')

            # display tof range in auto/manual TOF range    #FIXME
            autotmin = float(tof_range_auto[0])
            autotmax = float(tof_range_auto[1])
            self.display_tof_range(autotmin, autotmax, 'ms')

            tmin = autotmin*1e-3
            tmax = autotmax*1e-3

            t1 = yt_plot.canvas.ax.axvline(tmin, color='#072be2')
            t2 = yt_plot.canvas.ax.axvline(tmax, color='#072be2')

            y1 = yt_plot.canvas.ax.axhline(peak1, color='#00aa00')
            y2 = yt_plot.canvas.ax.axhline(peak2, color='#00aa00')

            if back_flag:
                yb1 = yt_plot.canvas.ax.axhline(back1, color='#aa0000')
                yb2 = yt_plot.canvas.ax.axhline(back2, color='#aa0000')

            if data.all_plot_axis.is_yt_ylog:
                yt_plot.canvas.ax.set_yscale('log')
            else:
                yt_plot.canvas.ax.set_yscale('linear')

            if data.all_plot_axis.yt_data_interval is None:
                yt_plot.canvas.ax.set_ylim(0,ylim)
                yt_plot.canvas.draw()
                [xmin,xmax] = yt_plot.canvas.ax.xaxis.get_view_interval()
                [ymin,ymax] = yt_plot.canvas.ax.yaxis.get_view_interval()
                data.all_plot_axis.yt_data_interval = [xmin, xmax, ymin, ymax]
                data.all_plot_axis.yt_view_interval = [xmin, xmax, ymin, ymax]
                yt_plot.toolbar.home_settings = [xmin, xmax, ymin, ymax]
            else:
                [xmin,xmax,ymin,ymax] = data.all_plot_axis.yt_view_interval
                yt_plot.canvas.ax.set_xlim([xmin,xmax])
                yt_plot.canvas.ax.set_ylim([ymin,ymax])
                yt_plot.canvas.draw()

        # display it
        if plot_it:
            it_plot.canvas.ax.plot(tof_axis_ms[0:-1],countstofdata, color='#0000aa')
            it_plot.canvas.ax.set_xlabel(u't (ms)')
#      u'\u03bcs
            it_plot.canvas.ax.set_ylabel(u'Counts')
            autotmin = float(tof_range_auto[0])
            autotmax = float(tof_range_auto[1])
            ta = it_plot.canvas.ax.axvline(autotmin/1000, color='#00aa00')
            tb = it_plot.canvas.ax.axvline(autotmax/1000, color='#00aa00')

            if data.all_plot_axis.is_it_ylog:
                it_plot.canvas.ax.set_yscale('log')
            else:
                it_plot.canvas.ax.set_yscale('linear')

            if data.all_plot_axis.it_data_interval is None:
                it_plot.canvas.draw()
                [xmin,xmax] = it_plot.canvas.ax.xaxis.get_view_interval()
                [ymin,ymax] = it_plot.canvas.ax.yaxis.get_view_interval()
                data.all_plot_axis.it_data_interval = [xmin,xmax,ymin,ymax]
                data.all_plot_axis.it_view_interval = [xmin,xmax,ymin,ymax]
                it_plot.toolbar.home_settings = [xmin,xmax,ymin,ymax]
            else:
                [xmin,xmax,ymin,ymax]=data.all_plot_axis.it_view_interval
                it_plot.canvas.ax.set_xlim([xmin,xmax])
                it_plot.canvas.ax.set_ylim([ymin,ymax])
                it_plot.canvas.draw()

        if plot_yi:
            xaxis = range(len(ycountsdata))
            yi_plot.canvas.ax.plot(ycountsdata,xaxis)
            yi_plot.canvas.ax.set_xlabel(u'counts')
            yi_plot.canvas.ax.set_ylabel(u'y (pixel)')

            if  data.all_plot_axis.yi_data_interval is None:    
                yi_plot.canvas.ax.set_ylim(0,ylim)

            y1peak = yi_plot.canvas.ax.axhline(peak1, color='#00aa00')
            y2peak = yi_plot.canvas.ax.axhline(peak2, color='#00aa00')
            if back_flag:
                y1back = yi_plot.canvas.ax.axhline(back1, color='#aa0000')
                y2back = yi_plot.canvas.ax.axhline(back2, color='#aa0000')

            if data.all_plot_axis.is_yi_xlog:
                yi_plot.canvas.ax.set_xscale('log')
            else:
                yi_plot.canvas.ax.set_xscale('linear')

            if data.all_plot_axis.yi_data_interval is None:
                yi_plot.canvas.draw()
                [xmin, xmax] = yi_plot.canvas.ax.xaxis.get_view_interval()
                [ymin, ymax] = yi_plot.canvas.ax.yaxis.get_view_interval()
                data.all_plot_axis.yi_data_interval = [xmin, xmax, ymin, ymax]
                data.all_plot_axis.yi_view_interval = [xmin, xmax, ymin, ymax]
                yi_plot.toolbar.home_settings = [xmin, xmax, ymin, ymax]
            else:
                [xmin, xmax, ymin, ymax] = data.all_plot_axis.yi_view_interval
                yi_plot.canvas.ax.set_xlim([xmin, xmax])
                yi_plot.canvas.ax.set_ylim([ymin, ymax])
                yi_plot.canvas.draw()

        # display ix
        if plot_ix:
            ix_plot.canvas.ax.plot(countsxdata, color='#0000aa')
            ix_plot.canvas.ax.set_xlabel(u'pixels')
            ix_plot.canvas.ax.set_ylabel(u'counts')
            ix_plot.canvas.ax.set_xlim(0,xlim)

            if low_res_flag:
                x1low = ix_plot.canvas.ax.axvline(lowRes1, color='#aa00aa')
                x2low = ix_plot.canvas.ax.axvline(lowRes2, color='#aa00aa')

            if data.all_plot_axis.is_ix_ylog:
                ix_plot.canvas.ax.set_yscale('log')
            else:
                ix_plot.canvas.ax.set_yscale('linear')

            if data.all_plot_axis.ix_data_interval is None:
                ix_plot.canvas.draw()
                [xmin,xmax] = ix_plot.canvas.ax.xaxis.get_view_interval()
                [ymin,ymax] = ix_plot.canvas.ax.yaxis.get_view_interval()
                data.all_plot_axis.ix_data_interval = [xmin,xmax,ymin,ymax]
                data.all_plot_axis.ix_view_interval = [xmin,xmax,ymin,ymax]
                ix_plot.toolbar.home_settings = [xmin,xmax,ymin,ymax]
            else:
                [xmin,xmax,ymin,ymax] = data.all_plot_axis.ix_view_interval
                ix_plot.canvas.ax.set_xlim([xmin,xmax])
                ix_plot.canvas.ax.set_ylim([ymin,ymax])
                ix_plot.canvas.draw()

        # save back data
        _data.active_data = data
        self.bigTableData[r,c] = _data

    def retrieve_tof_range(self, data):
        '''
        will retrieve the TOF (auto or manual) selected in microS
        '''

        # auto
        if self.ui.dataTOFautoMode.isChecked():
            return data.tof_range_auto

        else: #manual
            tof_min = self.ui.TOFmanualFromValue.value()
            tof_max = self.ui.TOFmanualToValue.value()

            if TOFmanualMicrosValue.isChecked():
                return [float(tof_min), float(tof_max)]
            else:
                tof_min = float(tof_min)*1000
                tof_max = float(tof_max)*1000
                return [tof_min, tof_max]

    def calculate_q_range(self, data):

        theta_rad = data.theta

        dMD = data.dMD
        _const = float(4) * math.pi * constants.mn * dMD / constants.h

        # retrieve tof from GUI
        [tof_min, tof_max] = self.retrieve_tof_range(data)

        q_min = _const * math.sin(theta_rad) / (tof_max * 1e-6) * float(1e-10)
        q_max = _const * math.sin(theta_rad) / (tof_min * 1e-6) * float(1e-10)

        return [q_min, q_max]

    def calculate_lambda_range(self, data):

        dMD = data.dMD
        _const = constants.h / (constants.mn * dMD)

        # retrieve tof from GUI
        [tof_min, tof_max] = self.retrieve_tof_range(data)

        lambda_min = _const * (tof_min * 1e-6) / float(1e-10)
        lambda_max = _const * (tof_max * 1e-6) / float(1e-10)

        return [lambda_min, lambda_max]


    def display_tof_range(self, tmin, tmax, units):
        '''
        will display the TOF min and max value in the metadata field
        according to the units selected
        '''
        #_tmin = tmin.copy()
        #_tmax = tmax.copy()

        _tmin = 1e-3 * float(tmin)
        _tmax = 1e-3 * float(tmax)

        stmin = str("%.2f" % _tmin)
        stmax = str("%.2f" % _tmax)

        self.ui.TOFmanualFromValue.setText(stmin)
        self.ui.TOFmanualToValue.setText(stmax)

    @log_call
    def plot_xy(self):
        '''
        X vs. Y plots for all channels.
        '''
        plots=[self.ui.xy_pp, self.ui.xy_mm, self.ui.xy_pm, self.ui.xy_mp]
        for i in range(len(self.active_data), 4):
            if plots[i].cplot is not None:
                plots[i].clear()
                plots[i].draw()
        imin=1e20
        imax=1e-20
        xynormed=[]
        for dataset in self.active_data[:4]:
            d=dataset.xydata/dataset.proton_charge
            xynormed.append(d)
            imin=min(imin, d[d>0].min())
            imax=max(imax, d.max())

        if len(xynormed)>1:
            self.ui.frame_xy_mm.show()
            if len(xynormed)==4:
                self.ui.frame_xy_sf.show()
            else:
                self.ui.frame_xy_sf.hide()
        else:
            self.ui.frame_xy_mm.hide()
            self.ui.frame_xy_sf.hide()

        for i, datai in enumerate(xynormed):
            if self.ui.tthPhi.isChecked():
                plots[i].clear()
                rad_per_pixel=dataset.det_size_x/dataset.dist_sam_det/dataset.xydata.shape[1]
                phi_range=datai.shape[0]*rad_per_pixel*180./pi
                tth_range=datai.shape[1]*rad_per_pixel*180./pi
                phi0=self.ui.refYPos.value()*rad_per_pixel*180./pi
                tth0=(dataset.dangle-dataset.dangle0)-(304-dataset.dpix)*rad_per_pixel*180./pi #TODO MAGIC NUMBER

                plots[i].imshow(datai, log=self.ui.logarithmic_colorscale.isChecked(), imin=imin, imax=imax,
                                aspect='auto', cmap=self.color, origin='lower',
                                extent=[tth_range+tth0, tth0, phi0, phi0-phi_range])
                plots[i].set_xlabel(u'2$\\Theta{}$ [°]')
                plots[i].set_ylabel(u'$\\phi{}$ [°]')
            else:
                plots[i].imshow(datai, log=self.ui.logarithmic_colorscale.isChecked(), imin=imin, imax=imax,
                                aspect='auto', cmap=self.color, origin='lower')
                plots[i].set_xlabel(u'x [pix]')
                plots[i].set_ylabel(u'y [pix]')
            plots[i].set_title(self.channels[i])
            if plots[i].cplot is not None:
                plots[i].cplot.set_clim([imin, imax])
            if plots[i].cplot is not None and self.ui.show_colorbars.isChecked() and plots[i].cbar is None:
                plots[i].cbar=plots[i].canvas.fig.colorbar(plots[i].cplot)
            plots[i].draw()

    @log_call
    def plot_xtof(self):
        '''
        X vs. ToF plots for all channels.
        '''
        imin=1e20
        imax=1e-20
        xtofnormed=[]
        ref_norm=self.getNorm()
        if ref_norm is not None:
            ref_norm=ref_norm.Rraw
            ref_norm=where(ref_norm>0, ref_norm, 1.)

        for dataset in self.active_data[:4]:
            d=dataset.xtofdata/dataset.proton_charge
            if self.ui.normalizeXTof.isChecked() and ref_norm is not None:
                # normalize all datasets for wavelength distribution
                d=d/ref_norm[newaxis, :]
            xtofnormed.append(d)
            imin=min(imin, d[d>0].min())
            imax=max(imax, d.max())
        lamda=self.active_data[self.active_channel].lamda
        tof=self.active_data[self.active_channel].tof

        plots=[self.ui.xtof_pp, self.ui.xtof_mm, self.ui.xtof_pm, self.ui.xtof_mp]
        for i in range(len(self.active_data), 4):
            if plots[i].cplot is not None:
                plots[i].clear()
                plots[i].draw()

        if len(xtofnormed)>1:
            self.ui.frame_xtof_mm.show()
            if len(xtofnormed)==4:
                self.ui.frame_xtof_sf.show()
            else:
                self.ui.frame_xtof_sf.hide()
        else:
            self.ui.frame_xtof_mm.hide()
            self.ui.frame_xtof_sf.hide()
        for i, datai in enumerate(xtofnormed):
            if self.ui.xLamda.isChecked():
                plots[i].imshow(datai[::-1], log=self.ui.logarithmic_colorscale.isChecked(), imin=imin, imax=imax,
                                aspect='auto', cmap=self.color, extent=[lamda[0], lamda[-1], 0, datai.shape[0]-1])
                plots[i].set_xlabel(u'$\\lambda{}$ [Å]')
            else:
                plots[i].imshow(datai[::-1], log=self.ui.logarithmic_colorscale.isChecked(), imin=imin, imax=imax,
                                aspect='auto', cmap=self.color, extent=[tof[0]*1e-3, tof[-1]*1e-3, 0, datai.shape[0]-1])
                plots[i].set_xlabel(u'ToF [ms]')
            plots[i].set_title(self.channels[i])
            plots[i].set_ylabel(u'x [pix]')
            if plots[i].cplot is not None:
                plots[i].cplot.set_clim([imin, imax])
            if plots[i].cplot is not None and self.ui.show_colorbars.isChecked() and plots[i].cbar is None:
                plots[i].cbar=plots[i].canvas.fig.colorbar(plots[i].cplot)
            plots[i].draw()

    @log_call
    def plot_projections(self, preserve_lim=False):
        '''
        Create projections of the data on the x and y axes.
        The x-projection can also be done be means of quantile calculation,
        which means that the ToF intensities are calculation which are
        exceeded by a certain number of points. This can be helpful to better
        separate the specular reflection from bragg-sheets
        '''
        if self.active_data is None:
            return

        if instrument.NAME=="REF_L": #TODO HARDCODED INSTRUMENT
            data = self.active_data
        else:
            data=self.active_data[self.active_channel]

        xproj=data.xdata
        yproj=data.ydata

        x_peak=self.ui.refXPos.value()
        x_width=self.ui.refXWidth.value()
        y_pos=self.ui.refYPos.value()
        y_width=self.ui.refYWidth.value()
        bg_pos=self.ui.bgCenter.value()
        bg_width=self.ui.bgWidth.value()

        if preserve_lim:
            xview=self.ui.x_project.canvas.ax.axis()
            yview=self.ui.y_project.canvas.ax.axis()
        xxlim=(0, len(xproj)-1)
        xylim=(xproj[xproj>0].min(), xproj.max()*2)
        yxlim=(0, len(yproj)-1)
        yylim=(yproj[yproj>0].min(), yproj.max()*2)

        if self._x_projection is None:
            self._x_projection=self.ui.x_project.plot(xproj, color='blue')[0]
            self.ui.x_project.set_xlabel(u'x [pix]')
            self.ui.x_project.set_ylabel(u'I$_{max}$')
            xpos=self.ui.x_project.canvas.ax.axvline(x_peak, color='black')
            xleft=self.ui.x_project.canvas.ax.axvline(x_peak-x_width/2., color='red')
            xright=self.ui.x_project.canvas.ax.axvline(x_peak+x_width/2., color='red')
            xleft_bg=self.ui.x_project.canvas.ax.axvline(bg_pos-bg_width/2., color='black')
            xright_bg=self.ui.x_project.canvas.ax.axvline(bg_pos+bg_width/2., color='black')

            self._y_projection=self.ui.y_project.plot(yproj, color='blue')[0]
            self.ui.y_project.set_xlabel(u'y [pix]')
            self.ui.y_project.set_ylabel(u'I$_{max}$')
            yreg_left=self.ui.y_project.canvas.ax.axvline(y_pos-y_width/2., color='green')
            yreg_right=self.ui.y_project.canvas.ax.axvline(y_pos+y_width/2., color='green')
            ybg=self.ui.y_project.canvas.ax.axhline(self.y_bg, color='black')
            self.proj_lines=(xleft, xpos, xright, xleft_bg, xright_bg, yreg_left, yreg_right, ybg)
        else:
            self._x_projection.set_ydata(xproj)
            self._y_projection.set_ydata(yproj)
            lines=self.proj_lines
            lines[0].set_xdata([x_peak-x_width/2., x_peak-x_width/2.])
            lines[1].set_xdata([x_peak, x_peak])
            lines[2].set_xdata([x_peak+x_width/2., x_peak+x_width/2.])
            lines[3].set_xdata([bg_pos-bg_width/2., bg_pos-bg_width/2.])
            lines[4].set_xdata([bg_pos+bg_width/2., bg_pos+bg_width/2.])
            lines[5].set_xdata([y_pos-y_width/2., y_pos-y_width/2.])
            lines[6].set_xdata([y_pos+y_width/2., y_pos+y_width/2.])
            lines[7].set_ydata([self.y_bg, self.y_bg])
        if preserve_lim:
            self.ui.x_project.canvas.ax.axis(xview)
            self.ui.y_project.canvas.ax.axis(yview)
        if self.ui.logarithmic_y.isChecked():
            self.ui.x_project.set_yscale('log')
            self.ui.y_project.set_yscale('log')
        else:
            self.ui.x_project.set_yscale('linear')
            self.ui.y_project.set_yscale('linear')
        self.ui.x_project.canvas.ax.set_xlim(*xxlim)
        self.ui.x_project.canvas.ax.set_ylim(*xylim)
        self.ui.y_project.canvas.ax.set_xlim(*yxlim)
        self.ui.y_project.canvas.ax.set_ylim(*yylim)

        self.ui.x_project.draw()
        self.ui.y_project.draw()

    @log_call
    def calc_refl(self):
        if self.active_data is None:
            return False
        data=self.active_data[self.active_channel]
        if self.ui.directPixelOverwrite.value()>=0:
            dpix=self.ui.directPixelOverwrite.value()
        else:
            dpix=None
        if self.ui.trustDANGLE.isChecked():
            try:
                tth=data.dangle-float(self.ui.dangle0Overwrite.text())
            except ValueError:
                tth=None
        else:
            grad_per_pixel=data.det_size_x/data.dist_sam_det/data.xydata.shape[1]*180./pi
            tth=data.sangle*2.-(data.dpix-self.ui.refXPos.value())*grad_per_pixel
        bg_poly_regions=None
        # get additional background options from dialog, if it has been opened
        if self.background_dialog:
            bg_tof_constant=self.background_dialog.ui.presumeIofLambda.isChecked()
            if self.background_dialog.ui.polyregionActive.isChecked():
                bg_poly_regions=list(self.background_dialog.polygons)
            bg_scale=self.background_dialog.ui.scaleFactor.value()
        else:
            bg_tof_constant=False
            bg_scale=1.
        if type(self.active_data.number) is list:
            number='['+",".join(map(str, self.active_data.number))+']'
        else:
            number=str(self.active_data.number)
        normalization=self.getNorm()
        options=dict(
            x_pos=self.ui.refXPos.value(),
            x_width=self.ui.refXWidth.value(),
            y_pos=self.ui.refYPos.value(),
            y_width=self.ui.refYWidth.value(),
            bg_pos=self.ui.bgCenter.value(),
            bg_width=self.ui.bgWidth.value(),
            scale=10**self.ui.refScale.value(),
            extract_fan=self.ui.fanReflectivity.isChecked(),
            P0=self.ui.rangeStart.value(),
            PN=self.ui.rangeEnd.value(),
            number=number,
            tth=tth,
            dpix=dpix,
            bg_tof_constant=bg_tof_constant,
            bg_poly_regions=bg_poly_regions,
            # scale background by 0. if BG box not checked
            bg_scale_factor=(bg_scale*self.ui.bgActive.isChecked()),
            normalization=normalization,
        )

        self.refl=Reflectivity(data, **options)
        self.ui.datasetAi.setText(u"%.3f°"%(self.refl.ai*180./pi))
        self.ui.datasetROI.setText(u"%.4g"%(self.refl.Iraw.sum()))
        if normalization is not None:
            if self.ui.fanReflectivity.isChecked():
                self.cut_areas['fan']=(self.ui.rangeStart.value(), self.ui.rangeEnd.value())
            else:
                self.cut_areas[normalization]=(self.ui.rangeStart.value(), self.ui.rangeEnd.value())
        return True

    @log_call
    def plot_refl(self, preserve_lim=False):
        return #REMOVEME
        '''
    Calculate and display the reflectivity from the current dataset
    and any dataset stored. Intensities from direct beam
    measurements can be used for normalization.
    '''
        if not self.calc_refl():
            return
        options=self.refl.options
        P0=len(self.refl.Q)-self.ui.rangeStart.value()
        PN=self.ui.rangeEnd.value()

        if len(self.ui.refl.toolbar._views)>0:
            spos=self.ui.refl.toolbar._views._pos
            view=self.ui.refl.toolbar._views[spos]
            position=self.ui.refl.toolbar._positions[spos]
        else:
            view=None

        self.ui.refl.clear()
        if options['normalization']:
            ymin=1e50
            ymax=1e-50
            ynormed=self.refl.R[PN:P0]
            if len(ynormed[ynormed>0])>=2:
                ymin=min(ymin, ynormed[ynormed>0].min())
                ymax=max(ymax, ynormed.max())
                self.ui.refl.errorbar(self.refl.Q[PN:P0], ynormed,
                                      yerr=self.refl.dR[PN:P0], label='Active', lw=2, color='black')
            else:
                self.ui.refl.canvas.ax.text(0.5, 0.5,
                                            u'No points to show\nin active dataset!',
                                            horizontalalignment='center',
                                            verticalalignment='center',
                                            fontsize=14,
                                            transform=self.ui.refl.canvas.ax.transAxes)
            for i, refli in enumerate(self.reduction_list):
                #self.ui.refl.semilogy(x, y/self.ref_norm, label=str(settings['index']))
                P0i=len(refli.Q)-refli.options['P0']
                PNi=refli.options['PN']
                ynormed=refli.R[PNi:P0i]
                try:
                    ymin=min(ymin, ynormed[ynormed>0].min())
                except ValueError:
                    pass
                ymax=max(ymax, ynormed.max())
                self.ui.refl.errorbar(refli.Q[PNi:P0i], ynormed,
                                      yerr=refli.dR[PNi:P0i], label=str(refli.options['number']),
                                      color=self._refl_color_list[i%len(self._refl_color_list)])
            self.ui.refl.set_ylabel(u'I')
            self.ui.refl.canvas.ax.set_ylim((ymin*0.9, ymax*1.1))
            self.ui.refl.set_xlabel(u'Q$_z$ [Å$^{-1}$]')
        else:
            try:
                ymin=min(self.refl.BG[self.refl.BG>0].min(), self.refl.I[self.refl.I>0].min())
            except ValueError:
                try:
                    ymin=self.refl.I[self.refl.I>0].min()
                except ValueError:
                    ymin=1e-10
            ymax=max(self.refl.BG.max(), self.refl.I.max())
            self.ui.refl.errorbar(self.refl.lamda, self.refl.I, yerr=self.refl.dI, label='I-'+options['number'])
            self.ui.refl.errorbar(self.refl.lamda, self.refl.BG, yerr=self.refl.dBG, label='BG-'+options['number'])
            self.ui.refl.set_ylabel(u'I')
            self.ui.refl.canvas.ax.set_ylim((ymin*0.9, ymax*1.1))
            self.ui.refl.set_xlabel(u'$\\lambda{}$ [Å]')
        if self.ui.logarithmic_y.isChecked():
            self.ui.refl.set_yscale('log')
        else:
            self.ui.refl.set_yscale('linear')
        self.ui.refl.legend()
        if view is not None:
            self.ui.refl.toolbar.push_current()
            self.ui.refl.toolbar._views.push(view)
            self.ui.refl.toolbar._positions.push(position)
        if preserve_lim:
            # reset the last zoom position
            self.ui.refl.toolbar._update_view()
        else:
            self.ui.refl.toolbar._views._pos=0
            self.ui.refl.toolbar._positions._pos=0
        self.ui.refl.draw()
        self.ui.refl.toolbar.set_history_buttons()

    @log_call
    def plot_offspec(self):
        '''
        Create an offspecular plot for all channels of the datasets in the
        reduction list. The user can define upper and lower bounds for the 
        plotted intensity and select the coordinates to be ither kiz-kfz vs. Qz,
        Qx vs. Qz or kiz vs. kfz.
        '''
        plots=[self.ui.offspec_pp, self.ui.offspec_mm,
               self.ui.offspec_pm, self.ui.offspec_mp]
        for plot in plots:
            plot.clear()
        for i in range(len(self.active_data), 4):
            if plots[i].cplot is not None:
                plots[i].draw()
        Imin=10**self.ui.offspecImin.value()
        Imax=10**self.ui.offspecImax.value()
        Qzmax=0.01
        for item in self.reduction_list:
            if type(item.origin) is list:
                flist=[origin[0] for origin in item.origin]
                data_all=NXSMultiData(flist, **item.read_options)
            else:
                fname=item.origin[0]
                data_all=NXSData(fname, **item.read_options)
            for i, channel in enumerate(self.ref_list_channels):
                plot=plots[i]
                selected_data=data_all[channel]
                offspec=OffSpecular(selected_data, **item.options)
                P0=len(selected_data.tof)-item.options['P0']
                PN=item.options['PN']
                Qzmax=max(offspec.Qz[int(item.options['x_pos']), PN:P0].max(), Qzmax)
                ki_z, kf_z, Qx, Qz, S=offspec.ki_z, offspec.kf_z, offspec.Qx, offspec.Qz, offspec.S
                if self.ui.kizmkfzVSqz.isChecked():
                    plot.pcolormesh((ki_z-kf_z)[:, PN:P0],
                                    Qz[:, PN:P0], S[:, PN:P0], log=True,
                                    imin=Imin, imax=Imax, cmap=self.color,
                                    shading='gouraud')
                elif self.ui.qxVSqz.isChecked():
                    plot.pcolormesh(Qx[:, PN:P0],
                                    Qz[:, PN:P0], S[:, PN:P0], log=True,
                                    imin=Imin, imax=Imax, cmap=self.color,
                                    shading='gouraud')
                else:
                    plot.pcolormesh(ki_z[:, PN:P0],
                                    kf_z[:, PN:P0], S[:, PN:P0], log=True,
                                    imin=Imin, imax=Imax, cmap=self.color,
                                    shading='gouraud')
        for i, channel in enumerate(self.ref_list_channels):
            plot=plots[i]
            if self.ui.kizmkfzVSqz.isChecked():
                plot.canvas.ax.set_xlim([-0.03, 0.03])
                plot.canvas.ax.set_ylim([0., Qzmax])
                plot.set_xlabel(u'k$_{i,z}$-k$_{f,z}$ [Å$^{-1}$]')
                plot.set_ylabel(u'Q$_z$ [Å$^{-1}$]')
            elif self.ui.qxVSqz.isChecked():
                plot.canvas.ax.set_xlim([-0.001, 0.001])
                plot.canvas.ax.set_ylim([0., Qzmax])
                plot.set_xlabel(u'Q$_x$ [Å$^{-1}$]')
                plot.set_ylabel(u'Q$_z$ [Å$^{-1}$]')
            else:
                plot.canvas.ax.set_xlim([0., Qzmax/2.])
                plot.canvas.ax.set_ylim([0., Qzmax/2.])
                plot.set_xlabel(u'k$_{i,z}$ [Å$^{-1}$]')
                plot.set_ylabel(u'k$_{f,z}$ [Å$^{-1}$]')
            plot.set_title(channel)
            if plot.cplot is not None:
                plot.cplot.set_clim([Imin, Imax])
                if self.ui.show_colorbars.isChecked() and plots[i].cbar is None:
                    plots[i].cbar=plots[i].canvas.fig.colorbar(plots[i].cplot)
            plot.draw()

    @log_call
    def auto_tof_switch(self, bool):
        '''
        Reached by the TOF auto switch
        '''
        if not self._auto_tof_flag:
            self.ui.TOFmanualFromLabel.setEnabled(not bool)
            self.ui.TOFmanualFromValue.setEnabled(not bool)
            self.ui.TOFmanualFromUnitsValue.setEnabled(not bool)
            self.ui.TOFmanualToLabel.setEnabled(not bool)
            self.ui.TOFmanualToValue.setEnabled(not bool)
            self.ui.TOFmanualToUnitsValue.setEnabled(not bool)
#      self.ui.TOFmanualMsValue.setEnabled(not bool)
#      self.ui.TOFmanualMicrosValue.setEnabled(not bool)
            self._auto_tof_flag = True
        self.plot_overview_REFL(plot_yt=True, plot_yi=True, plot_it=True, plot_ix=True)

    def manual_tof_selection(self):
        # first save the manual parameters
        #[row,col] = self.getCurrentRowColumnSelected()
        row = self._cur_row_selected
        col = self._cur_column_selected
        _data = self.bigTableData[row,col]
        _active_data = _data.active_data

        # retrieve tof parameters defined by user
        _valueFrom = float(self.ui.TOFmanualFromValue.text())
        _valueTo = float(self.ui.TOFmanualToValue.text())
#    if self.ui.TOFmanualMsValue.isChecked(): # ms units
        _valueFrom *= 1000
        _valueTo *= 1000 

        _active_data.tof_range = [_valueFrom, _valueTo]
        _data.active_data = _active_data
        self.bigTableData[row,col] = _data

        self.plot_overview_REFL(plot_yt=True, plot_yi=True, plot_it=True, plot_ix=True)

    def manual_tof_switch(self, bool):
        '''
        Reached by the TOF manual switch
        '''
        if self._auto_tof_flag:
            self.ui.TOFmanualFromLabel.setEnabled(bool)
            self.ui.TOFmanualFromValue.setEnabled(bool)
            self.ui.TOFmanualFromUnitsValue.setEnabled(bool)
            self.ui.TOFmanualToLabel.setEnabled(bool)
            self.ui.TOFmanualToValue.setEnabled(bool)
            self.ui.TOFmanualToUnitsValue.setEnabled(bool)
#      self.ui.TOFmanualMsValue.setEnabled(bool)
#      self.ui.TOFmanualMicrosValue.setEnabled(bool)
            self._auto_tof_flag = False
        self.plot_overview_REFL(plot_yt=True, plot_yi=True, plot_it=True, plot_ix=True)

    #def tof_micros_switch(self, bool):
        #'''
        #Will change the ms->micros labels in the TOF widgets
        #and the value of tof fields
        #'''
        #_units = u'\u03bcs'
        #self.ui.TOFmanualFromUnitsValue.setText(_units)
        #self.ui.TOFmanualToUnitsValue.setText(_units) 
        ## change units
        #self.change_tof_units('micros')

        ## change value as well from ms -> microS
        ## if bool == true => ms -> microS
        ## if bool == false => microS -> ms

        #_valueFrom = float(self.ui.TOFmanualFromValue.text())
        #if bool: # ms -> microS
            #new_valueFrom = _valueFrom * 1000
        #else: # microS -> ms
            #new_valueFrom = _valueFrom / 1000
        #newStr = "%.2f"%new_valueFrom
        #self.ui.TOFmanualFromValue.setText(newStr)

        #_valueTo = float(self.ui.TOFmanualToValue.text())
        #if bool: # ms -> microS
            #new_valueTo = _valueTo * 1000
        #else: # microS -> ms
            #new_valueTo = _valueTo / 1000
        #newStr = "%.2f"%new_valueTo
        #self.ui.TOFmanualToValue.setText(newStr)

    #def tof_ms_switch(self, bool):
        #'''
        #Will change the microS->ms labels in the TOF widgets
        #and the value of tof fields
        #'''
        #_units = u'ms'
        #self.ui.TOFmanualFromUnitsValue.setText(_units)
        #self.ui.TOFmanualToUnitsValue.setText(_units) 
        ## change units
        #self.change_tof_units('ms')

    def change_tof_units(self, new_units):
        '''
        Change the TOF value according to the new units selected
        '''
        tof_from = self.ui.TOFmanualFromValue.text().strip()
        tof_to = self.ui.TOFmanualToValue.text().strip()

        # make sure the 'from' value is a float
        if not tof_from: 
            tof_from_float = 0.
        else:
            try:
                tof_from_float = float(tof_from)
            except ValueError:
                tof_from_float = 0.
        self.ui.TOFmanualFromValue.setText(str(tof_from_float))

        # make sure the 'to' value is a float
        if not tof_from: 
            tof_to_float = 0.
        else:
            try:
                tof_to_float = float(tof_to)
            except ValueError:
                tof_to_float = 0.
        self.ui.TOFmanualToValue.setText(str(tof_to_float))

    @log_call
    def change_offspec_colorscale(self):
        plots=[self.ui.offspec_pp, self.ui.offspec_mm,
               self.ui.offspec_pm, self.ui.offspec_mp]
        Imin=10**self.ui.offspecImin.value()
        Imax=10**self.ui.offspecImax.value()
        if Imin>=Imax:
            return
        for i, ignore in enumerate(self.ref_list_channels):
            plot=plots[i]
            if plot.cplot is not None:
                for item in plot.canvas.ax.collections:
                    item.set_clim(Imin, Imax)
            plot.draw()

    @log_call
    def clip_offspec_colorscale(self):
        plots=[self.ui.offspec_pp, self.ui.offspec_mm,
               self.ui.offspec_pm, self.ui.offspec_mp]
        Imin=1e10
        for i, ignore in enumerate(self.ref_list_channels):
            plot=plots[i]
            if plot.cplot is not None:
                for item in plot.canvas.ax.collections:
                    I=item.get_array()
                    Imin=min(Imin, I[I>0].min())
        for i, ignore in enumerate(self.ref_list_channels):
            plot=plots[i]
            if plot.cplot is not None:
                for item in plot.canvas.ax.collections:
                    I=item.get_array()
                    I[I<=0]=Imin
                    item.set_array(I)
            plot.draw()

    @log_call
    def change_gisans_colorscale(self):
        plots=[self.ui.gisans_pp, self.ui.gisans_mm,
               self.ui.gisans_pm, self.ui.gisans_mp]
        Imin=10**self.ui.gisansImin.value()
        Imax=10**self.ui.gisansImax.value()
        if Imin>=Imax:
            return
        for i, ignore in enumerate(self.ref_list_channels):
            plot=plots[i]
            if plot.cplot is not None:
                plot.cplot.set_clim(Imin, Imax)
            plot.draw()

    @log_call
    def plot_gisans(self):
        '''
        Create GISANS plots of the current dataset with Qy-Qz maps.
        '''
        plots=[self.ui.gisans_pp, self.ui.gisans_mm, self.ui.gisans_pm, self.ui.gisans_mp]
        norm=self.getNorm()
        if norm is None:
            for plot in plots:
                plot.clear()
                plot.draw()
            return
        for i, plot in enumerate(plots):
            if i>=len(self.active_data):
                if plot.cplot is not None:
                    plot.clear()
                    plot.draw()
            else:
                plot.clear()
                plot.canvas.fig.text(0.3, 0.5, "Pease wait for calculation\nto be finished.")
                plot.draw()
        info('Calculating GISANS projection...')
        self.updateEventReadout(0.)

        options=dict(self.refl.options)
        region=where(norm.Rraw>(norm.Rraw.max()*0.1))[0]
        options['P0']=len(norm.Rraw)-region[-1]
        options['PN']=region[0]
        if self._gisansThread:
            self._gisansThread.finished.disconnect()
            self._gisansThread.terminate()
            self._gisansThread.wait(100)
            self._gisansThread=None
        self._gisansThread=gisansCalcThread(self.active_data, options)
        self._gisansThread.updateProgress.connect(self.updateEventReadout)
        self._gisansThread.finished.connect(self._plot_gisans)
        self._gisansThread.start()


    @log_call
    def update_daslog(self):
        '''
        Write parameters from all file daslogs to the tables in the 
        daslog tab.
        '''
        table=self.ui.daslogTableBox
        table.setRowCount(0)
        table.sortItems(-1)
        table.setColumnCount(len(self.channels)+2)
        table.setHorizontalHeaderLabels(['Name']+self.channels+['Unit'])
        for j, key in enumerate(sorted(self.active_data[0].logs.keys(), key=lambda s: s.lower())):
            table.insertRow(j)
            table.setItem(j, 0, QtGui.QTableWidgetItem(key))
            table.setItem(j, len(self.channels)+1,
                          QtGui.QTableWidgetItem(self.active_data[0].log_units[key]))
            for i, _channel, data in self.active_data.numitems():
                item=QtGui.QTableWidgetItem(u'%g'%data.logs[key])
                item.setToolTip(u'MIN: %g   MAX: %g'%(data.log_minmax[key]))
                table.setItem(j, i+1, item)
        table.resizeColumnsToContents()

###### GUI actions

    @log_call
    def fileOpenDialog(self):
        '''
        Show a dialog to open a new file.
        '''
        if self.ui.histogramActive.isChecked():
            filter_=u'Histo Nexus (*histo.nxs);;All (*.*)'
        elif self.ui.oldFormatActive.isChecked():
            filter_=u'Old Nexus (*.nxs);;All (*.*)'
        else:
            filter_=u'Event Nexus (*event.nxs);;All (*.*)'
        filenames=QtGui.QFileDialog.getOpenFileNames(self, u'Open NXS file...',
                                                     directory=self.active_folder,
                                                     filter=filter_)
        if filenames:
            filenames=map(unicode, filenames)
            if len(filenames)==1:
                self.fileOpen(filenames[0])
            else:
                self.automaticExtraction(filenames)

    @log_call
    def fileOpenSumDialog(self):
        '''
        Show a dialog to open a set of files and sum them together.
        '''
        if self.ui.histogramActive.isChecked():
            filter_=u'Histo Nexus (*histo.nxs);;All (*.*)'
        elif self.ui.oldFormatActive.isChecked():
            filter_=u'Old Nexus (*.nxs);;All (*.*)'
        else:
            filter_=u'Event Nexus (*event.nxs);;All (*.*)'
        filenames=QtGui.QFileDialog.getOpenFileNames(self, u'Open NXS file...',
                                                     directory=self.active_folder,
                                                     filter=filter_)
        if filenames:
            filenames=map(unicode, filenames)
            self.fileOpenSum(filenames)

    @log_call
    def fileOpenList(self):
        '''
        Called when a new file is selected from the file list.
        '''
        if self.auto_change_active:
            return
        item=self.ui.file_list.currentItem()
        name=unicode(item.text())

        # check if user wants to add this/those files to a previous selected box
        do_add = False
        #if self.ui.addRunNumbers.isEnabled() and self.ui.addRunNumbers.isChecked():
            #do_add = True

        # only reload if filename was actually changed or file was modified
        self.fileOpen(os.path.join(self.active_folder, name), do_add=do_add)


    def  is_working_with_data(self):
        if self.ui.dataNormTabWidget.currentIndex() == 0: #data
            return True
        else:
            return False

    def is_with_auto_peak_finder(self):
        if self.ui.actionAutomaticPeakFinder.isChecked():
            return True
        else:
            return False

    #@log_call
    def openByNumber(self):
        OpenRunNumber(self)
        PopulateReductionTable(self)
        # selection
        _row = self._prev_row_selected
        _col = self._prev_col_selected
        self.ui.reductionTable.setRangeSelected(QtGui.QTableWidgetSelectionRange(_row, _col, _row, _col), True)

        DisplayPlots(self)

    @waiting_effects
    def find_peak_back(self):

        bigTableData = self.bigTableData
        if bigTableData[0,0] is None:
            return

        #[row,col] = self.getCurrentRowColumnSelected()
        row = self._cur_row_selected
        col = self._cur_column_selected
        _data = bigTableData[row, col]
        _active_data = _data.active_data

        ycountsdata = _active_data.ycountsdata
        pf = PeakFinder(range(len(ycountsdata)), ycountsdata)
        peaks = pf.get_peaks()
        main_peak = peaks[0]
        peak1 = int(main_peak[0] - main_peak[1])
        peak2 = int(main_peak[0] + main_peak[1])
        _active_data.peak  = [peak1, peak2]

        backOffsetFromPeak = self.ui.autoBackSelectionWidth.value()
        back1 = int(peak1 - backOffsetFromPeak)
        back2 = int(peak2 + backOffsetFromPeak)
        _active_data.back = [back1, back2]

        _data.active_data = _active_data
        bigTableData[row, col] = _data
        self.bigTableData = bigTableData

        self.plot_overview_REFL(plot_yt=True, plot_yi=True, plot_it=True, plot_ix=True)

    @log_call
    def nextFile(self):
        item=self.ui.file_list.currentRow()
        if (item+1)<self.ui.file_list.count():
            self.ui.file_list.setCurrentRow(item+1)

    @log_call
    def prevFile(self):
        item=self.ui.file_list.currentRow()
        if item>0:
            self.ui.file_list.setCurrentRow(item-1)

    @log_call
    def loadExtraction(self, filename=None):
        '''
        Analyse an already extracted dataset header to reload all settings
        used for this extraction for further processing.
        '''
        if filename is None and self._pending_header is None:
            filename=QtGui.QFileDialog.getOpenFileName(self, u'Create extraction from file header...',
                                                       directory=paths.results,
                                                       filter=u'Extracted Dataset (*.dat)')
        if filename==u'':
            return

        self.clearRefList(do_plot=False)
        if self._pending_header is None:
            text=unicode(open(filename, 'rb').read(), 'utf8')
            header=[]
            for line in text.splitlines():
                if not line.startswith('#'):
                    break
                header.append(line)
            header='\n'.join(header)
            from_backup=False
        else:
            header=self._pending_header
            self._pending_header=None
            from_backup=True
        try:
            parser=HeaderParser(header, parse_meta=not from_backup)
        except:
            warning('Could not evaluate header information, probably the wrong format:\n\n',
                    exc_info=True)
            return
        info('Reloading data from information in file header...')
        parser.parse(callback=self.updateEventReadout)
        info('Data loaded')
        # updating GUI and attributes
        for norm, norm_data in zip(parser.norms, parser.norm_data):
            self.refl=norm
            self.active_data=norm_data
            self.setNorm(do_plot=False, do_remove=False)
        for refl in parser.refls:
            self.refl=refl
            self.addRefList(do_plot=False)
        # update global export options
        if 'Global Options' in parser.section_data:
            export.sampleSize=parser.section_data['Global Options']['sample_length']
        # set settings for the dataset added last
        self.auto_change_active=True
        self.ui.refXPos.setValue(refl.options['x_pos'])
        self.ui.refXWidth.setValue(refl.options['x_width'])
        self.ui.refYPos.setValue(refl.options['y_pos'])
        self.ui.refYWidth.setValue(refl.options['y_width'])
        self.ui.bgCenter.setValue(refl.options['bg_pos'])
        self.ui.bgWidth.setValue(refl.options['bg_width'])
        self.ui.refScale.setValue(log10(refl.options['scale']))
        self.auto_change_active=False
        # load the last file in the list to be in the right directory and trigger plotting
        if type(refl.origin) is list:
            self.fileOpenSum([item[0] for item in refl.origin])
        else:
            self.fileOpen(refl.origin[0])
        self.ref_list_channels=list(self.active_data.keys())

    @log_input
    def cutPoints(self):
        norm=self.getNorm()
        if norm is None:
            return
        region=where(norm.Rraw>=(norm.Rraw.max()*0.05))[0]
        P0=len(norm.Rraw)-region[-1]
        PN=region[0]
        self.ui.rangeStart.setValue(P0)
        self.ui.rangeEnd.setValue(PN)
        info('Changed Cut Points to area with at least 5% of maximum incident intensity')

    @log_call
    def autoRef(self):
        '''
        Starting of the active dataset continue to add all subsequent datasets until the incident
        angle get smaller again. Quick method to create a full reflectivity automatically.
        '''
        if self.getNorm() is None:
            warning('Can only use Auto Reflectivity on normalized total reflection dataset')
            return
        self.clearRefList(do_plot=False)
        self.normalizeTotalReflection()
        self.addRefList(do_plot=False)
        for ignore in range(10):
            last_ai=self.refl.ai
            self.nextFile()
            if self.refl.ai<(last_ai-0.001):
                break
            self.normalizeTotalReflection()
            self.addRefList(do_plot=False)
        self.stripOverlap()
        self.prevFile()

    @log_call
    def stripOverlap(self):
        '''
        Remove overlapping points in the reflecitviy, cutting always from the lower Qz
        measurements.
        '''
        if len(self.reduction_list)<2:
            warning('You need to have at least two datasets in the reduction table')
            return
        for idx, item in enumerate(self.reduction_list[:-1]):
            next_item=self.reduction_list[idx+1]
            end_idx=next_item.Q.shape[0]-next_item.options['P0']
            overlap_idx=where(item.Q>=next_item.Q[end_idx-1])[0][-1]
            self.ui.reductionTable.setItem(idx, 3,
                                           QtGui.QTableWidgetItem(str(overlap_idx)))

    @log_call
    def onPathChanged(self, base, folder):
        '''
        Update the file list and create a watcher to update the list again if a new file was
        created.
        '''
        self.active_folder=folder

    @log_call
    def reloadFile(self):
        self.fileOpen(os.path.join(self.active_folder, self.active_file))

    @log_call
    def updateLabels(self):
        '''
        Write file metadata to the labels in the overview tab.
        '''

        if instrument.NAME == "REF_M": #TODO HARDCODED INSTRUMENT

            d=self.active_data[self.active_channel]

            try:
                dangle0=u"%.3f° (%.3f°)"%(float(self.ui.dangle0Overwrite.text()), d.dangle0)
            except ValueError:
                dangle0=u"%.3f°"%(d.dangle0)
            if self.ui.directPixelOverwrite.value()>=0:
                dpix=u"%.1f (%.1f)"%(self.ui.directPixelOverwrite.value(), d.dpix)
            else:
                dpix=u"%.1f"%d.dpix
            self.ui.datasetLambda.setText(u"%.2f (%.2f-%.2f) Å"%(self.active_data.lambda_center,
                                                                  self.active_data.lambda_center-1.5,
                                                                  self.active_data.lambda_center+1.5))
            self.ui.datasetPCharge.setText(u"%.3e"%d.proton_charge)
            self.ui.datasetTime.setText(u"%i s"%d.total_time)
            self.ui.datasetTotCounts.setText(u"%.4e"%d.total_counts)
            self.ui.datasetRate.setText(u"%.1f cps"%(d.total_counts/d.total_time))
            self.ui.datasetDangle.setText(u"%.3f°"%d.dangle)
            self.ui.datasetDangle0.setText(dangle0)
            self.ui.datasetSangle.setText(u"%.3f°"%d.sangle)
            self.ui.datasetDirectPixel.setText(dpix)
            self.ui.currentChannel.setText('<b>%s</b> (%s)&nbsp;&nbsp;&nbsp;Type: %s&nbsp;&nbsp;&nbsp;Current State: <b>%s</b>'%(
                self.active_data.number,
                self.active_data.experiment,
                self.active_data.measurement_type,
                self.active_channel))

        else: #REF_L

            d = self.active_data
        #  if self.ui.dataNormTabWidget.currentIndex() == 0:
        #   self.ui.dataNameOfFile.setText('%s'%d.filename)
        # else:
            #  self.ui.normNameOfFile.setText('%s'%d.filename)

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

    @log_call
    def toggleColorbars(self):
        if instrument.NAME == 'REF_M': #TODO HARDCODED INSTRUMENT
            if not self.auto_change_active:
                plots=[self.ui.xy_pp, self.ui.xy_mp, self.ui.xy_pm, self.ui.xy_mm,
                       self.ui.xtof_pp, self.ui.xtof_mp, self.ui.xtof_pm, self.ui.xtof_mm,
                       self.ui.xy_overview, self.ui.xtof_overview,
                       self.ui.offspec_pp, self.ui.offspec_mp, self.ui.offspec_pm, self.ui.offspec_mm]
                for plot in plots:
                    plot.clear_fig()
                self.overview_lines=None
                self.plotActiveTab()

    @log_call
    def toggleHide(self):
        plots=[self.ui.frame_xy_mm, self.ui.frame_xy_sf, self.ui.frame_xtof_mm, self.ui.frame_xtof_sf,
               self.ui.frame_gisans_pp, self.ui.frame_gisans_mm, self.ui.frame_gisans_sf]
        if self.ui.hide_plots.isChecked():
            for plot in plots:
                plot.do_hide=True
        else:
            for plot in plots:
                plot.show()
                plot.do_hide=False
        self.ui.eventModeEntries.hide()

    @log_call
    def changeRegionValues(self):
        '''
        Called when the reflectivity extraction region has been changed.
        Sets up a trigger to replot the reflectivity with a delay so
        a subsequent change can occur without several replots.
        '''
        if self.auto_change_active or self.proj_lines is None:
            return
        lines=self.proj_lines
        olines=self.overview_lines

        x_peak=self.ui.refXPos.value()
        x_width=self.ui.refXWidth.value()
        y_pos=self.ui.refYPos.value()
        y_width=self.ui.refYWidth.value()
        bg_pos=self.ui.bgCenter.value()
        bg_width=self.ui.bgWidth.value()

        lines[0].set_xdata([x_peak-x_width/2., x_peak-x_width/2.])
        lines[1].set_xdata([x_peak, x_peak])
        lines[2].set_xdata([x_peak+x_width/2., x_peak+x_width/2.])
        lines[3].set_xdata([bg_pos-bg_width/2., bg_pos-bg_width/2.])
        lines[4].set_xdata([bg_pos+bg_width/2., bg_pos+bg_width/2.])
        lines[5].set_xdata([y_pos-y_width/2., y_pos-y_width/2.])
        lines[6].set_xdata([y_pos+y_width/2., y_pos+y_width/2.])
        self.ui.x_project.draw()
        self.ui.y_project.draw()

        if len(olines)>4:
            olines[0].set_xdata([x_peak-x_width/2., x_peak-x_width/2.])
            olines[1].set_xdata([x_peak+x_width/2., x_peak+x_width/2.])
            olines[2].set_ydata([y_pos-y_width/2., y_pos-y_width/2.])
            olines[3].set_ydata([y_pos+y_width/2., y_pos+y_width/2.])
            self.ui.xy_overview.draw()
        olines[-4].set_ydata([x_peak-x_width/2., x_peak-x_width/2.])
        olines[-3].set_ydata([x_peak+x_width/2., x_peak+x_width/2.])
        olines[-2].set_ydata([bg_pos-bg_width/2., bg_pos-bg_width/2.])
        olines[-1].set_ydata([bg_pos+bg_width/2., bg_pos+bg_width/2.])

        self.ui.xtof_overview.draw()

        if self.ui.fanReflectivity.isChecked() and self.refl and not self.refl.options['extract_fan']:
            old_aca=self.auto_change_active
            self.auto_change_active=False
            self.ui.rangeStart.setValue(self.cut_areas['fan'][0])
            self.ui.rangeEnd.setValue(self.cut_areas['fan'][1])
            self.auto_change_active=old_aca
        elif not self.ui.fanReflectivity.isChecked() and self.refl and self.refl.options['extract_fan']:
            norm=self.getNorm()
            if norm in self.cut_areas:
                old_aca=self.auto_change_active
                self.auto_change_active=False
                self.ui.rangeStart.setValue(self.cut_areas[norm][0])
                self.ui.rangeEnd.setValue(self.cut_areas[norm][1])
                self.auto_change_active=old_aca
        self.trigger('initiateReflectivityPlot', False)

    @log_call
    def replotProjections(self):
        self.initiateProjectionPlot.emit(True)
        self.initiateReflectivityPlot.emit(True)

    @log_call
    def setNorm(self, do_plot=True, do_remove=True):
        '''
        Add dataset to the available normalizations or clear the normalization list.
        '''
        if self.refl is None:
            return
        if str(self.active_data.number) not in self.ref_norm:
            lamda=self.active_data.lambda_center
            if type(self.active_data.number) is list:
                number='['+",".join(map(str, self.active_data.number))+']'
            else:
                number=str(self.active_data.number)
            opts=self.refl.options
            self.ref_norm[number]=self.refl
            idx=sorted(self.ref_norm.keys()).index(number)
            self.ui.normalizeTable.insertRow(idx)
            item=QtGui.QTableWidgetItem(number)
            item.setTextColor(QtGui.QColor(100, 0, 0))
            item.setBackgroundColor(QtGui.QColor(200, 200, 200))
            self.ui.normalizeTable.setItem(idx, 0, QtGui.QTableWidgetItem(item))
            self.ui.normalizeTable.setItem(idx, 1, QtGui.QTableWidgetItem(str(lamda)))
            item=QtGui.QTableWidgetItem(str(opts['x_pos']))
            item.setBackgroundColor(QtGui.QColor(200, 200, 200))
            self.ui.normalizeTable.setItem(idx, 2, QtGui.QTableWidgetItem(item))
            self.ui.normalizeTable.setItem(idx, 3, QtGui.QTableWidgetItem(str(opts['x_width'])))
            item=QtGui.QTableWidgetItem(str(opts['y_pos']))
            item.setBackgroundColor(QtGui.QColor(200, 200, 200))
            self.ui.normalizeTable.setItem(idx, 4, QtGui.QTableWidgetItem(item))
            self.ui.normalizeTable.setItem(idx, 5, QtGui.QTableWidgetItem(str(opts['y_width'])))
            item=QtGui.QTableWidgetItem(str(opts['bg_pos']))
            item.setBackgroundColor(QtGui.QColor(200, 200, 200))
            self.ui.normalizeTable.setItem(idx, 6, QtGui.QTableWidgetItem(item))
            self.ui.normalizeTable.setItem(idx, 7, QtGui.QTableWidgetItem(str(opts['bg_width'])))
            self.ui.normalizationLabel.setText(u",".join(map(str, sorted(self.ref_norm.keys()))))
            self.ui.normalizeTable.resizeColumnsToContents()
        elif do_remove:
            if type(self.active_data.number) is list:
                number='['+",".join(map(str, self.active_data.number))+']'
            else:
                number=str(self.active_data.number)
            idx=sorted(self.ref_norm.keys()).index(number)
            del(self.ref_norm[number])
            self.ui.normalizeTable.removeRow(idx)
            self.ui.normalizationLabel.setText(u",".join(map(str, sorted(self.ref_norm.keys()))))
        if do_plot:
            self.initiateReflectivityPlot.emit(False)

    @log_both
    def getNorm(self, data=None):
        '''
        Return a fitting normalization (same ToF channels and wavelength) for 
        a dataset.
        '''
        if self.active_data is None:
            return None
        fittings=[]
        indices=[]
        if data is None:
            data=self.active_data[self.active_channel]
        for index, norm in sorted(self.ref_norm.items()):
            if len(norm.Rraw)==len(data.tof) and norm.lambda_center==data.lambda_center:
                fittings.append(norm)
                indices.append(str(index))
        if len(fittings)==0:
            return None
        elif len(fittings)==1:
            return fittings[0]
        elif str(self.active_data.number) in indices:
            return fittings[indices.index(str(self.active_data.number))]
        else:
            if self._norm_selected is None:
                result=QtGui.QInputDialog.getItem(self, 'Select Normalization',
                                                  'There are more than one normalizations\nfor this wavelength available,\nplease select one:',
                                                  indices, editable=False)
                if not result[1]:
                    return None
                else:
                    self._norm_selected=indices.index(result[0])
            return fittings[self._norm_selected]

    @log_call
    def clearNormList(self):
        '''
        Remove all items from the reduction list.
        '''
        self.ui.normalizeTable.setRowCount(0)
        self.ui.normalizationLabel.setText(u"Unset")
        self.ref_norm={}

    @log_call
    def normalizeTotalReflection(self):
        '''
        Extract the scaling factor from the reflectivity curve.
        '''
        if self.refl is None or not self.refl.options['normalization']:
            warning('Please select a dataset with total reflection plateau\nand normalization.',
                    extra={'title': 'Select other dataset'})
            return
        self.auto_change_active=True
        if len(self.reduction_list)>0:
            # try to match both datasets by fitting a polynomiral to the overlapping region
            rescale, xfit, yfit=get_scaling(self.refl, self.reduction_list[-1],
                                            self.ui.addStitchPoints.value(),
                                            polynom=self.ui.polynomOrder.value())
            self.ui.refScale.setValue(self.ui.refScale.value()+log10(rescale)) #change the scaling factor
            self.initiateReflectivityPlot.emit(False)
            self.ui.refl.plot(xfit, yfit, '-r', lw=2)
        else:
            # normalize total reflection plateau
            # Start from low Q and search for the critical edge
            wmean, npoints=get_total_reflection(self.refl, return_npoints=True)
            self.ui.refScale.setValue(self.ui.refScale.value()+log10(wmean)) #change the scaling factor
            self.initiateReflectivityPlot.emit(False)
            # show a line in the plot corresponding to the extraction region
            first=len(self.refl.R)-self.ui.rangeStart.value()
            Q=self.refl.Q[:first][self.refl.R[:first]>0]
            totref=Line2D([Q.min(), Q[npoints]], [1., 1.], color='red')
            self.ui.refl.canvas.ax.add_line(totref)
        self.auto_change_active=False
        self.ui.refl.draw()

    @log_call
    def addRefList(self, do_plot=True):
        '''
        Collect information about the current extraction settings and store them
        in the list of reduction items.
        '''
        if self.refl is None:
            return
        if self.refl.options['normalization'] is None:
            warning(u"You can only add reflectivities (λ normalized)!",
                    extra={'title': u'Data not normalized'})
            return
        # collect current settings
        channels=self.channels
        if self.reduction_list==[]:
            self.ref_list_channels=list(channels)
        elif self.ref_list_channels!=channels:
            warning(u'''The active dataset has not the same states as the ones already in the list:

%s  ≠  %s'''%(u" / ".join(channels), u' / '.join(self.ref_list_channels)),
              extra={'title': u'Wrong Channels'})
            return
        # options used for the extraction
        opts=self.refl.options

        Pstart=len(self.refl.R)-where(self.refl.R>0)[0][-1]-1
        Pend=where(self.refl.R>0)[0][0]
        opts['P0']=max(Pstart, opts['P0'])
        opts['PN']=max(Pend, opts['PN'])

        if len(self.reduction_list)==0:
            # use the same y region for all following datasets (can be changed by user if desired)
            self.ui.actionAutoYLimits.setChecked(False)
        self.reduction_list.append(self.refl)
        self.ui.reductionTable.setRowCount(len(self.reduction_list))
        idx=len(self.reduction_list)-1
        self.auto_change_active=True

        item=QtGui.QTableWidgetItem(opts['number'])
        item.setTextColor(QtGui.QColor(100, 0, 0))
        item.setBackgroundColor(QtGui.QColor(200, 200, 200))
        self.ui.reductionTable.setItem(idx, 0, item)
        self.ui.reductionTable.setItem(idx, 1,
                                       QtGui.QTableWidgetItem("%.4f"%(opts['scale'])))
        self.ui.reductionTable.setItem(idx, 2,
                                       QtGui.QTableWidgetItem(str(opts['P0'])))
        self.ui.reductionTable.setItem(idx, 3,
                                       QtGui.QTableWidgetItem(str(opts['PN'])))
        item=QtGui.QTableWidgetItem(str(opts['x_pos']))
        item.setBackgroundColor(QtGui.QColor(200, 200, 200))
        self.ui.reductionTable.setItem(idx, 4, item)
        self.ui.reductionTable.setItem(idx, 5,
                                       QtGui.QTableWidgetItem(str(opts['x_width'])))
        item=QtGui.QTableWidgetItem(str(opts['y_pos']))
        item.setBackgroundColor(QtGui.QColor(200, 200, 200))
        self.ui.reductionTable.setItem(idx, 6, item)
        self.ui.reductionTable.setItem(idx, 7,
                                       QtGui.QTableWidgetItem(str(opts['y_width'])))
        item=QtGui.QTableWidgetItem(str(opts['bg_pos']))
        item.setBackgroundColor(QtGui.QColor(200, 200, 200))
        self.ui.reductionTable.setItem(idx, 8, item)
        self.ui.reductionTable.setItem(idx, 9,
                                       QtGui.QTableWidgetItem(str(opts['bg_width'])))
        self.ui.reductionTable.setItem(idx, 10,
                                       QtGui.QTableWidgetItem(str(opts['dpix'])))
        self.ui.reductionTable.setItem(idx, 11,
                                       QtGui.QTableWidgetItem("%.4f"%opts['tth']))
        self.ui.reductionTable.setItem(idx, 12,
                                       QtGui.QTableWidgetItem(str(opts['normalization'].options['number'])))
        self.ui.reductionTable.resizeColumnsToContents()
        self.auto_change_active=False
        # emit signals
        self.reflectivityUpdated.emit(do_plot)
        if do_plot:
            self.initiateReflectivityPlot.emit(True)

    def same_cell_selected(self, current_row, current_column):
        if (self._prev_row_selected == current_row) and (self._prev_col_selected == current_column):
            return True
        if (self._prev_row_selected == current_row) and (self._prev_col_selected < 6) and (current_column < 6):
            return True
        return False

    @waiting_effects          
    def bigTable_selection_changed(self, row, column):    
        self.userClickedInTable = True
        self.editing_flag = True
        if self.same_cell_selected(row, column):
            return

        self._cur_column_selected = column
        self._cur_row_selected = row
        SelectionBigTableChanged(self)

    def data_norm_tab_changed(self, index):
        if self.userClickedInTable:
            self.userClickedInTable = False
            return

        [r,col] = self.getTrueCurrentRowColumnSelected()

        # no data loaded yet
        if r == -1:
            return

        tabIndex = self.ui.dataNormTabWidget.currentIndex()

        # data
        if tabIndex == 0:
            if col == 6:
                col = 0
        else:
            if col != 6:
                col = 6

        self.ui.reductionTable.setRangeSelected(QtGui.QTableWidgetSelectionRange(r,0,r,6),False)                                                                                   	    
        self.ui.reductionTable.setRangeSelected(QtGui.QTableWidgetSelectionRange(r,col,r,col),True)                                                                                   	

        self.bigTable_selection_changed(r, col)


    @log_input
    def reductionTableChanged(self, item):
        '''
        Perform action upon change in data reduction list.
        '''
        if self.auto_change_active:
            return
        entry=item.row()
        column=item.column()
        refl=self.reduction_list[entry]
        options=dict(refl.options)
        # reset options that can't be changed
        if column==0:
            item.setText(str(options['number']))
            return
        elif column==12:
            item.setText(str(options['normalization'].options['number']))
            return
        # update settings from selected option
        elif column in [1, 4, 5, 6, 7, 8, 9, 10]:
            key=[None, 'scale', None, None,
                 'x_pos', 'x_width',
                 'y_pos', 'y_width',
                 'bg_pos', 'bg_width',
                 'dpix'][column]
            try:
                options[key]=float(item.text())
            except ValueError:
                item.setText(str(options[key]))
            else:
                refl_new=self.recalculateReflectivity(refl, options)
                self.reduction_list[entry]=refl_new
        elif column==2:
            try:
                refl.options['P0']=int(item.text())
            except ValueError:
                item.setText(str(options['P0']))
        elif column==3:
            try:
                refl.options['PN']=int(item.text())
            except ValueError:
                item.setText(str(options['PN']))
        elif column==11:
            try:
                options['tth']=float(item.text())
            except ValueError:
                item.setText(str(options['tth']))
            else:
                refl_new=self.recalculateReflectivity(refl, options)
                self.reduction_list[entry]=refl_new
        self.ui.reductionTable.resizeColumnsToContents()
        self.reflectivityUpdated.emit(True)
        self.initiateReflectivityPlot.emit(True)

    @log_call
    def changeActiveChannel(self):
        '''
        The overview and reflectivity channel was changed. This
        recalculates already extracted reflectivities.
        '''
        selection=0
        for i in range(12):
            if getattr(self.ui, 'selectedChannel%i'%i).isChecked():
                selection=i
        if selection>=len(self.channels):
            return
        self.active_channel=self.channels[selection]
        if self.active_channel in self.ref_list_channels:
            for i, refli in enumerate(self.reduction_list):
                refli=self.recalculateReflectivity(refli)
                self.reduction_list[i]=refli
        self.updateLabels()
        self.plotActiveTab()
        self.initiateProjectionPlot.emit(False)
        self.initiateReflectivityPlot.emit(False)

    @log_call
    def clearRefList(self, do_plot=True):
        '''
        Remove all items from the reduction list.
        '''
        self.reduction_list=[]
        self.ui.reductionTable.setRowCount(0)
        self.ui.actionAutoYLimits.setChecked(True)
        self.reflectivityUpdated.emit(do_plot)
        if do_plot:
            self.initiateReflectivityPlot.emit(False)

    @log_call
    def removeRefList(self):
        '''
        Remove one item from the reduction list.
        '''
        index=self.ui.reductionTable.currentRow()
        if index<0:
            return
        self.reduction_list.pop(index)
        self.ui.reductionTable.removeRow(index)
        #self.ui.reductionTable.setRowCount(0)
        self.reflectivityUpdated.emit(True)
        self.initiateReflectivityPlot.emit(False)

    @log_call
    def overwriteDirectBeam(self):
        '''
        Take the active x0 and Dangle values as overwrite parameters
        to be used with other datasets as well.
        '''
        self.auto_change_active=True
        self.ui.directPixelOverwrite.setValue(self.ui.refXPos.value())
        self.ui.dangle0Overwrite.setText(str(self.active_data[self.active_channel].dangle))
        self.auto_change_active=False
        self.overwriteChanged()

    @log_call
    def clearOverwrite(self):
        '''
        Reset overwrite to use values from the .nxs files.
        '''
        self.auto_change_active=True
        self.ui.directPixelOverwrite.setValue(-1)
        self.ui.dangle0Overwrite.setText("None")
        self.auto_change_active=False
        self.overwriteChanged()

    @log_call
    def overwriteChanged(self):
        '''
        Recalculate reflectivity based on changed overwrite parameters.
        '''
        if not self.auto_change_active and self.active_data is not None:
            self.updateLabels()
            self.calcReflParams()
            self.initiateProjectionPlot.emit(True)
            self.initiateReflectivityPlot.emit(True)

    @log_call
    def reduceDatasets(self):
        '''
        Open a dialog to select reduction options for the current list of
        reduction items.
        '''
        if len(self.reduction_list)==0:
            warning(u'Please select at least\none dataset to reduce.',
                    extra={'title': u'Select a dataset'})
            return
        dialog=ReduceDialog(self, self.ref_list_channels, self.reduction_list)
        dialog.exec_()
        dialog.destroy()

    @log_call
    def quickReduce(self):
        '''
        Reduce the current list of reduction items using the last options.
        '''
        if len(self.reduction_list)==0:
            warning(u'Please select at least\none dataset to reduce.',
                    extra={'title': u'Select a dataset'})
            return
        reducer=Reducer(self, self.ref_list_channels, self.reduction_list)
        reducer.execute()

    def plotMouseEvent(self, event):
        '''
        Show the mouse position of any plot in the main window
        status bar, as the single plot status indicator is only
        visible for larger plot toolbars.
        '''
        if event.inaxes is None:
            return
        self.ui.statusbar.showMessage(u"x=%15g    y=%15g"%(event.xdata, event.ydata))

    def plotRelese(self, event):
        self._picked_line=None

    def mouseNormPlotyt(self, event):
        '''
        user is moving the mouse in the plot_yt canvas
        '''
        # event.button == 1 -> mouse is moving with left button pressed
        # event.button == 3 -> mouse is moving with right button pressed

        return

        # clicked outside region, nothing should be done
        if event.button is not None and \
           (event.xdata is None or event.ydata is None):
            return

        offset = 4    # click within 2 pixels of current selection will move this selection

        _live_y = event.ydata
        _live_x = event.xdata

        if event.button == 1 and self._live_selection is None:

            peak_min = self.ui.normPeakFromValue.value()
            if abs(peak_min - _live_y) <= offset:
                self._live_selection = 'peak_min'

            peak_max = self.ui.normPeakToValue.value()
            if abs(peak_max - _live_y) <= offset:
                self._live_selection = 'peak_max'

            back_min = self.ui.normBackFromValue.value()
            if abs(back_min - _live_y) <= offset:
                self._live_selection = 'back_min'

            back_max = self.ui.normBackToValue.value()
            if abs(back_max - _live_y) <= offset:
                self._live_selection = 'back_max'

            #lowres_min = self.ui.normLowResFromValue.value()
            #if abs(lowres_min - _live_x) <= offset:
                #self._live_selection = 'lowres_min'

            #lowres_max = self.ui.normLowResToValue.value()
            #if abs(lowres_max - _live_x) <= offset:
                #self._live_selection = 'lowres_max'

            if self._live_selection == 'peak_min':
                self.ui.normPeakFromValue.setValue(_live_y)
            if self._live_selection == 'peak_max':
                self.ui.normPeakToValue.setValue(_live_y)
            if self._live_selection == 'back_min':
                self.ui.normBackFromValue.setValue(_live_y)
            if self._live_selection == 'back_max':
                self.ui.normBackToValue.setValue(_live_y)
            #if self._live_selection == 'lowres_min':
                #self.ui.normLowResFromValue.setValue(_live_y)
            #if self._live_selection == 'lowres_max':
                #self.ui.normLowResToValue.setValue(_live_y)

        else:

            self._live_selection = None  


        if event.button is not None:
            self.plot_overview_REFL(plot_yt=True, plot_yi=True, plot_it=False, plot_ix=False)


        #if event.button==1 and self.ui.xy_overview.toolbar._active is None and \
                #event.xdata is not None:
            #self.ui.refXPos.setValue(event.xdata)
        #elif event.button==3 and self.ui.xy_overview.toolbar._active is None and \
                #event.ydata is not None:
            #ypos=self.ui.refYPos.value()
            #yw=self.ui.refYWidth.value()
            #yl=ypos-yw/2.
            #yr=ypos+yw/2.
            #pl=self._picked_line
            #if pl=='yl' or (pl is None and abs(event.ydata-yl)<abs(event.ydata-yr)):
                #yl=event.ydata
                #self._picked_line='yl'
            #else:
                #yr=event.ydata
                #self._picked_line='yr'
            #ypos=(yr+yl)/2.
            #yw=(yr-yl)
            #self.auto_change_active=True
            #self.ui.refYPos.setValue(ypos)
            #self.auto_change_active=False
            #self.ui.refYWidth.setValue(yw)


    def plotPickX(self, event):
        '''
        Plot for x-projection has been clicked.
        '''
        if event.button is not None and self.ui.x_project.toolbar._active is None and \
           event.xdata is not None:
            if event.button==1:
                xcen=self.ui.refXPos.value()
                bgc=self.ui.bgCenter.value()
                bgw=self.ui.bgWidth.value()
                bgl=bgc-bgw/2.
                bgr=bgc+bgw/2.
                dists=[abs(event.xdata-item) for item in [xcen, bgl, bgr]]
                min_dist=dists.index(min(dists))
                pl=self._picked_line
                if pl=='bgl' or (pl is None and min_dist==1):
                    # left of right background bar and closer to left one
                    bgl=event.xdata
                    bgc=(bgr+bgl)/2.
                    bgw=(bgr-bgl)
                    self.auto_change_active=True
                    self.ui.bgCenter.setValue(bgc)
                    self.auto_change_active=False
                    self.ui.bgWidth.setValue(bgw)
                    self._picked_line='bgl'
                elif pl=='bgr' or (pl is None and min_dist==2):
                    # left of right background bar or closer to right background than peak
                    bgr=event.xdata
                    bgc=(bgr+bgl)/2.
                    bgw=(bgr-bgl)
                    self.auto_change_active=True
                    self.ui.bgCenter.setValue(bgc)
                    self.auto_change_active=False
                    self.ui.bgWidth.setValue(bgw)
                    self._picked_line='bgr'
                else:
                    self.ui.refXPos.setValue(event.xdata)
                    self._picked_line='xpos'
            elif event.button==3:
                self.ui.refXWidth.setValue(abs(self.ui.refXPos.value()-event.xdata)*2.)

    def plotPickY(self, event):
        '''
        Plot for y-projection has been clicked.
        '''
        if event.button==1 and self.ui.y_project.toolbar._active is None and \
           event.xdata is not None:
            ypos=self.ui.refYPos.value()
            yw=self.ui.refYWidth.value()
            yl=ypos-yw/2.
            yr=ypos+yw/2.
            pl=self._picked_line
            if pl=='yl' or (pl is None and abs(event.xdata-yl)<abs(event.xdata-yr)):
                yl=event.xdata
                self._picked_line='yl'
            else:
                yr=event.xdata
                self._picked_line='yr'
            ypos=(yr+yl)/2.
            yw=(yr-yl)
            self.auto_change_active=True
            self.ui.refYPos.setValue(ypos)
            self.auto_change_active=False
            self.ui.refYWidth.setValue(yw)

    def plotPickXY(self, event):
        '''
        Plot for xy-map has been clicked or mouse moved
        '''
        # event.button == 1 -> mouse is moving with left button pressed
        # event.button == 3 -> mouse is moving with right button pressed

        # clicked outside region, nothing should be done
        if event.xdata is None or event.ydata is None:
            return

        offset = 4    # click within 2 pixels of current selection will move this selection

        _live_y = event.ydata
        _live_x = event.xdata

        if event.button == 1 and self._live_selection is None:

            peak_min = self.ui.dataPeakFromValue.value()
            if abs(peak_min - _live_y) <= offset:
                self._live_selection = 'peak_min'

            peak_max = self.ui.dataPeakToValue.value()
            if abs(peak_max - _live_y) <= offset:
                self._live_selection = 'peak_max'

            back_min = self.ui.dataBackFromValue.value()
            if abs(back_min - _live_y) <= offset:
                self._live_selection = 'back_min'

            back_max = self.ui.dataBackToValue.value()
            if abs(back_max - _live_y) <= offset:
                self._live_selection = 'back_max'

            lowres_min = self.ui.dataLowResFromValue.value()
            if abs(lowres_min - _live_x) <= offset:
                self._live_selection = 'lowres_min'

            lowres_max = self.ui.dataLowResToValue.value()
            if abs(lowres_max - _live_x) <= offset:
                self._live_selection = 'lowres_max'

        if self._live_selection == 'peak_min':
            self.ui.dataPeakFromValue.setValue(_live_y)
        if self._live_selection == 'peak_max':
            self.ui.dataPeakToValue.setValue(_live_y)
        if self._live_selection == 'back_min':
            self.ui.dataBackFromValue.setValue(_live_y)
        if self._live_selection == 'back_max':
            self.ui.dataBackToValue.setValue(_live_y)
        if self._live_selection == 'lowres_min':
            self.ui.dataLowResFromValue.setValue(_live_y)
        if self._live_selection == 'lowres_max':
            self.ui.dataLowResToValue.setValue(_live_y)

        else:

            self._live_selection = None  

        return

        if event.button==1 and self.ui.xy_overview.toolbar._active is None and \
           event.xdata is not None:
            self.ui.refXPos.setValue(event.xdata)
        elif event.button==3 and self.ui.xy_overview.toolbar._active is None and \
             event.ydata is not None:
            ypos=self.ui.refYPos.value()
            yw=self.ui.refYWidth.value()
            yl=ypos-yw/2.
            yr=ypos+yw/2.
            pl=self._picked_line
            if pl=='yl' or (pl is None and abs(event.ydata-yl)<abs(event.ydata-yr)):
                yl=event.ydata
                self._picked_line='yl'
            else:
                yr=event.ydata
                self._picked_line='yr'
            ypos=(yr+yl)/2.
            yw=(yr-yl)
            self.auto_change_active=True
            self.ui.refYPos.setValue(ypos)
            self.auto_change_active=False
            self.ui.refYWidth.setValue(yw)

    #def lin_log_toggle(self):
        #print 'lin_log_toggle'


    def plotPickXToF(self, event):
        if event.button==1 and self.ui.xtof_overview.toolbar._active is None and \
           event.ydata is not None:
            xcen=self.ui.refXPos.value()
            bgc=self.ui.bgCenter.value()
            bgw=self.ui.bgWidth.value()
            bgl=bgc-bgw/2.
            bgr=bgc+bgw/2.
            dists=[abs(event.ydata-item) for item in [xcen, bgl, bgr]]
            min_dist=dists.index(min(dists))
            pl=self._picked_line
            if pl=='bgl' or (pl is None and min_dist==1):
                # left of right background bar and closer to left one
                bgl=event.ydata
                bgc=(bgr+bgl)/2.
                bgw=(bgr-bgl)
                self.auto_change_active=True
                self.ui.bgCenter.setValue(bgc)
                self.auto_change_active=False
                self.ui.bgWidth.setValue(bgw)
                self._picked_line='bgl'
            elif pl=='bgr' or (pl is None and min_dist==2):
                # left of right background bar or closer to right background than peak
                bgr=event.ydata
                bgc=(bgr+bgl)/2.
                bgw=(bgr-bgl)
                self.auto_change_active=True
                self.ui.bgCenter.setValue(bgc)
                self.auto_change_active=False
                self.ui.bgWidth.setValue(bgw)
                self._picked_line='bgr'
            else:
                self.ui.refXPos.setValue(event.ydata)
                self._picked_line='xpos'
        elif event.button==3 and self.ui.xtof_overview.toolbar._active is None and \
             event.ydata is not None:
            xpos=self.ui.refXPos.value()
            self.ui.refXWidth.setValue(abs(xpos-event.ydata)*2.)

    def scaleOnPlot(self, event):
        steps=event.step
        xpos=event.xdata
        if xpos is None:
            return
        for i, refl in enumerate(self.reduction_list):
            if (refl.Q[refl.options['PN']]>xpos):
                Ival=refl.options['scale']
                if self._control_down:
                    Inew=Ival*10**(0.05*steps)
                else:
                    Inew=Ival*10**(0.01*steps)
                self.ui.reductionTable.setItem(i, 1,
                                               QtGui.QTableWidgetItem("%.4f"%(Inew)))

    def isDataTabSelected(self):
        if self.ui.dataNormTabWidget.currentIndex() == 0:
            return True
        else:
            return False


    def changeColorScale(self, event):
        '''
          Change the intensity limits of a map plot with the mouse wheel.
        '''
        return #FIXME
        canvas=None
        for plot in [self.ui.xy_overview, self.ui.xtof_overview]:
            if plot.canvas is event.canvas:
                canvas=[plot]
        if event.canvas in [self.ui.xy_pp.canvas, self.ui.xy_mp.canvas,
                            self.ui.xy_pm.canvas, self.ui.xy_mm.canvas]:
            canvas=[self.ui.xy_pp, self.ui.xy_mp, self.ui.xy_pm, self.ui.xy_mm]
        if event.canvas in [self.ui.xtof_pp.canvas, self.ui.xtof_mp.canvas,
                            self.ui.xtof_pm.canvas, self.ui.xtof_mm.canvas]:
            canvas=[self.ui.xtof_pp, self.ui.xtof_mp, self.ui.xtof_pm, self.ui.xtof_mm]
        if not (canvas and canvas[0].cplot):
            return
        clim=canvas[0].cplot.get_clim()
        for canv in canvas:
            if canv.cplot is None:
                continue
            if self._control_down:
                canv.cplot.set_clim(min(clim[1]*0.9, clim[0]*10**(0.05*event.step)), clim[1])
            else:
                canv.cplot.set_clim(clim[0], max(clim[0]*1.1, clim[1]*10**(0.05*event.step)))
            canv.draw()

    def keyPressEvent(self, event):
        if event.modifiers()==QtCore.Qt.ControlModifier:
            self._control_down=True
        else:
            self._control_down=False

    def keyReleaseEvent(self, event):
        self._control_down=False

    def updateEventReadout(self, progress):
        '''
        When reading event mode data this is the callback
        used after each finished channel to indicate the progress.
        '''
        self.eventProgress.setValue(progress*100)
        # make sure the update is shown in the interface
        self.eventProgress.update()

    def updateProgressBar(self, progress):
        self.eventProgress.setVisible(True)
        self.eventProgress.setValue(progress*100)
        self.eventProgress.update()
        if progress == 1:
            time.sleep(2)
            self.eventProgress.setVisible(False)
            self.eventProgress.setValue(0)
            self.eventProgress.update()

####### Calculations and data treatment

    def updateStateFile(self, ignore):
        sfile=open(paths.STATE_FILE, 'wb')
        sfile.write((u'Running PID %i\n'%os.getpid()).encode('utf8'))
        if len(self.reduction_list)>0:
            sfile.write(unicode(HeaderCreator(self.reduction_list)).encode('utf8'))
        sfile.close()

    @log_call
    def calcReflParams(self):
        '''
        Calculate x and y regions for reflectivity extraction and put them in the
        entry fields.
        '''
        if instrument.NAME == "REF_M": #TODO HARDCODED INSTRUMENT
            data=self.active_data[self.active_channel]
        else:
            data=self.active_data

        self.auto_change_active=True
        if self.ui.actionAutomaticXPeak.isChecked():
            # locate peaks using CWT peak finder algorithm
            try:
                dangle0_overwrite=float(self.ui.dangle0Overwrite.text())
            except ValueError:
                dangle0_overwrite=None
            x_peak, self.pf=get_xpos(data, dangle0_overwrite,
                                     self.ui.directPixelOverwrite.value(),
                                     snr=self.ui.pfSNR.value(),
                                     min_width=self.ui.pfMinWidth.value(),
                                     max_width=self.ui.pfMaxWidth.value(),
                                     ridge_length=self.ui.pfRidgeLength.value(),
                                     return_pf=True)
            self.ui.refXPos.setValue(x_peak)

        if self.ui.actionAutoYLimits.isChecked():
            # find the central peak reagion with intensities larger than 10% of maximum
            y_center, y_width, self.y_bg=get_yregion(data)
            self.ui.refYPos.setValue(y_center)
            self.ui.refYWidth.setValue(y_width)
        else:
            self.y_bg=0.
        self.auto_change_active=False

    def visualizePeakfinding(self):
        '''
        Show a graphical representation of the peakfinder process.
        '''
        self.pf.visualize(snr=self.ui.pfSNR.value(),
                          min_width=self.ui.pfMinWidth.value(),
                          max_width=self.ui.pfMaxWidth.value(),
                          ridge_length=self.ui.pfRidgeLength.value())


    def recalculateReflectivity(self, old_object, overwrite_options=None):
        '''
        Use parameters to calculate and return the reflectivity
        of one file.
        '''
        if type(old_object.origin) is list:
            filenames=[origin[0] for origin in old_object.origin]
            data=NXSMultiData(filenames, **old_object.read_options)[self.active_channel]
        else:
            filename, _channel=old_object.origin
            data=NXSData(filename, **old_object.read_options)[self.active_channel]
        if overwrite_options:
            refl=Reflectivity(data, **overwrite_options)
        else:
            refl=Reflectivity(data, **old_object.options)
        return refl

###### Window initialization and exit

    def readSettings(self):
        '''
        Restore window and dock geometry.
        '''
        # setup a file in the users directroy making sure the application is not run twice
        # the file also stores the current working state for reload after a crash (reduced data)
        if os.path.exists(paths.STATE_FILE):
            _result=QtGui.QMessageBox.warning(self, "Previous Crash",
"""There is a state file but no running process for it, 
this could indicate a previous crash.

Do you want to try to restore the working reduction list?""",
                                                            buttons=QtGui.QMessageBox.Yes|QtGui.QMessageBox.No)
            if _result==QtGui.QMessageBox.Yes:
                self._pending_header=open(paths.STATE_FILE, 'r').read()
                QtCore.QTimer.singleShot(1500, self.loadExtraction)
        open(paths.STATE_FILE, 'w').write('Running PID %i\n'%os.getpid())
        # read window settings
        debug('Applying GUI configuration')
        if gui.geometry is not None: self.restoreGeometry(QtCore.QByteArray(gui.geometry))
        if gui.state is not None: self.restoreState(QtCore.QByteArray(gui.state))
        if hasattr(self.ui, 'mainSplitter'):
            self.ui.mainSplitter.setSizes(gui.splitters[0])
#      self.ui.plotSplitter.setSizes(gui.splitters[2])
#    self.ui.overviewSplitter.setSizes(gui.splitters[1])
        self.ui.color_selector.setCurrentIndex(gui.color_selection)
        self.ui.show_colorbars.setChecked(gui.show_colorbars)
        if instrument.NAME is "REF_M": #TODO HARDCODED INSTRUMENT
            self.ui.normalizeXTof.setChecked(gui.normalizeXTof)
        #for i, fig in enumerate([
                                                        #self.ui.xy_overview,
                                                        #self.ui.xtof_overview,
                                                        #self.ui.refl,
                                                        #self.ui.x_project,
                                                        #self.ui.y_project,
                                                        #]):
            #fig.set_config(gui.figure_params[i])

    def closeEvent(self, event=None):
        '''
        Save window and dock geometry.
        '''

        if instrument.NAME == 'REF_M': #TODO HARDCODED INSTRUMENT

            # join delay thread
            debug('Shutting down delay trigger')
            self.trigger.stay_alive=False
            self.trigger.wait()
            del(self.trigger)
            debug('Gathering figure and window layout')
            # store geometry and setting parameters
            figure_params=[]
            for fig in [
                self.ui.xy_overview,
                self.ui.xtof_overview,
                self.ui.refl,
                self.ui.x_project,
                self.ui.y_project,
                ]:
                figure_params.append(fig.get_config())

            debug('Storing GUI configuration')
            gui.geometry=self.saveGeometry().data()
            gui.state=self.saveState().data()
            if hasattr(self.ui, 'mainSplitter'):
                gui.splitters=(self.ui.mainSplitter.sizes(), self.ui.overviewSplitter.sizes(), self.ui.plotSplitter.sizes())
            else:
                gui.splitters=(gui.splitters[0], self.ui.overviewSplitter.sizes(), gui.splitters[2])
            gui.color_selection=self.ui.color_selector.currentIndex()
            gui.show_colorbars=self.ui.show_colorbars.isChecked()
            gui.normalizeXTof=self.ui.normalizeXTof.isChecked()
            gui.figure_params=figure_params

            # remove the state file on normal exit
            debug('Removing status file')
            os.remove(paths.STATE_FILE)
            # detach the gui logging handler before closing the window
            debug('Detaching GUI handler')
            from logging import getLogger
            logger=getLogger()
            for handler in logger.handlers:
                if handler.__class__.__name__=='QtHandler':
                    logger.removeHandler(handler)
            debug('GUI handler removed, closing window')
            # actually close the window
            QtGui.QMainWindow.closeEvent(self, event)

        else: #REF_L

            # save config files
            self.save_config_files()
            # remove the state file on normal exit
#      debug('Removing status file')
    #    os.remove(paths.STATE_FILE)
            # detach the gui logging handler before closing the window
            debug('Detaching GUI handler')
            from logging import getLogger
            logger=getLogger()
            for handler in logger.handlers:
                if handler.__class__.__name__=='QtHandler':
                    logger.removeHandler(handler)
            debug('GUI handler removed, closing window')
            # actually close the window
            QtGui.QMainWindow.closeEvent(self, event)

    def save_config_files(self):
        self.reducedFilesLoadedObject.save()
        self.gui_config()

    def gui_config(self):
        from quicknxs.config import refllastloadedfiles
        refllastloadedfiles.switch_config('config_files')
        refllastloadedfiles.config_files_path = self.path_config
        refllastloadedfiles.switch_config('default')

    @log_call
    def open_advanced_background(self):
        '''
        Show a dialog to enter additional options for the background calculation.
        '''
        if self.background_dialog:
            self.background_dialog.show()
        else:
            self.background_dialog=BackgroundDialog(self)
            self.background_dialog.show()
            self.background_dialog.resize(self.background_dialog.width(), self.height())
            self.background_dialog.move(self.background_dialog.pos().x()+self.width(),
                                        self.pos().y())
            if self.refl:
                self.background_dialog.drawXTof()
                self.background_dialog.drawBG()

    @log_call
    def open_compare_window(self):
        dia=CompareDialog(size=QtCore.QSize(800, 800))
        dia.show()
        self.open_plots.append(dia)

    def tofValidation( self, tof_auto_switch_status, tof1, tof2):
        self.ui.dataTOFautoMode.setChecked(tof_auto_switch_status)
        self.ui.dataTOFmanualMode.setChecked(not tof_auto_switch_status)
        bigTableData = self.bigTableData
        row = self._cur_row_selected
        col = self._cur_column_selected
        if col != 0:
            col = 1
        data = bigTableData[row, col]
        _active_data =  data.active_data
        tof1 = str(float(tof1)*1000)
        tof2 = str(float(tof2)*1000)
        if tof_auto_switch_status:
            _active_data.tof_range_auto = [tof1, tof2]
        else:
            _active_data.tof_range = [tof1, tof2]
        data.active_data = _active_data
        bigTableData[row, col] = data
        self.bigTableData = bigTableData
        self.auto_tof_switch(tof_auto_switch_status)
	self.fileHasBeenModified()

    def data_background_switch(self):
        '''
        With or without data background
        '''
        bigTableData = self.bigTableData
        #[row,col] = self.getCurrentRowColumnSelected()
        row = self._cur_row_selected
        col = self._cur_column_selected
        if col != 0:
            col = 1
        data = bigTableData[row,col]
        data = data.active_data

        flag = self.ui.dataBackgroundFlag.isChecked()

        data.back_flag = flag
        self.active_data = data

        self.ui.dataBackFromLabel.setEnabled(flag)
        self.ui.dataBackFromValue.setEnabled(flag)
        self.ui.dataBackToLabel.setEnabled(flag)
        self.ui.dataBackToValue.setEnabled(flag)

        # save new settings
        self.save_new_settings()

        # refresh plot
        self.plot_overview_REFL(plot_yi=True, plot_yt=True)

        CheckErrorWidgets(self)
	self.fileHasBeenModified()


    def data_low_res_switch(self):
        '''
        With or without data low resolution range
        '''
        bigTableData = self.bigTableData
        #[row,col] = self.getCurrentRowColumnSelected()
        row = self._cur_row_selected
        col = self._cur_column_selected
        if col != 0:
            col = 1
        data = bigTableData[row,col]
        data = data.active_data

        flag = self.ui.dataLowResFlag.isChecked()

        data.low_res_flag = flag
        self.active_data = data

        self.ui.dataLowResFromLabel.setEnabled(flag)
        self.ui.dataLowResFromValue.setEnabled(flag)
        self.ui.dataLowResToLabel.setEnabled(flag)
        self.ui.dataLowResToValue.setEnabled(flag)

        # save new settings
        self.save_new_settings()

        # refresh plot
        self.plot_overview_REFL(plot_ix=True, plot_yt=True, plot_yi=True)
	self.fileHasBeenModified()

    def normalization_switch(self, flag):
        '''
        With or without normalization
        '''

        if flag:
            # need to check status of over flags here
            flagLowRes = self.ui.normLowResFlag.isChecked()
            flagBack = self.ui.normBackgroundFlag.isChecked()
        else:
            flagLowRes = False
            flagBack = False

            bigTableData = self.bigTableData
#      [row,col] = self.getCurrentRowColumnSelected()
            row = self._cur_row_selected
            col = self._cur_column_selected
            if col != 0:
                col = 1
            data = bigTableData[row,col]
            data = data.active_data

        data.use_it_flag = flag
        self.active_data = data

        self.ui.norm_yt_plot.setEnabled(flag)
        self.ui.norm_yi_plot.setEnabled(flag)
        self.ui.norm_it_plot.setEnabled(flag)
        self.ui.norm_ix_plot.setEnabled(flag)

        self.ui.normPeakFromLabel.setEnabled(flag)
        self.ui.normPeakFromValue.setEnabled(flag)
        self.ui.normPeakToLabel.setEnabled(flag)
        self.ui.normPeakToValue.setEnabled(flag)
        self.ui.normBackgroundFlag.setEnabled(flag)
        self.ui.normBackFromLabel.setEnabled(flagBack)
        self.ui.normBackFromValue.setEnabled(flagBack)
        self.ui.normBackToLabel.setEnabled(flagBack)
        self.ui.normBackToValue.setEnabled(flagBack)
        self.ui.normLowResFlag.setEnabled(flag)
        self.ui.normLowResFromLabel.setEnabled(flagLowRes)
        self.ui.normLowResFromValue.setEnabled(flagLowRes)
        self.ui.normLowResToLabel.setEnabled(flagLowRes)
        self.ui.normLowResToValue.setEnabled(flagLowRes)

        # save new settings
        self.save_new_settings()
	self.fileHasBeenModified()

    def normalization_background_switch(self):
        '''
        With or without normalization background
        '''
        bigTableData = self.bigTableData
        #[row,col] = self.getCurrentRowColumnSelected()
        row = self._cur_row_selected
        col = self._cur_column_selected
        if col != 0:
            col = 1
        data = bigTableData[row,col]
        data = data.active_data

        flag = self.ui.normBackgroundFlag.isChecked()

        self.ui.normBackFromLabel.setEnabled(flag)
        self.ui.normBackFromValue.setEnabled(flag)
        self.ui.normBackToLabel.setEnabled(flag)
        self.ui.normBackToValue.setEnabled(flag)

        # save new settings
        self.save_new_settings()

        self.plot_overview_REFL(plot_yi=True, plot_yt=True)    
        CheckErrorWidgets(self)
	self.fileHasBeenModified()

    def normalization_low_res_switch(self):
        '''
        With or without normalization low resolution range
        '''

        bigTableData = self.bigTableData
        #[row,col] = self.getCurrentRowColumnSelected()
        row = self._cur_row_selected
        col = self._cur_column_selected
        if col != 0:
            col = 1
        data = bigTableData[row,col]
        data = data.active_data

        flag = self.ui.normLowResFlag.isChecked()

        data.low_res_flag = flag
        self.active_data = data

        self.ui.normLowResFromLabel.setEnabled(flag)
        self.ui.normLowResFromValue.setEnabled(flag)
        self.ui.normLowResToLabel.setEnabled(flag)
        self.ui.normLowResToValue.setEnabled(flag)

        # save new settings
        self.save_new_settings()

        # refresh plots
        self.plot_overview_REFL(plot_ix=True, plot_yt=True, plot_yi=True)
	self.fileHasBeenModified()

    def data_peak_and_back_validation(self, withPlotUpdate=True):
        self.data_peak_spinbox_validation(withPlotUpdate=withPlotUpdate)
        self.data_back_spinbox_validation(withPlotUpdate=withPlotUpdate)
        CheckErrorWidgets(self)
	self.fileHasBeenModified()

    # data peak spinboxes
    def data_peak_spinbox_validation(self, withPlotUpdate=True):
        '''
        This function, reached when the user is done editing the
        spinboxes (ENTER, leaving the spinbox) 
        will make sure the min value is < max value    
        '''

        bigTableData = self.bigTableData
        #[row,col] = self.getCurrentRowColumnSelected()
        row = self._cur_row_selected
        col = self._cur_column_selected
        if col != 0:
            col = 1
        data = bigTableData[row,col]
        data = data.active_data

        peak1 = self.ui.dataPeakFromValue.value()
        peak2 = self.ui.dataPeakToValue.value()

        if (peak1 > peak2):
            peak_min = peak2
            peak_max = peak1
        else:
            peak_min = peak1
            peak_max = peak2

        data.peak = [str(peak_min),str(peak_max)]
        self.active_data = data

        self.ui.dataPeakFromValue.setValue(peak_min)
        self.ui.dataPeakToValue.setValue(peak_max)

        # refresh plots
        if withPlotUpdate:
            self.plot_overview_REFL(plot_ix=True, plot_yt=True, plot_yi=True)

        # save new settings
        self.save_new_settings()

        CheckErrorWidgets(self)
	self.fileHasBeenModified()

    # data back spinboxes
    def data_back_spinbox_validation(self, withPlotUpdate=True):
        r = self._cur_row_selected
        c = self._cur_column_selected
        if c != 0:
            c = 1
        _data = self.bigTableData[r,c]
	if _data is None:
	    return
        data = _data.active_data

        back1 = self.ui.dataBackFromValue.value()
        back2 = self.ui.dataBackToValue.value()

        if (back1 > back2):
            back_min = back2
            back_max = back1
        else:
            back_min = back1
            back_max = back2

        data.back = [str(back_min),str(back_max)]

        _data.active_data = data
        self.bigTableData[r,c] = _data

        self.ui.dataBackFromValue.setValue(back_min)
        self.ui.dataBackToValue.setValue(back_max)

        # save new settings
        self.save_new_settings()

        # refresh plots
        self.plot_overview_REFL(plot_ix=True, plot_yt=True, plot_yi=True)

        CheckErrorWidgets(self)
	self.fileHasBeenModified()

    # data low resolution spinboxes
    def data_lowres_spinbox_validation(self):
        '''
        This function, reached when the user is done editing the
        spinboxes (ENTER, leaving the spinbox) 
        will make sure the min value is < max value  
        '''
        bigTableData = self.bigTableData
        #[row,col] = self.getCurrentRowColumnSelected()
        row = self._cur_row_selected
        col = self._cur_column_selected
        if col != 0:
            col = 1
        data = bigTableData[row,col]
        if data is None:
            return
        data = data.active_data

        lowres1 = self.ui.dataLowResFromValue.value()
        lowres2 = self.ui.dataLowResToValue.value()

        if (lowres1 > lowres2):
            lowres_min = lowres2
            lowres_max = lowres1
        else:
            lowres_min = lowres1
            lowres_max = lowres2

        data.low_res = [str(lowres_min),str(lowres_max)]
        self.active_data = data

        self.ui.dataLowResFromValue.setValue(lowres_min)
        self.ui.dataLowResToValue.setValue(lowres_max)

        # save new settings
        self.save_new_settings()

        # refresh plots
        self.plot_overview_REFL(plot_ix=True, plot_yt=True, plot_yi=True)

        CheckErrorWidgets(self)
	self.fileHasBeenModified()

    def norm_peak_and_back_validation(self, withPlotUpdate=False):
        self.norm_peak_spinbox_validation(withPlotUpdate)
        self.norm_back_spinbox_validation(withPlotUpdate)
	self.fileHasBeenModified()

    # norm peak spinboxes
    def norm_peak_spinbox_validation(self, withPlotUpdate=True):
        '''
        This function, reached when the user is done editing the
        spinboxes (ENTER, leaving the spinbox) 
        will make sure the min value is < max value    
        '''

        bigTableData = self.bigTableData
        #[row,col] = self.getCurrentRowColumnSelected()
        row = self._cur_row_selected
        col = self._cur_column_selected
        if col != 0:
            col = 1
        data = bigTableData[row,col]
        data = data.active_data

        peak1 = self.ui.normPeakFromValue.value()
        peak2 = self.ui.normPeakToValue.value()

        if (peak1 > peak2):
            peak_min = peak2
            peak_max = peak1
        else:
            peak_min = peak1
            peak_max = peak2

        data.peak = [str(peak_min),str(peak_max)]
        self.active_data = data

        self.ui.normPeakFromValue.setValue(peak_min)
        self.ui.normPeakToValue.setValue(peak_max)

        # save new settings
        self.save_new_settings()

        if withPlotUpdate:
            # refresh plots
            self.plot_overview_REFL(plot_ix=True, plot_yt=True, plot_yi=True)

        CheckErrorWidgets(self)
	self.fileHasBeenModified()

    # norm back spinboxes
    def norm_back_spinbox_validation(self, withPlotUpdate=True):
        '''
        This function, reached when the user is done editing the
        spinboxes (ENTER, leaving the spinbox) 
        will make sure the min value is < max value  
        '''

        bigTableData = self.bigTableData
        #[row,col] = self.getCurrentRowColumnSelected()
        row = self._cur_row_selected
        col = self._cur_column_selected
        if col != 0:
            col = 1
        data = bigTableData[row,col]
        data = data.active_data

        back1 = self.ui.normBackFromValue.value()
        back2 = self.ui.normBackToValue.value()

        if (back1 > back2):
            back_min = back2
            back_max = back1
        else:
            back_min = back1
            back_max = back2

        data.back = [str(back_min),str(back_max)]
        self.active_data = data

        self.ui.normBackFromValue.setValue(back_min)
        self.ui.normBackToValue.setValue(back_max)

        # save new settings
        self.save_new_settings()

        if withPlotUpdate:
            # refresh plots
            self.plot_overview_REFL(plot_ix=True, plot_yt=True, plot_yi=True)

        CheckErrorWidgets(self)
	self.fileHasBeenModified()

    # data low resolution spinboxes
    def norm_lowres_spinbox_validation(self):
        '''
        This function, reached when the user is done editing the
        spinboxes (ENTER, leaving the spinbox) 
        will make sure the min value is < max value  
        '''
        bigTableData = self.bigTableData
        row = self._cur_row_selected
        col = self._cur_column_selected
        if col != 0:
            col = 1

        data = bigTableData[row,col]
        if data is None:
            return
        data = data.active_data

        lowres1 = self.ui.normLowResFromValue.value()
        lowres2 = self.ui.normLowResToValue.value()

        if (lowres1 > lowres2):
            lowres_min = lowres2
            lowres_max = lowres1
        else:
            lowres_min = lowres1
            lowres_max = lowres2

        data.low_res = [str(lowres_min),str(lowres_max)]
        self.active_data = data

        self.ui.normLowResFromValue.setValue(lowres_min)
        self.ui.normLowResToValue.setValue(lowres_max)

        # save new settings
        self.save_new_settings()

        # refresh plots
        self.plot_overview_REFL(plot_ix=True, plot_yt=True, plot_yi=True)
	self.fileHasBeenModified()

    def useAutoPeakBackSelectionCheckBox(self, status):
        self.ui.autoPeakBackSelectionFrame.setEnabled(status)
	self.fileHasBeenModified()

    def useGeometryCorrectionCheckBox(self, status):
        self.ui.geometryCorrectionFrame.setEnabled(status)
	self.fileHasBeenModified()

    def useScalingFactorConfigCheckBox(self, status):
        self.ui.scalingFactorConfigFrame.setEnabled(status)
	self.fileHasBeenModified()

    def reduction_table_right_click(self, pos):
        menu = QtGui.QMenu(self)
        modify = menu.addAction("Edit ...")
        menu.addSeparator()
        #copy = menu.addAction("Copy")
        #paste = menu.addAction("Paste")
        #if self.reduction_table_copied_field != '':
            #paste.setEnabled(True)  
        #else:
            #paste.setEnabled(False)
        #menu.addSeparator()
        removeRow = menu.addAction("Delete Row")
	clearTable = menu.addAction('Clear Table')
        menu.addSeparator()
        displayMeta = menu.addAction("Display Metadata ...")
        action = menu.exec_(QtGui.QCursor.pos())

        if action == modify:
            self.reductionTableEdit()
        #elif action == copy:
            #self.reductionTableCopy()
        #elif action == paste:
            #self.reductionTablePaste()
        elif action == removeRow:
            self.reductionTableDeleteRow()
	elif action == clearTable:
	    self.reductionTableClearTable()
        elif action == displayMeta:
            self.reductionTableDisplayMetadata()
	    
	self.fileHasBeenModified()

    def reductionTableCopy(self):
        _item = self.ui.reductionTable.selectedItems()
        self.reduction_table_copied_field = _item[0].text()
        #[row,col] = self.getCurrentRowColumnSelected()
        row = self._cur_row_selected
        col = self._cur_column_selected
        self.reduction_table_copied_row_col = [row,col]

    def reductionTablePaste(self):
        #[newrow, newcol] = self.getCurrentRowColumnSelected()
        newrow = self._cur_row_selected
        newcol = self._cur_column_selected
        [oldrow, oldcol] = self.reduction_table_copied_row_col
        if newrow == oldrow and newcol == oldcol:
            return
        bigTable = self.bigTableData
        bigTable[newrow,newcol] = bigTable[oldrow,oldcol]
        self.bigTableData = bigTable
        self._fileOpenDoneREFL(data=bigTable[newrow, newcol])

    def reductionTableEdit(self):
        ''' Modify data or norm run number '''
        [row,col] = self.getCurrentRowColumnSelected()
        _editTable = TableReductionRunEditor(parent=self, col=col, row=row)
        _editTable.show()

    @waiting_effects
    def reductionTableDisplayMetadata(self):
        bigTableData = self.bigTableData
#    [row,col] = self.getCurrentRowColumnSelected()
        row = self._cur_row_selected
        col = self._cur_column_selected
        if col != 0:
            col = 1
        data = bigTableData[row,col]
        active_data = data.active_data
        _displayMeta = DisplayMetadata(self, active_data)
        _displayMeta.show()

    def reductionTableDeleteRow(self):
        self.removeRowReductionTable()

    def reductionTableClearTable(self):
	self.clear_plot_overview_REFL(True)
	self.clear_plot_overview_REFL(False)
	self.clearMetadataWidgets()
	nbrRow = self.ui.reductionTable.rowCount()
	bigTableData = self.bigTableData
	for _row in range(nbrRow):
	    bigTableData = np.delete(bigTableData, 0, axis=0)
	    self.ui.reductionTable.removeRow(0)
	self.bigTableData = bigTableData
	self.ui.reductionTable.show()
	self.allTabWidgetsEnabler(enableFlag=False)
	self.ui.reductionTable.setEnabled(False)
	
    def save_new_settings(self):
        '''
        This function will retrieve all the settings (peak, background...)
        and will save them in the corresponding data or norm file (if any)
        '''

        #[r,c] = self.getCurrentRowColumnSelected()
        r = self._cur_row_selected
        c = self._cur_column_selected
        data = self.bigTableData[r,2]

        if data is None:
            return

        if c==0: #data

            use_it_flag = True

            peak = [self.ui.dataPeakFromValue.value(), 
                    self.ui.dataPeakToValue.value()]
            data.data_peak = peak

            back = [self.ui.dataBackFromValue.value(),
                    self.ui.dataBackToValue.value()]
            data.data_back = back

            low_res = [self.ui.dataLowResFromValue.value(),
                       self.ui.dataLowResToValue.value()]
            data.data_low_res = low_res

            back_flag = self.ui.dataBackgroundFlag.isChecked()
            data.data_back_flag = back_flag

            low_res_flag = self.ui.dataLowResFlag.isChecked()
            data.data_low_res_flag = low_res_flag

        else:

            use_it_flag = self.ui.useNormalizationFlag.isChecked()
            data.norm_flag = use_it_flag

            peak = [self.ui.normPeakFromValue.value(),
                    self.ui.normPeakToValue.value()]
            data.norm_peak = peak

            back = [self.ui.normBackFromValue.value(),
                    self.ui.normBackToValue.value()]
            data.norm_back = back

            back_flag = self.ui.normBackgroundFlag.isChecked()
            data.norm_back_flag = back_flag

            low_res = [self.ui.normLowResFromValue.value(),
                       self.ui.normLowResToValue.value()]
            data.norm_low_res = low_res

            low_res_flag = self.ui.normLowResFlag.isChecked()
            data.norm_low_res_flag = low_res_flag

        tof_range = [self.ui.TOFmanualFromValue.text(),
                     self.ui.TOFmanualToValue.text()]
        data.tof_range = tof_range

        tof_units = 'ms'
        data.tof_units = tof_units

        tof_auto_flag = self.ui.dataTOFautoMode.isChecked()
        data.tof_auto_flag = tof_auto_flag

        # put back info in right place
        self.bigTableData[r,2] = data


    def getTrueCurrentRowColumnSelected(self):
        '''
        will determine the current row and column selected in the big Table.
        '''
        rangeSelected = self.ui.reductionTable.selectedRanges()
        if rangeSelected == []:
            return [-1, -1]

        col = rangeSelected[0].leftColumn()
        row = rangeSelected[0].topRow()
        return [row, col]

    def getCurrentRowColumnSelected(self):
        '''
        will determine the current row and column selected in the big Table.
        return 0 or 1
        '''
        try:
            rangeSelected = self.ui.reductionTable.selectedRanges()
            col = rangeSelected[0].leftColumn()
            row = rangeSelected[0].topRow()
            if col < 6:
                col = 0
            else:
                col = 1
            return [row, col]
        except IndexError:
            return [self._prev_row_selected, self._prev_col_selected]

    @log_call
    def open_reduction_preview(self):
        dia=ReductionPreviewDialog(self)
        dia.show()
        self.open_plots.append(dia)

    @log_call
    def open_rawdata_dialog(self):
        dia=RawCompare(self)
        dia.show()

    @log_call
    def open_polarization_window(self):
        dia=PolarizationDialog(self)
        dia.show()

    @log_call
    def open_nxs_dialog(self):
        if self.active_data is None: return
        dia=NXSDialog(self, self.active_data.origin)
        dia.show()

    @log_call
    def open_filter_dialog(self):
        filter_=u'Reflectivity (*.dat);;All (*.*)'
        names=QtGui.QFileDialog.getOpenFileNames(self, u'Select reflectivity file(s)...',
                                                 directory=paths.results,
                                                 filter=filter_)
        if names:
            filtered_points=[]
            for name in names:
                text=unicode(open(name, 'rb').read(), 'utf8')
                header=[]
                for line in text.splitlines():
                    if not line.startswith('#'):
                        break
                    header.append(line)
                header='\n'.join(header)
                try:
                    parser=HeaderParser(header)
                except:
                    warning('Open file %s:\nCould not evaluate header information, probably the wrong format:\n\n'%
                            name,
                            exc_info=True)
                    continue
                if not (parser.export_type=='Specular' and len(parser.states_in_file)==1):
                    warning('Open file %s:\nThis function only works for reflectivity files with a single spin state.'%
                            name)
                    continue
                if 'Filtered Indices' in parser.sections:
                    # if opening a already filtered dataset the original is opened with the used filters
                    origin=parser.sections['Filtered Indices'][0].split(': ', 1)[1].strip()
                    if os.path.exists(origin):
                        name=origin
                        filtered_points=eval(parser.sections['Filtered Indices'][1].split(': ', 1)[1])

                dia=PointPicker(name, filtered_points)
                result=dia.exec_()
                if result:
                    filtered_points=dia.filtered_idxs

    @log_call
    @waiting_effects
    def loading_configuration(self):
        _path = self.path_config
        filename = QtGui.QFileDialog.getOpenFileName(self,'Open Configuration File', _path)      

        if not (filename == ""):
            self.loading_configuration_file(filename)

            if self.reducedFilesLoadedObject is None:
                _reducedFilesLoadedObject = ReducedConfigFilesHandler(self)
            else:
                _reducedFilesLoadedObject = self.reducedFilesLoadedObject
            _reducedFilesLoadedObject.addFile(filename)
            _reducedFilesLoadedObject.updateGui()
            self.reducedFilesLoadedObject = _reducedFilesLoadedObject

            self.current_loaded_file = filename
	    self.resetFileHasBeenModified()

    def loading_configuration_file(self, filename):
        self.path_config = os.path.dirname(filename)

        # make sure the reductionTable is empty
        nbrRow = self.ui.reductionTable.rowCount()
        if nbrRow > 0:
            for _row in range(nbrRow):
                self.ui.reductionTable.removeRow(0)

	ImportXMLquickNXSConfig(parent=self, filename=filename)
        self.enableWidgets(checkStatus=True)
        CheckErrorWidgets(self)

    @log_call
    def saving_configuration_as(self):
        _path = self.path_config
        filename = QtGui.QFileDialog.getSaveFileName(self, 'Save Configuration File', _path)
        if not(filename == ""):
	    self.savingConfigurationStep2(filename)
	    
    @log_call
    def saving_configuration(self):
	filename = self.current_loaded_file
	self.savingConfigurationStep2(filename)
    
    def savingConfigurationStep2(self, filename):
            self.path = os.path.dirname(filename)
	    ExportXMLquickNXSConfig(parent=self, filename=filename)
#            self.saveConfig(filename)
            if self.reducedFilesLoadedObject is None:
                _reducedFilesLoadedObject = ReducedConfigFilesHandler(self)
            else:
                _reducedFilesLoadedObject = self.reducedFilesLoadedObject
            _reducedFilesLoadedObject.addFile(filename)
            _reducedFilesLoadedObject.updateGui()
            self.reducedFilesLoadedObject = _reducedFilesLoadedObject
	    
	    self.current_loaded_file = filename
	    self.resetFileHasBeenModified()
	    
    def isPeakBackSelectionOkFromNXSdata(self, active_data):
	peak = active_data.peak
	back = active_data.back
	back_flag = active_data.back_flag
	return self.isPeakBackSelectionOk(peak, back, back_flag)

    def isPeakBackSelectionOkFromConfig(self, _metadataObject, type='data'):
	if type == 'data':
	    peak = _metadataObject.data_peak
	    back = _metadataObject.data_back
	    back_flag = _metadataObject.data_back_flag
	else:
	    peak = _metadataObject.norm_peak
	    back = _metadataObject.norm_back
	    back_flag = _metadataObject.norm_back_flag
	return self.isPeakBackSelectionOk(peak, back, back_flag)
	
    def isPeakBackSelectionOk(self, peak, back, back_flag):
	if back_flag:
	    peak_min = int(min(peak))
	    peak_max = int(max(peak))
	    back_min = int(min(back))
	    back_max = int(max(back))
	    if back_min > peak_min:
		return False
	    if back_max < peak_max:
		return False
	    if peak_min == peak_max:
		return False
	    return True
	else:
	    return True

    def getMetadataObject(self, node):
        '''
        will retrieve the metadata from the XML and will create an instance of LConfigDataset
        '''
        iMetadata = LConfigDataset()

        _peak_min = self.getNodeValue(node, 'from_peak_pixels')
        _peak_max = self.getNodeValue(node, 'to_peak_pixels')
        iMetadata.data_peak = [_peak_min, _peak_max]

        _back_min = self.getNodeValue(node, 'back_roi1_from')
        _back_max = self.getNodeValue(node, 'back_roi1_to')
        iMetadata.data_back = [_back_min, _back_max]

        _low_res_min = self.getNodeValue(node, 'x_min_pixel')
        _low_res_max = self.getNodeValue(node, 'x_max_pixel')
        iMetadata.data_low_res = [_low_res_min, _low_res_max]

        _back_flag = self.getNodeValue(node, 'background_flag')
        iMetadata.data_back_flag = _back_flag

        _low_res_flag = self.getNodeValue(node, 'x_range_flag')
        iMetadata.data_low_res_flag = _low_res_flag

        _tof_min = self.getNodeValue(node, 'from_tof_range')
        _tof_max = self.getNodeValue(node, 'to_tof_range')
        if float(_tof_min) < 500:  # ms
            _tof_min = str(float(_tof_min) * 1000)
            _tof_max = str(float(_tof_max) * 1000)
        iMetadata.tof_range = [_tof_min, _tof_max]

        _q_min = self.getNodeValue(node, 'from_q_range')
        _q_max = self.getNodeValue(node, 'to_q_range')
        iMetadata.q_range = [_q_min, _q_max]

        _lambda_min = self.getNodeValue(node, 'from_lambda_range')
        _lambda_max = self.getNodeValue(node, 'to_lambda_range')
        iMetadata.lambda_range = [_lambda_min, _lambda_max]

        iMetadata.tof_units = 'micros'

        _data_sets = self.getNodeValue(node, 'data_sets')
        iMetadata.data_sets = _data_sets

        _data_lambda = self.getNodeValue(node, 'data_lambda_requested')
        iMetadata.data_lambda_requested = _data_lambda

        _tof_auto = self.getNodeValue(node, 'tof_range_flag')
        iMetadata.tof_auto_flag = _tof_auto

        _norm_flag = self.getNodeValue(node, 'norm_flag')
        iMetadata.norm_flag = _norm_flag

        _peak_min = self.getNodeValue(node, 'norm_from_peak_pixels')
        _peak_max = self.getNodeValue(node, 'norm_to_peak_pixels')
        iMetadata.norm_peak = [_peak_min, _peak_max]

        _back_min = self.getNodeValue(node, 'norm_from_back_pixels')
        _back_max = self.getNodeValue(node, 'norm_to_back_pixels')
        iMetadata.norm_back = [_back_min, _back_max]

        _norm_sets = self.getNodeValue(node, 'norm_dataset')
        iMetadata.norm_sets = _norm_sets

        _low_res_min = self.getNodeValue(node, 'norm_x_min')
        _low_res_max = self.getNodeValue(node, 'norm_x_max')
        iMetadata.norm_low_res = [_low_res_min, _low_res_max]

        _back_flag = self.getNodeValue(node, 'norm_background_flag')
        iMetadata.norm_back_flag = _back_flag

        _low_res_flag = self.getNodeValue(node, 'norm_x_range_flag')
        iMetadata.norm_low_res_flag = _low_res_flag

        _norm_lambda = self.getNodeValue(node, 'norm_lambda_requested')
        iMetadata.norm_lambda_requested = _norm_lambda

        return iMetadata

    def sf_browse_button(self):
        filename = QtGui.QFileDialog.getOpenFileName(self,'Open scaling factor file', '.',"sfConfig (*.cfg)")

        if filename is not u'':
            self.ui.scalingFactorFile.setText(filename)
            self.populate_sf_widgets(filename)
	    self.fileHasBeenModified()

    def populate_sf_widgets(self, filename):
        listMedium = self.parse_scaling_factor_file(filename)
        self.ui.selectIncidentMediumList.addItems(listMedium)


    def parse_scaling_factor_file(self, filename):
        '''
        will parse the scaling factor file
        '''
        f = open(filename,'r')
        sfFactorTable = []
        for line in f.read().split('\n'):
            if (len(line) > 0) and (line[0] != '#'):
                sfFactorTable.append(line.split(' '))
        f.close()

        uniqIncidentMedium = self.list_uniq_incident_medium(sfFactorTable)
        return uniqIncidentMedium


    def list_uniq_incident_medium(self, table):

        [nbr_row, nbr_column] = shape(table)
        first_column_only = []
        for i in range(nbr_row):
            _line_split = table[i][0].split('=')
            first_column_only.append(_line_split[1])

        return sorted(set(first_column_only))

    def select_current_SF(self):

        sf_status = 'auto'
        if self.ui.manualSF.isChecked(): 
            sf_status = 'manual'
        elif self.ui.oneSF.isChecked():
            sf_status = '1'

        bigTableData = self.bigTableData
        nbr_row = self.ui.reductionTable.rowCount()
        for i in range(nbr_row):
            _data = bigTableData[i,2]
            if sf_status == 'auto':
                _data.sf = _data.sf_auto
            elif sf_status == 'manual':
                _data.sf = _data.sf_manual
            else:
                _data.sf = 1
                bigTableData[i,2] = _data

        self.bigTableData = bigTableData

    def calculate_autoSF(self):
        '''
        Determine the auto SF coefficient to stitch the data
        '''
        bigTableData = self.bigTableData
        nbr_row = self.ui.reductionTable.rowCount()

        _myReduction = CalculateSF(bigTableData, self)
        bigTableData = _myReduction.getAutoScaledData()
        self.bigTableData = bigTableData

        for i in range(nbr_row):
            _data = bigTableData[i,2]
            sf = _data.sf_auto

    @log_call
    @waiting_effects
    def runReduction(self):
        '''
        Run the full reduction
        '''
        bigTableData = self.bigTableData
        if bigTableData[0,0] is None:
            warning(u'Define at least one data run to reduce.',
                    extra={'title': u'Define a dataset'})
            return

        _reduction = REFLReduction(self)

        # calculate auto SF coefficient
        self.calculate_autoSF()
        bigTableData = self.bigTableData

        # select right SF
        self.select_current_SF()

        # display data reduced
        self.plot_reduced_data()

        # enabled all stitching related widgets
        self.enabled_reduced_widgets(True)

        # move to stitching table tab
        self.ui.plotTab.setCurrentIndex(1)      

        # save current view limits of plot
        self.initializeReduceViewObject()

    def enabled_reduced_widgets(self, status):
        # overview tab
        self.ui.reflectivity_plot.setEnabled(status)
        self.ui.RvsQ.setEnabled(status)
        self.ui.RQ4vsQ.setEnabled(status)
        self.ui.LogRvsQ.setEnabled(status)
        # stitching tab
        self.ui.dataStitchingTable.setEnabled(status)
        self.ui.autoSF.setEnabled(status)
        self.ui.manualSF.setEnabled(status)
        self.ui.oneSF.setEnabled(status)
        self.ui.data_stitching_plot.setEnabled(status)
        self.ui.RvsQ_2.setEnabled(status)
        self.ui.RQ4vsQ_2.setEnabled(status)
        self.ui.LogRvsQ_2.setEnabled(status)

    def initializeReduceViewObject(self):
        bigTableData = self.bigTableData
        _data = bigTableData[0,0]
        _active_data = _data.active_data

        [xmin,xmax] = self.ui.data_stitching_plot.canvas.ax.xaxis.get_view_interval()
        [ymin,ymax] = self.ui.data_stitching_plot.canvas.ax.yaxis.get_view_interval()
        _active_data.all_plot_axis.reduced_plot_stitching_tab_view_interval = [xmin,xmax,ymin,ymax]
        _active_data.all_plot_axis.reduced_plot_stitching_tab_data_interval = [xmin,xmax,ymin,ymax]
        _data.active_data = _active_data
        bigTableData[0,0] = _data
        self.bigTableData = bigTableData
        self.ui.data_stitching_plot.toolbar.home_settings = [xmin,xmax,ymin,ymax]

    def reduce_plot_RvsQ_radiobutton(self):
        self.reduce_plot_radiobuttons(option='RvsQ')

    def reduce_plot_RQ4vsQ_radiobutton(self):
        self.reduce_plot_radiobuttons(option='RQ4vsQ')

    def reduce_plot_LogRvsQ_radiobutton(self):
        self.reduce_plot_radiobuttons(option='LogRvsQ')

    def reduce_plot_radiobuttons(self, option='RvsQ'):
        status_RvsQ = False
        status_RQ4vsQ = False
        status_LogRvsQ = False

        if option == 'RvsQ':
            status_RvsQ = True
        elif option == 'RQ4vsQ':
            status_RQ4vsQ = True
        else:
            status_LogRvsQ = True

        self.ui.RvsQ.setChecked(status_RvsQ)
        self.ui.RQ4vsQ.setChecked(status_RQ4vsQ)
        self.ui.LogRvsQ.setChecked(status_LogRvsQ)

        self.replot_reduced_data()

    def reduce_plot_RvsQ_2_radiobutton(self):
        self.stitching_plot_radiobuttons(option='RvsQ')

    def reduce_plot_RQ4vsQ_2_radiobutton(self):
        self.stitching_plot_radiobuttons(option='RQ4vsQ')

    def reduce_plot_LogRvsQ_2_radiobutton(self):
        self.stitching_plot_radiobuttons(option='LogRvsQ')

    def stitching_plot_radiobuttons(self, option='RvsQ'):
        status_RvsQ = False
        status_RQ4vsQ = False
        status_LogRvsQ = False

        if option == 'RvsQ':
            status_RvsQ = True
        elif option == 'RQ4vsQ':
            status_RQ4vsQ = True
        else:
            status_LogRvsQ = True

        self.ui.RvsQ_2.setChecked(status_RvsQ)
        self.ui.RQ4vsQ_2.setChecked(status_RQ4vsQ)
        self.ui.LogRvsQ_2.setChecked(status_LogRvsQ)

        self.replot_stitched_data()

    def clearStitchingTable(self):
        self.ui.dataStitchingTable.clearContents()
        nbrRow = self.ui.dataStitchingTable.rowCount()
        if nbrRow > 0:
            for _row in range(nbrRow):
                self.ui.dataStitchingTable.removeRow(0)

    def plot_reduced_data(self):
        self.clearStitchingTable()

        loadedAscii = reducedAsciiLoader(self,asciiFilename='', isLiveReduced=True, bigTableData=self.bigTableData )    
        if self.stitchingAsciiWidgetObject is None:
            self.stitchingAsciiWidgetObject = stitchingAsciiWidgetObject(self, loadedAscii)
        else:
            self.stitchingAsciiWidgetObject.addData(loadedAscii)

        bigTableData= self.bigTableData
        data0 = bigTableData[0,0]
        data0_active_data = data0.active_data
        isylog = data0_active_data.all_plot_axis.is_reduced_plot_stitching_tab_ylog
        isxlog = data0_active_data.all_plot_axis.is_reduced_plot_stitching_tab_xlog
        self.stitchingAsciiWidgetObject.updateDisplay(isylog=isylog, isxlog=isxlog)

        # refresh reductionTable content (lambda range, Q range...etc)
#		self.update_reductionTable()
        self.update_stitchingTable()
        self.replot_reduced_data()

    def refresh_stitching_ascii_plot(self):
        if self.stitchingAsciiWidgetObject is None:
            return

        self.stitchingAsciiWidgetObject.updateStatus()

        bigTableData= self.bigTableData
        data0 = bigTableData[0,0]
        data0_active_data = data0.active_data
        _isylog = data0_active_data.all_plot_axis.is_reduced_plot_stitching_tab_ylog
        _isxlog = data0_active_data.all_plot_axis.is_reduced_plot_stitching_tab_xlog
        self.stitchingAsciiWidgetObject.updateDisplay(isylog=_isylog, isxlog=_isxlog)

    def replot_reduced_data(self):
        '''
        plot the data after reduction
        '''
        bigTableData = self.bigTableData
        nbr_row = self.ui.reductionTable.rowCount()

        reflectivity_plot = self.ui.reflectivity_plot

        _colors = colors.COLOR_LIST
        _colors.append(_colors)

        # start by clearing plot
        reflectivity_plot.clear()
        reflectivity_plot.draw()

        for i in range(nbr_row):
            _data = bigTableData[i,2]
            _q_axis = _data.q_axis_for_display
            _y_axis = _data.y_axis_for_display
            _e_axis = _data.e_axis_for_display
            sf = _data.sf

            _y_axis = _y_axis / sf
            _e_axis = _e_axis / sf

            [y_axis_red, e_axis_red] = self.plot_selected_output_reduced(_q_axis,
                                                                         _y_axis, 
                                                                         _e_axis)

            reflectivity_plot.errorbar(_q_axis, y_axis_red, yerr=e_axis_red, color=_colors[i])

        reflectivity_plot.set_xlabel(u'Q (1/Angstroms)')
        type = self.get_selected_output_reduced()    
        if type == 'RvsQ':
            reflectivity_plot.set_ylabel(u'R')
        elif type == 'RQ4vsQ':
            reflectivity_plot.set_ylabel(u'RQ4')
        else:
            reflectivity_plot.set_ylabel(u'Log(Q))')

        reflectivity_plot.draw()

        _data = bigTableData[0,0]
        if _data.active_data.all_plot_axis.is_reduced_plot_overview_tab_ylog:
            reflectivity_plot.canvas.ax.set_yscale('log')
        else:
            reflectivity_plot.canvas.ax.set_yscale('linear')

        if _data.active_data.all_plot_axis.is_reduced_plot_overview_tab_xlog:
            reflectivity_plot.canvas.ax.set_xscale('log')
        else:
            reflectivity_plot.canvas.ax.set_xscale('linear')

        reflectivity_plot.draw()

        liveDataSet = reducedAsciiLoader(self, '', True, bigTableData)
        if self.stitchingAsciiWidgetObject is None:
            self.stitchingAsciiWidgetObject = stitchingAsciiWidgetObject(self, liveDataSet)
        else:
            self.stitchingAsciiWidgetObject.addData(liveDataSet)

        _isylog = _data.active_data.all_plot_axis.is_reduced_plot_stitching_tab_ylog
        _isxlog = _data.active_data.all_plot_axis.is_reduced_plot_stitching_tab_xlog
        self.stitchingAsciiWidgetObject.updateDisplay(isylog=_isylog, isxlog=_isxlog)


    def replot_stitched_data(self):
        '''
        plot the data after stitching
        '''
        bigTableData= self.bigTableData
        data0 = bigTableData[0,0]
        data0_active_data = data0.active_data
        _isylog = data0_active_data.all_plot_axis.is_reduced_plot_stitching_tab_ylog
        _isxlog = data0_active_data.all_plot_axis.is_reduced_plot_stitching_tab_xlog

        _type = self.get_selected_output_stitched()
        self.stitchingAsciiWidgetObject.updateDisplay(isylog=_isylog, isxlog=_isxlog, yaxistype=_type)

        bigTableData = self.bigTableData
        nbr_row = self.ui.reductionTable.rowCount()

        data_stitching_plot = self.ui.data_stitching_plot

        _colors = colors.COLOR_LIST
        _colors.append(_colors)

        # start by clearing plot
        data_stitching_plot.clear()
        data_stitching_plot.draw()

        for i in range(nbr_row):
            _data = bigTableData[i,2]
            _q_axis = _data.q_axis_for_display
            _y_axis = _data.y_axis_for_display
            _e_axis = _data.e_axis_for_display
            sf = _data.sf

            _y_axis = _y_axis / sf
            _e_axis = _e_axis / sf

            [y_axis_stit, e_axis_stit] = self.plot_selected_output_stitched(_q_axis,
                                                                            _y_axis, 
                                                                            _e_axis)

            data_stitching_plot.errorbar(_q_axis, y_axis_stit, yerr=e_axis_stit, color=_colors[i])
            data_stitching_plot.draw()

        _data0 = bigTableData[0,0]
        if _data0.active_data.all_plot_axis.is_reduced_plot_stitching_tab_ylog:
            data_stitching_plot.canvas.ax.set_yscale('log')
        else:
            data_stitching_plot.canvas.ax.set_yscale('linear')

        if _data0.active_data.all_plot_axis.is_reduced_plot_stitching_tab_xlog:
            data_stitching_plot.canvas.ax.set_xscale('log')
        else:
            data_stitching_plot.canvas.ax.set_xscale('linear')

        data_stitching_plot.set_xlabel(u'Q (1/Angstroms)')
        type = self.get_selected_output_stitched()
        if type == 'RvsQ':
            data_stitching_plot.set_ylabel(u'R')
        elif type == 'RQ4vsQ':
            data_stitching_plot.set_ylabel(u'RQ4')
        else:
            data_stitching_plot.set_ylabel(u'Log(Q))')

        data_stitching_plot.draw()


    def get_selected_output_reduced(self):
        type = 'RvsQ'
        if self.ui.RQ4vsQ.isChecked():
            type = 'RQ4vsQ'
        elif self.ui.LogRvsQ.isChecked():
            type = 'LogRvsQ'
        return type

    def plot_selected_output_reduced(self, _q_axis, _y_axis, _e_axis):
        '''
        will format the data to agree with the format (RvsQ, RQ^4 vs Q or LogR vs Q) selected
        '''
        type = self.get_selected_output_reduced()
        [final_y_axis, final_e_axis] = self.get_selected_output(type, _q_axis, _y_axis, _e_axis)
        return [final_y_axis, final_e_axis]

    def get_selected_output_stitched(self):
        type = 'RvsQ'
        if self.ui.RQ4vsQ_2.isChecked():
            type = 'RQ4vsQ'
        elif self.ui.LogRvsQ_2.isChecked():
            type = 'LogRvsQ'
        return type    

    def plot_selected_output_stitched(self, _q_axis, _y_axis, _e_axis):
        '''
        will format the data to agree with the format (RvsQ, RQ^4 vs Q or LogR vs Q) selected
        '''
        type = self.get_selected_output_stitched()
        [final_y_axis, final_e_axis] = self.get_selected_output(type, _q_axis, _y_axis, _e_axis)
        return [final_y_axis, final_e_axis]


    def get_selected_output(self, type, _q_axis, _y_axis, _e_axis):

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

    @waiting_effects
    def output_selected_data_into_crtof_ascii(self):    #REMOVEME
        '''
        The RTOF of the selected data set (data or norm) will be output into an ASCII file
        '''
        bigTableData = self.bigTableData
        if bigTableData[0,0] is None and bigTableData[0,1] is None:
            info('No Data!')
            return

        #[row,col] = self.getCurrentRowColumnSelected()
        row = self._cur_row_selected
        col = self._cur_column_selected
        if col == 1:
            table_col = 6
        else:
            table_col = 0
        run_number = self.ui.reductionTable.item(row,table_col).text()
        default_filename = 'REFL_' + run_number + '_crtof.txt' #TODO HARDCODED INSTRUMENT
        _path = self.path_ascii
        default_filename = _path + '/' + default_filename
        filename = QtGui.QFileDialog.getSaveFileName(self, 'Create RTOF ASCII file', default_filename)

        # user cancelled request
        if str(filename).strip() == '':
            info('User Canceled Output Ascii!')
            return

        self.path_ascii = os.path.dirname(filename)

        bigTableData = self.bigTableData
        _data = bigTableData[row,col]
        _active_data = _data.active_data

        tof_axis = _active_data.tof_axis_auto_with_margin[0:-1]/1000

        countstofdata = _active_data.countstofdata
#    Ixyt = _active_data.Ixyt
    #  Exyt = _active_data.Exyt

    #  [_Ixt, _Ext] = utilities.weighted_sum_dim3(Ixyt, Exyt, 1)
    # [_It, _Et] = utilities.weighted_sum_dim2(_Ixt, _Ext, 0)

        text = ["#Counts vs TOF", "TOF(ms) - Counts"]
        sz = len(tof_axis)
        for i in range(sz):
#      _line = str(tof_axis[i]) + ' ' + str(_It[i]) + ' ' + str(_Et[i])
            _line = str(tof_axis[i]) + ' ' + str(countstofdata[i])
            text.append(_line)

        utilities.write_ascii_file(filename, text)

    @waiting_effects
    def output_selected_data_into_ivspx_ascii(self):
        '''
        ascii of Counts vs Pixels 
        '''
        bigTableData = self.bigTableData
        if bigTableData[0,0] is None and bigTableData[0,1] is None:
            info('No Data!')
            return

        #[row,col] = self.getCurrentRowColumnSelected()
        row = self._cur_row_selected
        col = self._cur_column_selected
        if col == 1:
            table_col = 6
        else:
            table_col = 0
        run_number = self.ui.reductionTable.item(row,table_col).text()
        default_filename = 'REFL_' + run_number + '_rpx.txt' #TODO HARDCODED INSTRUMENT
        _path = self.path_ascii
        default_filename = _path + '/' + default_filename
        filename = QtGui.QFileDialog.getSaveFileName(self, 'Create Counts vs Pixel ASCII file', default_filename)

        # user cancelled request
        if str(filename).strip() == '':
            info('User Canceled Output Ascii!')
            return

        self.path_ascii = os.path.dirname(filename)

        bigTableData = self.bigTableData
        _data = bigTableData[row,col]
        _active_data = _data.active_data

        #Ixyt = _active_data.Ixyt
        #Exyt = _active_data.Exyt

        #[_Ixy, _Exy] = utilities.weighted_sum_dim3(Ixyt, Exyt, 2)
        #[_Iy, _Ey] = utilities.weighted_sum_dim2(_Ixy, _Exy, 0)

        ycountsdata = _active_data.ycountsdata
        xaxis = range(len(ycountsdata))

        text = ["#Counts vs pixel integrated over TOF range and x-axis", "Pixels - Counts"]
        sz = len(xaxis)
        for i in range(sz):
#      _line = str(i) + ' ' + str(_Iy[i]) + ' ' + str(_Ey[i])
            _line = str(i) + ' ' + str(ycountsdata[i])
            text.append(_line)

        utilities.write_ascii_file(filename, text)


    def output_data_into_ascii(self):
        '''
        will use ascii format to output the data
        '''
        cell0 = self.ui.reductionTable.item(0,0)
        # if nothing in big table, stop here
        if cell0 is None:
            info('No Data Reduced!')
            return

        # if no data reduced, stop here
        bigTableData = self.bigTableData
        _data = bigTableData[0,0]
        _q_axis = _data.reduce_q_axis
        if _q_axis is None:
            info('No Data Reduced!')
            return

        run_number = self.ui.reductionTable.item(0,0).text()
        default_filename = 'REFL_' + run_number + '_combined_data.txt' #TODO HARDCODED INSTRUMENT
        _path = self.path_ascii
        default_filename = _path + '/' + default_filename
        filename = QtGui.QFileDialog.getSaveFileName(self, 'Create ASCII file', default_filename)

        # user cancelled request
        if str(filename).strip() == '':
            info('User Canceled Output Ascii!')
            return

        self.path_ascii = os.path.dirname(filename)

        _4th_column_flag = self.ui.output4thColumnFlag.isChecked()
        if _4th_column_flag:
            dq0 = float(self.ui.dq0Value.text())
            dq_over_q = float(self.ui.dQoverQvalue.text())
            line1 = '#dQ0[1/Angstrom]=' + str(dq0)
            line2 = '#dQ/Q=' + str(dq_over_q)
            line3 = '#Q(1/Angstrom) R delta_R Precision'
            text = [line1, line2, line3]
        else:
            text = ['#Q(1/Angstrom) R delta_R']

        [q_axis, y_axis, e_axis] = self.produce_workspace_with_common_q_axis()

        sz = len(q_axis)-1
        for i in range(sz):

            # do not display data where R < 1e-15
            if (y_axis[i] > 1e-15):
                _line = str(q_axis[i])
                _line += ' ' + str(y_axis[i])
                _line += ' ' + str(e_axis[i])
                if _4th_column_flag:
                    _precision = str(dq0 + dq_over_q * q_axis[i])
                    _line += ' ' + _precision
                text.append(_line)

        utilities.write_ascii_file(filename, text)


    def applySF(self, row, y_array, e_array):
        """
        Apply SF
        """

        _data = self.bigTableData[row,0]

        if self.ui.autoSF.isChecked():
            _sf = _data.sf_auto
        elif self.ui.manualSF.isChecked():
            _sf = _data.sf_manual
        else:
            _sf = 1

        y_array /= _sf
        e_array /= _sf

        return [y_array, e_array]

    def produce_workspace_with_common_q_axis(self):
        '''
        In order to produce output ascii file, we need to get all the data sets with a common q axis
        '''

        bigTableData = self.bigTableData
        nbrRow = self.ui.reductionTable.rowCount()

        minQ = 100
        maxQ = 0

        for i in range(nbrRow):

            tmp_wks_name = 'wks_' + str(i)

            _data = bigTableData[i,0]

            _q_axis = _data.reduce_q_axis
            _y_axis = _data.reduce_y_axis[:-1]
            _e_axis = _data.reduce_e_axis[:-1]

            [_y_axis, _e_axis] = self.applySF(i, _y_axis, _e_axis)


            minQ = min([_q_axis[0], minQ])
            maxQ = max([_q_axis[-1], maxQ])

            tmp_wks_name = CreateWorkspace(DataX = _q_axis,
                                           DataY = _y_axis,
                                           DataE = _e_axis,
                                           Nspec = 1,
                                           UnitX = "Wavelength",
                                           OutputWorkspace = tmp_wks_name)
            tmp_wks_name.setDistribution(True)

        # rebin everyting using the same Q binning parameters  
        binQ = float(self.ui.qStep.text())
        bin_parameters = str(minQ) + ',-' + str(binQ) + ',' + str(maxQ)
        for i in range(nbrRow):  

            tmp_wks_name = 'wks_' + str(i)
            ConvertToHistogram(InputWorkspace = tmp_wks_name,
                               OutputWorkspace = tmp_wks_name)

            Rebin(InputWorkspace = tmp_wks_name, 
                  Params = bin_parameters,
                  OutputWorkspace = tmp_wks_name)

        # we use the first histo as output reference
        data_y = mtd['wks_0'].dataY(0).copy()
        data_e = mtd['wks_0'].dataE(0).copy()

        skip_index = 0
        point_to_skip = 1

        isUsingLessErrorValue = self.ui.usingLessErrorValueFlag.isChecked()

        for k in range(1, nbrRow):

            skip_point = True
            can_skip_last_point = False

            data_y_k = mtd['wks_' + str(k)].dataY(0)
            data_e_k = mtd['wks_' + str(k)].dataE(0)
            for j in range(len(data_y_k)-1):

                if data_y_k[j] > 0:

                    can_skip_last_point = True
                    if skip_point:
                        skip_index += 1
                        if skip_index == point_to_skip:
                            skip_point = False
                            skip_index = 0
                        else:
                            continue

                if can_skip_last_point and (data_y_k[j+1] == 0):
                    break

                if data_y[j] > 0 and data_y_k[j] > 0:

                    if isUsingLessErrorValue:
                        if (data_e[j] > data_e_k[j]):
                            data_y[j] = data_y_k[j]
                            data_e[j] = data_e_k[j]

                    else:
                        [data_y[j], data_e[j]] = utilities.weighted_mean([data_y[j], data_y_k[j]],
                                                                         [data_e[j], data_e_k[j]])

                elif (data_y[j] == 0) and (data_y_k[j]>0):
                    data_y[j] = data_y_k[j]
                    data_e[j] = data_e_k[j]

        data_x = mtd['wks_1'].dataX(0)

        return [data_x, data_y, data_e]

    def clear_reductionTable(self):
        '''
        full clear of reductionTable and bigTableData
        '''
        self.bigTableData = empty((20,3), dtype=object)
        self.ui.reductionTable.clearContents()
        nbrRow = self.ui.reductionTable.rowCount()
        if nbrRow > 0:
            for _row in range(nbrRow):
                self.ui.reductionTable.removeRow(0)
        self.clear_plot_overview_REFL(True)

        # clear metadata fields
        cls = 'N/A'
        self.ui.metadataProtonChargeValue.setText(cls)
        self.ui.metadataLambdaRequestedValue.setText(cls)
        self.ui.metadatathiValue.setText(cls)
        self.ui.metadatatthdValue.setText(cls)
        self.ui.metadataS1WValue.setText(cls)
        self.ui.metadataS2WValue.setText(cls)
        self.ui.metadataS1HValue.setText(cls)
        self.ui.metadataS2HValue.setText(cls)

        # switch to first tab
        self.ui.dataNormTabWidget.setCurrentIndex(0)  
	self.fileHasBeenModified()

    def data_stitching_is_auto(self):
        self.data_stitching_mode('auto')

    def data_stitching_is_manual(self):
        self.data_stitching_mode('manual')

    def data_stitching_is_1(self):
        self.data_stitching_mode('1')

    def manual_entry_of_sf_table(self):
        bigTableData = self.bigTableData

        # switch to manual option
        self.ui.manualSF.setChecked(True)
        self.ui.autoSF.setChecked(False)
        self.ui.oneSF.setChecked(False)

        # save all manual parameters
        nbr_row = self.ui.dataStitchingTable.rowCount()
        for i in range(nbr_row):
            _data = bigTableData[i,2]

            _sf_manual = self.ui.dataStitchingTable.cellWidget(i,2).value()
            _data.sf_manual = _sf_manual

            bigTableData[i,2] = _data

        self.data_stitching_mode('manual')


    def data_stitching_mode(self, type):
        '''
        auto, manual or 1
        '''
        # recovering data
        bigTableData = self.bigTableData
        nbr_row = self.ui.dataStitchingTable.rowCount()

        _data = bigTableData[0,0]
        if _data is None:
            return

        _data = bigTableData[0,2]
        if _data.q_axis_for_display == []:
            return

        if type == "auto":
            for i in range(nbr_row):
                _data = bigTableData[i,2]
                _data.sf = _data.sf_auto
                bigTableData[i,2] = _data

        elif type == "manual":
            # recover manual input 
            for i in range(nbr_row):
                _data = bigTableData[i,2]
                _data.sf = _data.sf_manual
                bigTableData[i,2] = _data

        else: # no scaling apply, just plot data
            for i in range(nbr_row):
                _data = bigTableData[i,2]
                _data.sf = 1
                bigTableData[i,2] = _data

        self.bigTableData = bigTableData
        self.plot_stitched_scaled_data()

    def plot_stitched_scaled_data(self):

        bigTableData = self.bigTableData
        nbr_row = self.ui.reductionTable.rowCount()

        _colors = colors.COLOR_LIST
        _colors.append(_colors)

        self.ui.data_stitching_plot.clear()
        self.ui.data_stitching_plot.draw()

        _data0 = bigTableData[0,0]
        _isxlog = _data0.active_data.all_plot_axis.is_reduced_plot_stitching_tab_xlog
        _isylog = _data0.active_data.all_plot_axis.is_reduced_plot_stitching_tab_ylog
        [xmin,xmax,ymin,ymax] = _data0.active_data.all_plot_axis.reduced_plot_stitching_tab_view_interval

        for i in range(nbr_row):

            _data = bigTableData[i,2]
            _q_axis = _data.q_axis_for_display
            _y_axis = _data.y_axis_for_display
            _e_axis = _data.e_axis_for_display

            sf = _data.sf

            _y_axis = _y_axis * sf
            _e_axis = _e_axis * sf

            self.ui.data_stitching_plot.errorbar(_q_axis, _y_axis, yerr=_e_axis, color=_colors[i])
            self.ui.data_stitching_plot.draw()

        self.ui.data_stitching_plot.set_xlabel(u'Q (1/Angstroms)')
        self.ui.data_stitching_plot.set_ylabel(u'R')
        if _isxlog:
            self.ui.data_stitching_plot.set_xscale('log')
        else:
            self.ui.data_stitching_plot.set_xscale('linear')
        if _isylog:
            self.ui.data_stitching_plot.set_yscale('log')
        else:
            self.ui.data_stitching_plot.set_yscale('linear')
        self.ui.data_stitching_plot.canvas.ax.set_xlim([xmin, xmax])
        self.ui.data_stitching_plot.canvas.ax.set_ylim([ymin, ymax])
        self.ui.data_stitching_plot.draw()

    def update_stitchingTable(self):
        '''
        will refresh the table in the stitching table
        '''
        bigTableData = self.bigTableData
        nbr_row = self.ui.reductionTable.rowCount()

        for i in range(nbr_row):

            _data = bigTableData[i,2]

            self.ui.dataStitchingTable.insertRow(i)

            _run_number = self.ui.reductionTable.item(i,0).text()
            _run_number_item = QtGui.QTableWidgetItem(_run_number)
            _run_number_item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
            self.ui.dataStitchingTable.setItem(i,0,_run_number_item)

            _brush = QtGui.QBrush()
            if strtobool(_data.sf_auto_found_match):
                _brush.setColor(QtCore.Qt.green)
            else:
                _brush.setColor(QtCore.Qt.red)

            str_sf_auto = "%.2f" % _data.sf_auto
            _item_auto = QtGui.QTableWidgetItem(str_sf_auto)
            _item_auto.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
            _item_auto.setForeground(_brush)
            self.ui.dataStitchingTable.setItem(i,1,_item_auto)

            _widget_manual = QtGui.QDoubleSpinBox()
            _widget_manual.setMinimum(0)
            _widget_manual.setValue(_data.sf_manual)
            _widget_manual.setSingleStep(0.01)
            _widget_manual.valueChanged.connect(self.manual_entry_of_sf_table)
            self.ui.dataStitchingTable.setCellWidget(i,2,_widget_manual)

            _item_1 = QtGui.QTableWidgetItem(str(1))
            _item_1.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
            self.ui.dataStitchingTable.setItem(i,3,_item_1)


    def update_reductionTable(self):
        '''
        will refresh the content of the reductionTable (lambda, Q ranges...)
        '''
        bigTableData = self.bigTableData
        nbr_row = self.ui.reductionTable.rowCount()

        for i in range(nbr_row):
            _data = bigTableData[i,0]
            _active_data = _data.active_data
            lambda_range = _active_data.lambda_range
            q_range = _active_data.q_range
            incident_angle = _active_data.incident_angle

            lambda_min = lambda_range[0]
            lambda_max = lambda_range[1]
            q_min = q_range[0]
            q_max = q_range[1]

            _item = QtGui.QTableWidgetItem(str(lambda_min))
            self.ui.reductionTable.setItem(i,2,_item)
            _item = QtGui.QTableWidgetItem(str(lambda_max))
            self.ui.reductionTable.setItem(i,3,_item)

            _item = QtGui.QTableWidgetItem(str(q_min))
            self.ui.reductionTable.setItem(i,4,_item)
            _item = QtGui.QTableWidgetItem(str(q_max))
            self.ui.reductionTable.setItem(i,5,_item)

            _item = QtGui.QTableWidgetItem(str(incident_angle))
            self.ui.reductionTable.setItem(i,1,_item)

    def addItemToBigTable(self, value, row, column, editableFlag=False, isCheckOk=False, isOk=False):
        '''
        Add element by element in the BigTable
        '''
        _item = QtGui.QTableWidgetItem(str(value))
	_brush = QtGui.QBrush()
	if isCheckOk:
	    if isOk:
		_brush.setColor(colors.VALUE_OK)
	    else:
		_brush.setColor(colors.VALUE_BAD)
	    _item.setForeground(_brush)
        if not editableFlag:
            _item.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)

        self.ui.reductionTable.setItem(row, column, _item)

    def load_reduced_ascii(self):

    #  try:
        _path = self.path_config
        filename = QtGui.QFileDialog.getOpenFileName(self,'Open Reduced Data Set', _path)      
        if not(filename == ""):
            self.path_config = os.path.dirname(filename)

            loadedAscii = reducedAsciiLoader(self, filename)
            if self.stitchingAsciiWidgetObject is None:
                self.stitchingAsciiWidgetObject = stitchingAsciiWidgetObject(self, loadedAscii)
            else:
                self.stitchingAsciiWidgetObject.addData(loadedAscii)

            bigTableData= self.bigTableData
            data0 = bigTableData[0,0]
            data0_active_data = data0.active_data
            _isylog = data0_active_data.all_plot_axis.is_reduced_plot_stitching_tab_ylog
            _isxlog = data0_active_data.all_plot_axis.is_reduced_plot_stitching_tab_xlog
            self.stitchingAsciiWidgetObject.updateDisplay(isylog=_isylog, isxlog=_isxlog)

        # except:
            # warning('Could not open ASCII file!')

    def getNodeValue(self,node,flag):
        '''
        get the value of the node from the dom (config file)
        '''
        try:
            _tmp = node.getElementsByTagName(flag)
            _value = _tmp[0].childNodes[0].nodeValue
        except:
            _value = ''
        return _value

    @log_call
    def helpDialog(self):
        '''
        Open a HTML page with the program documentation and place it on the right
        side of the current screen.
        '''
        if instrument.NAME == "REF_L": #TODO HARDCODED INSTRUMENT
            return

        dia=QtGui.QDialog(self)
        dia.setWindowTitle(u'QuickNXS Manual')
        verticalLayout=QtGui.QVBoxLayout(dia)
        dia.setLayout(verticalLayout)
        webview=QtWebKit.QWebView(dia)
        webview.load(QtCore.QUrl.fromLocalFile(paths.DOC_INDEX))
        verticalLayout.addWidget(webview)
        # set width of the page to fit the document and height to the same as the main window
        dia.resize(700, self.height())
        pos=-700
        dw=QtGui.QDesktopWidget()
        for i in range(dw.screenCount()):
            pos+=dw.screenGeometry(i).width()
            if pos>self.pos().x():
                break
        dia.move(pos, dia.pos().y())
        dia.show()

    def aboutDialog(self):
        from numpy.version import version as npversion
        from matplotlib import __version__ as mplversion
        from h5py.version import version as h5pyversion
        from h5py.version import hdf5_version as hdf5version
        from version import str_version
        try:
            from PyQt4.pyqtconfig import Configuration
            pyqtversion=Configuration().pyqt_version_str
        except ImportError:
            pyqtversion='Unknown'

        if instrument.NAME == 'REF_M': #TODO HARDCODED INSTRUMENT
            QtGui.QMessageBox.about(self, 'About QuickNXS',
                                    '''
  QuickNXS - SNS Magnetism Reflectometer data reduction program
    Version %s on Python %s

  Library Versions:
    Numpy %s
    Matplotlib %s
    Qt %s
    PyQt4 %s
    H5py %s
    HDF5 %s
  '''%(str_version, sys.version, npversion, mplversion,
       QtCore.QT_VERSION_STR, pyqtversion, h5pyversion, hdf5version))
        else:
            QtGui.QMessageBox.about(self, 'About QuickNXS',
                                    '''
  QuickNXS - SNS Liquids Reflectometer data reduction program
    Version %s on Python %s

  Library Versions:
    Numpy %s
    Matplotlib %s
    Qt %s
    PyQt4 %s
    H5py %s
    HDF5 %s
  '''%(str_version, sys.version, npversion, mplversion,
       QtCore.QT_VERSION_STR, pyqtversion, h5pyversion, hdf5version))