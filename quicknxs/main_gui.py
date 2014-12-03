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
from .version import str_version
from logging import info, warning, debug
from reduction import REFLReduction
from utilities import convert_angle
import utilities
import constants
import colors
from calculate_SF import CalculateSF
from reduced_ascii_loader import reducedAsciiLoader
from stitching_ascii_widget import stitchingAsciiWidgetObject
from peakfinder import PeakFinder
from reduced_config_files_handler import ReducedConfigFilesHandler
from init_file_menu import InitFileMenu
from refl_gui_utils import PlotDialogREFL


from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
#from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg
from matplotlib.figure import Figure


class gisansCalcThread(QtCore.QThread):
  '''
  Perform GISANS scattering calculations in the background.
  '''
  updateProgress=QtCore.pyqtSignal(float)
  gisans=None

  def __init__(self, dataset, options):
    QtCore.QThread.__init__(self)
    self.dataset=dataset
    self.options=options

  def run(self):
    gisans=[]
    for i, dataset in enumerate(self.dataset):
      gisans.append(GISANS(dataset, **self.options))
      self.updateProgress.emit(float(i+1)/len(self.dataset))
    self.gisans=gisans            
            
class MainGUI(QtGui.QMainWindow):
  '''
  The program top level window with all direct event handling.
  '''
  active_folder=instrument.data_base
  active_file=u''
  last_mtime=0. #: Stores the last time the current file has been modified
  _active_data=None
  
  #bigTableData = [] # Will store all the data objects indexes just like the BigTable
  
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

  # current TOF status
  _auto_tof_flag = True
  _ms_tof_flag = True
  
  # live selection of peak, back and low_res
  _live_selection = None # 'peak_min','peak_max','back_min','back_max','lowres_min','lowres_max'
  
  # to skip data_norm_tab_changed when user clicked table
  userClickedInTable = False

  # log/linear status of yi_plot
  isLog = False

  stitchingAsciiWidgetObject = None
  reducedFilesLoadedObject = None
  listAction = [] # in Menu File
  fileMenuObject = None

  # for double click of yi plot
  timeClick1 = -1
  DOUBLE_CLICK_IF_WITHIN_TIME = 0.4  #s


  ##### for IPython mode, keep namespace up to date ######
  @property
  def active_data(self): return self._active_data
  @active_data.setter
  def active_data(self, value):
    if self.ipython:
      self.ipython.namespace['data']=value
    self._active_data=value
  @property
  def refl(self): return self._refl
  @refl.setter
  def refl(self, value):
    if self.ipython:
      self.ipython.namespace['refl']=value
    self._refl=value
  ##### for IPython mode, keep namespace up to date ######

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
    if instrument.NAME == 'REF_M':
      exec 'from .default_interface import Ui_MainWindow'
    else:
      exec 'from .default_interface_refl import Ui_MainWindow'
        
    self.ui=Ui_MainWindow()
    self.ui.setupUi(self)
    install_gui_handler(self)
    if instrument.NAME == 'REF_L':
      window_title = 'QuickNXS for REF_L'
    else:
      window_title = 'QuickNXS'
    self.setWindowTitle(u'%s   %s'%(window_title,str_version))
    self.cache_indicator=QtGui.QLabel("Cache Size: 0.0MB")
    self.ui.statusbar.addPermanentWidget(self.cache_indicator)
    button=QtGui.QPushButton('Empty Cache')
    self.ui.statusbar.addPermanentWidget(button)
    button.pressed.connect(self.empty_cache)
    button.setFlat(True)
    button.setMaximumSize(150, 20)

    if instrument.NAME=="REF_M":
      # hide radio buttons
      for i in range(1, 12):
        getattr(self.ui, 'selectedChannel%i'%i).hide()

    self.eventProgress=QtGui.QProgressBar(self.ui.statusbar)
    self.eventProgress.setMinimumSize(20, 14)
    self.eventProgress.setMaximumSize(140, 100)
    self.ui.statusbar.addPermanentWidget(self.eventProgress)

    if instrument.NAME=="REF_M":
      self.toggleHide()      
    
    if instrument.NAME=="REF_L":
      #set up the header of the big table
      verticalHeader = ["Data Run #",u'2\u03b8 (\u00B0)',u'\u03bbmin(\u00c5)',
                        u'\u03bbmax (\u00c5)',u'Qmin (1/\u00c5)',u'Qmax (1/\u00c5)',
                        'Norm. Run #']
      self.ui.reductionTable.setHorizontalHeaderLabels(verticalHeader)
      self.ui.reductionTable.resizeColumnsToContents()
      # define the context menu of the recap table
      self.ui.reductionTable.horizontalHeader().setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
      self.ui.reductionTable.horizontalHeader().customContextMenuRequested.connect(self.handleReductionTableMenu)

      # set up the header of the scaling factor table
      verticalHeader = ["Data Run #","SF: auto","SF: manual","SF: 1"]
      self.ui.dataStitchingTable.setHorizontalHeaderLabels(verticalHeader)
      self.ui.dataStitchingTable.resizeColumnsToContents()
      
      palette_green = QtGui.QPalette()
      palette_green.setColor(QtGui.QPalette.Foreground, QtCore.Qt.green)
      self.ui.sf_found_label.setPalette(palette_green)
      
      palette_red = QtGui.QPalette()
      palette_red.setColor(QtGui.QPalette.Foreground, QtCore.Qt.red)
      self.ui.sf_not_found_label.setPalette(palette_red)

      # set up header for reduced ascii table
      verticalHeader = ["ASCII files", "Active"]
      self.ui.reducedAsciiDataSetTable.setHorizontalHeaderLabels(verticalHeader)
      self.ui.reducedAsciiDataSetTable.setColumnWidth(0,249)
      self.ui.reducedAsciiDataSetTable.setColumnWidth(1,49)

    self.ui.plotTab.setCurrentIndex(0)
    # start a separate thread for delayed actions
    self.trigger=DelayedTrigger()
    self.trigger.activate.connect(self.processDelayedTrigger)
    self.trigger.start()
    if instrument.NAME == "REF_M":
      self.ui.bgCenter.setValue((DETECTOR_X_REGION[0]+100.)/2.)
      self.ui.bgWidth.setValue((100-DETECTOR_X_REGION[0]))
      self.connect_plot_events()
    else:
      self.connect_plot_events_refl()

    self.ui.data_yi_plot.canvas.trigger.connect(self.double_click_yi_plot)
      
    self._path_watcher=QtCore.QFileSystemWatcher([self.active_folder], self)
    self._path_watcher.directoryChanged.connect(self.folderModified)

    # watch folder for changes
    self.auto_change_active=False

    self.fileLoaded.connect(self.updateLabels)
#    self.fileLoaded.connect(self.calcReflParams) #REMOVEME
    self.fileLoaded.connect(self.plotActiveTab)
    self.initiateProjectionPlot.connect(self.plot_projections)
    self.initiateReflectivityPlot.connect(self.plot_refl)
    self.initiateReflectivityPlot.connect(self.updateStateFile)
    self.folderModified()

    if instrument.NAME=="REF_L":
      self.defineRightDefaultPath()
      self.fileMenuObject = InitFileMenu(self)
      self.reducedFilesLoadedObject = ReducedConfigFilesHandler(self)
      self.initConfigGui()
      
    # open file after GUI is shown
    if '-ipython' in argv:
      self.run_ipython()
    else:
      self.ipython=None
    if len(argv)>0:
      if sys.version_info[0]<3:
        # if non ascii character in filenames interprete it as utf8
        argv=[unicode(argi, 'utf8', 'ignore') for argi in argv]
      # delay action to be run within event loop, this allows the error handling to work
      if argv[0][-4:]=='.dat':
        self.trigger('loadExtraction', argv[0])
      elif len(argv)==1:
        if argv[0][-4:]=='.nxs':
          self.trigger('fileOpen', argv[0])
        else:
          self.trigger('openByNumber', argv[0])
      else:
        self.trigger('automaticExtraction', argv)
    else:
      self.ui.numberSearchEntry.setFocus()

  
  def initConfigGui(self):
    from quicknxs.config import refllastloadedfiles
    refllastloadedfiles.switch_config('config_files')
    if refllastloadedfiles.config_files_path != '':
      self.path_config =  refllastloadedfiles.config_files_path
    

  def defineRightDefaultPath(self):
    
    import socket
    if socket.gethostname() == 'lrac.sns.gov':
      self.path_config = '/SNS/REF_L/'
      self.path_ascii = '/SNS/REF_L'

  def logtoggle(self, checked):
    self.isLog = checked
    self.plot_overview_REFL(plot_yt=True, plot_yi=True, plot_it=True, plot_ix=True)

  def double_click_yi_plot(self):
    '''
    This function is reached when the user click the yi plot (data and normalization)
    '''
    if self.timeClick1 == -1:
      self.timeClick1 = time.time()
      return
    else:
      _timeClick2 = time.time()

    if (_timeClick2 - self.timeClick1) <= self.DOUBLE_CLICK_IF_WITHIN_TIME:
      data = self.active_data
      yaxis = data.ycountsdata
      peak = data.peak
      back = data.back
      new_detector_geometry_flag = data.new_detector_geometry_flag
      dialog_refl = PlotDialogREFL(yaxis, peak, back, new_detector_geometry_flag)
      dialog_refl.show()
      
    self.timeClick1 = -1
  
  def handleReductionTableMenu(self, pos):
    '''
    Context menu of the Reduction table
    '''
    menu = QtGui.QMenu()
    menu.addAction('Delete Row')
    menu.addAction('Delete Data')
    menu.addAction('Delete Normalization')
#    menu.exec_(self.mapToGlobal(pos))
    
  def run_ipython(self):
    '''
      Startup the IPython console within the program.
    '''
    info('Start IPython console')
    from .ipython_widget import IPythonConsoleQtWidget
    self.ipython=IPythonConsoleQtWidget(self)
    self.ui.plotTab.addTab(self.ipython, 'IPython')
    self.ipython.namespace['data']=self.active_data
    # exceptions within GUI thread, must be installed by method within that process
    self.trigger('_install_exc')


  #def saveListPrevLoadedFiles(self):
    
    #from quicknxs.config import refllastloadedfiles
    #refllastloadedfiles.switch_config('config_files')
    #refllastloadedfiles.reduce1 = '/SNS/REF_L/shared/0/IPTS_e5454/dfdfdf.txt'
    

  #def  loadListPrevLoadedFiles(self):
    #'''
    #will update the gui with the previous files (config, reduced) loaded
    #'''
    #from quicknxs.config import refllastloadedfiles
    #refllastloadedfiles.switch_config('config_files')
    #file1 = refllastloadedfiles.reduce1
    #if file1 is not '':
      #self.ui.menuFile.addSeparator()
      #file1Action = QtGui.QAction(file1, self)
      #file1Action.triggered.connect(self.loadConfigFile1)
      #self.ui.menuFile.addAction(file1Action)
      
    #file2 = refllastloadedfiles.reduce2
    #file3 = refllastloadedfiles.reduce3
    #file4 = refllastloadedfiles.reduce4
    #file5 = refllastloadedfiles.reduce5
    
    #refllastloadedfiles.switch_config('default')

  #def addConfigFileLoaded(self, fullFileName):
    
    #from quicknxs.config import refllastloadedfiles
    #refllastloadedfiles.switch_config('config_files')
    #file1 = refllastloadedfiles.reduce1
    


  #def loadConfigFile1(self):
    #print 'in loadConfigFile1'


  def launch_config_file1(self):
    self.launch_config_file_nbr(0)
  def launch_config_file2(self):
    self.launch_config_file_nbr(1)
  def launch_config_file3(self):
    self.launch_config_file_nbr(2)
  def launch_config_file4(self):
    self.launch_config_file_nbr(3)
  def launch_config_file5(self):
    self.launch_config_file_nbr(4)

  def launch_config_file_nbr(self, index):
    _configObject = self.reducedFilesLoadedObject
    _filename = _configObject.configFiles[index].fullFileName
    _configObject.configFiles[index].setNewTime()
    self.reducedFilesLoadedObject = _configObject
    self.loading_configuration_file(_filename)
    self.fileMenuObject.activate_file_at_index(index)

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

  def connect_plot_events(self):
    '''
    Connect matplotlib mouse events.
    '''
    for plot in [self.ui.xy_pp, self.ui.xy_mp, self.ui.xy_pm, self.ui.xy_mm,
                 self.ui.xtof_pp, self.ui.xtof_mp, self.ui.xtof_pm, self.ui.xtof_mm,
                 self.ui.xy_overview, self.ui.xtof_overview,
                 self.ui.x_project, self.ui.y_project, self.ui.refl]:
      plot.canvas.mpl_connect('motion_notify_event', self.plotMouseEvent)
    for plot in [self.ui.xy_pp, self.ui.xy_mp, self.ui.xy_pm, self.ui.xy_mm,
                 self.ui.xtof_pp, self.ui.xtof_mp, self.ui.xtof_pm, self.ui.xtof_mm,
                 self.ui.xy_overview, self.ui.xtof_overview]:
      plot.canvas.mpl_connect('scroll_event', self.changeColorScale)

    self.ui.x_project.canvas.mpl_connect('motion_notify_event', self.plotPickX)
    self.ui.x_project.canvas.mpl_connect('button_press_event', self.plotPickX)
    self.ui.x_project.canvas.mpl_connect('button_release_event', self.plotRelese)
    self.ui.y_project.canvas.mpl_connect('motion_notify_event', self.plotPickY)
    self.ui.y_project.canvas.mpl_connect('button_press_event', self.plotPickY)
    self.ui.y_project.canvas.mpl_connect('button_release_event', self.plotRelese)
    self.ui.refl.canvas.mpl_connect('scroll_event', self.scaleOnPlot)
    self.ui.xy_overview.canvas.mpl_connect('button_press_event', self.plotPickXY)
    self.ui.xy_overview.canvas.mpl_connect('motion_notify_event', self.plotPickXY)
    self.ui.xy_overview.canvas.mpl_connect('button_release_event', self.plotRelese)
    self.ui.xtof_overview.canvas.mpl_connect('button_press_event', self.plotPickXToF)
    self.ui.xtof_overview.canvas.mpl_connect('motion_notify_event', self.plotPickXToF)
    self.ui.xtof_overview.canvas.mpl_connect('button_release_event', self.plotRelese)

  def connect_plot_events_refl(self):
    '''
    Connect matplotlib mouse events.
    '''
    for plot in [self.ui.data_yt_plot, 
#                 self.ui.data_yi_plot,
                 self.ui.data_it_plot,
                 self.ui.data_ix_plot,
                 self.ui.norm_yt_plot, 
#                 self.ui.norm_yi_plot,
                 self.ui.norm_it_plot,
                 self.ui.norm_ix_plot]:
      plot.canvas.mpl_connect('motion_notify_event', self.plotMouseEvent)
    
    for plot in [self.ui.data_yt_plot, 
#                 self.ui.data_yi_plot,
                 self.ui.data_it_plot,
                 self.ui.data_ix_plot,
                 self.ui.norm_yt_plot, 
#                 self.ui.norm_yi_plot,
                 self.ui.norm_it_plot,
                 self.ui.norm_ix_plot]:
      plot.canvas.mpl_connect('scroll_event', self.changeColorScale)

    self.ui.norm_yt_plot.canvas.mpl_connect('motion_notify_event', self.mouseNormPlotyt)
    self.ui.norm_yt_plot.canvas.mpl_connect('button_press_event', self.mouseNormPlotyt)
    self.ui.norm_yt_plot.canvas.mpl_connect('button_release_event', self.mouseNormPlotyt)

#    self.ui.data_yt_plot.canvas.mpl_connect('motion_notify_event', self.plotPickyt)

    #self.ui.x_project.canvas.mpl_connect('motion_notify_event', self.plotPickX)
    #self.ui.x_project.canvas.mpl_connect('button_press_event', self.plotPickX)
    #self.ui.x_project.canvas.mpl_connect('button_release_event', self.plotRelese)
    #self.ui.y_project.canvas.mpl_connect('motion_notify_event', self.plotPickY)
    #self.ui.y_project.canvas.mpl_connect('button_press_event', self.plotPickY)
    #self.ui.y_project.canvas.mpl_connect('button_release_event', self.plotRelese)
    #self.ui.refl.canvas.mpl_connect('scroll_event', self.scaleOnPlot)
    #self.ui.xy_overview.canvas.mpl_connect('button_press_event', self.plotPickXY)
    #self.ui.xy_overview.canvas.mpl_connect('motion_notify_event', self.plotPickXY)
    #self.ui.xy_overview.canvas.mpl_connect('button_release_event', self.plotRelese)
    #self.ui.xtof_overview.canvas.mpl_connect('button_press_event', self.plotPickXToF)
    #self.ui.xtof_overview.canvas.mpl_connect('motion_notify_event', self.plotPickXToF)
    #self.ui.xtof_overview.canvas.mpl_connect('button_release_event', self.plotRelese)


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
    
    if instrument.NAME=='REF_M':
      if base.endswith('event.nxs'):
        tottime=time_from_header(os.path.join(folder, base))
        self.ui.eventTotalTimeLabel.setText(u"(%i min)"%(tottime/60))
      if base.endswith('event.nxs') and self.ui.eventSplit.isChecked():
        event_split_bins=self.ui.eventSplitItems.value()
        event_split_index=self.ui.eventSplitIndex.value()-1
      else:
        event_split_bins=None
        event_split_index=0
      bin_type=self.ui.eventBinMode.currentIndex()

    else: #REF_L
      event_split_bins=None
      event_split_index=0      
      bin_type=0

    # we want to add those runs to selected data/norm cell runs
      if do_add:

        # get list of previously loaded runs
        [r,c] = self.getCurrentRowColumnSelected()
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
    
      if instrument.NAME == 'REF_M':
        self._fileOpenDone(data, filename, do_plot)

      else:
        if data is not None:
          # save the data in the right spot (row, column)
          if do_add:
            [r,c] = self.getCurrentRowColumnSelected()
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
    '''
    plot the REFL data
    '''
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
      [r,c] = self.getCurrentRowColumnSelected()
      data = self.bigTableData[r,c]
      if data is None:
        status = False
      else:
        status = True

    if isData:
      self.ui.tab.setEnabled(status)
    else:
      self.ui.tab_2.setEnabled(status)
          
  def getRowColumnNextDataSet(self):
    '''
    this routine will determine where the data set, just loaded
    will be saved in the 2D data set array
    '''
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
 
  def reduction_table_cell_double_clicked(self, row, column):

    if column == 0 or column == 6:
      # we are now editing the cell if column is 0 or 6
      self.editing_flag = True

  @waiting_effects
  def reductionTable_manual_entry(self, item):
    '''
    user manually modified data or norm run number in the reductionTable
    '''

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
    
    # keep going only for data and norm columns
    if (column != 0) and (column != 6):
      return
    
    # check if only 1 run number, or more
    str_split = cell_content.split(',')
    if len(str_split) == 1:
      # load object
      info('Trying to locate file number %s...'% cell_content)
      fullFileName = FileFinder.findRuns("REF_L_%d" % int(cell_content))[0]
    else:
      fullFileName = []
      for _run in str_split:
        _fullFileName = FileFinder.findRuns("REF_L_%d" % int(_run))[0]
        fullFileName.append(_fullFileName)
    
    data = NXSData(fullFileName,
                   bin_type = 0,
                   bins = self.ui.eventTofBins.value(),
                   callback = self.updateEventReadout,
                   event_split_bins = None,
                   event_split_index = 0,
                   angle_offset = self.ui.angleOffsetValue.text(),
                   isData = isData)
    
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
    

  def remove_row_reductionTable(self):
    nbrRow = self.ui.reductionTable.rowCount()
    if nbrRow == 0:
      return
    
    # remove row from table
    [row,col] = self.getCurrentRowColumnSelected()
    self.ui.reductionTable.removeRow(row)

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

  def reduction_table_cell_modified(self, item):
    
    if self.editing_flag:
      self.reductionTable_manual_entry(item)
 
 
  def populateReflectivityTable(self, data):
    # will populate the recap table
    
    _selected_row = self.ui.reductionTable.selectedRanges()
    
    # are we replacing or adding a new entry
    do_add = False
    #if self.ui.addRunNumbers.isEnabled() and self.ui.addRunNumbers.isChecked():
      #do_add = True
      
    if do_add:
      [r,c] = self.getCurrentRowColumnSelected()

      if c !=0:
        _column = 6
      else:
        _column = 0

      _row = r

      _item = QtGui.QTableWidgetItem(data.active_data.run_number)
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
    if instrument.NAME == 'REF_L':
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
    if instrument.NAME == "REF_M":
      self.plot_overview_REFM()
    else:
      self.plot_overview_REFL()

  def clear_plot_overview_REFL(self, isData):
    if isData:
      self.ui.data_yt_plot.clear()
      self.ui.data_yt_plot.draw()
      self.ui.data_yi_plot.clear()
      self.ui.data_yi_plot.draw()
      self.ui.data_it_plot.clear()
      self.ui.data_it_plot.draw()
      self.ui.data_ix_plot.clear()
      self.ui.data_ix_plot.draw()
    else:
      self.ui.norm_yt_plot.clear()
      self.ui.norm_yt_plot.draw()
      self.ui.norm_yi_plot.clear()
      self.ui.norm_yi_plot.draw()
      self.ui.norm_it_plot.clear()
      self.ui.norm_it_plot.draw()
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
    self.clear_plot_overview_REFL(isDataSelected)

    data = self.active_data
    if data is None:
      return

    filename = data.filename

    if self.ui.dataTOFmanualMode.isChecked(): # manual mode
      tof_range_auto = data.tof_range
  
    else: # auto mode
      tof_range_auto = data.tof_range_auto
      
    #tof_edges_full = data.tof_edges_full
    tof_axis = data.tof_axis_auto_with_margin
    
    xy = data.xydata
    ytof = data.ytofdata
    countstofdata = data.countstofdata
    countsxdata = data.countsxdata
    ycountsdata = data.ycountsdata
    
    [peak1, peak2] = data.peak
    [back1, back2] = data.back
    [lowRes1, lowRes2] = data.low_res
    back_flag = data.back_flag
    low_res_flag = data.low_res_flag
    
    if isDataSelected: # data

      self.ui.dataNameOfFile.setText('%s'%filename)

      # repopulate the tab
#      [peak1, peak2] = data.data_peak
      peak1 = int(peak1)
      peak2 = int(peak2)
      peak_min = min([peak1, peak2])
      peak_max = max([peak1, peak2])
      self.ui.dataPeakFromValue.setValue(peak_min)
      self.ui.dataPeakToValue.setValue(peak_max)

#      [back1, back2] = data.data_back
      back1 = int(back1)
      back2 = int(back2)
      back_min = min([back1, back2])
      back_max = max([back1, back2])
      self.ui.dataBackFromValue.setValue(back_min)
      self.ui.dataBackToValue.setValue(back_max)

#      [lowRes1, lowRes2] = data.data_low_res
      lowRes1 = int(lowRes1)
      lowRes2 = int(lowRes2)
      lowRes_min = min([lowRes1, lowRes2])
      lowRes_max = max([lowRes1, lowRes2])
      self.ui.dataLowResFromValue.setValue(lowRes_min)
      self.ui.dataLowResToValue.setValue(lowRes_max)
#      back_flag = data.data_back_flag
      self.ui.dataBackgroundFlag.setChecked(back_flag)

#      data_low_res_flag = data.data_low_res_flag
#      self.ui.dataLowResFlag.setChecked(data_low_res_flag)
      self.ui.dataLowResFlag.setChecked(low_res_flag)
      
      yt_plot = self.ui.data_yt_plot
      yi_plot = self.ui.data_yi_plot
      it_plot = self.ui.data_it_plot
      ix_plot = self.ui.data_ix_plot
    
      # calculate and display Q range if not calculated yet
      [r,c] = self.getCurrentRowColumnSelected()
      _data = self.bigTableData[r,c]
      _active_data = _data.active_data
        
      incident_angle = _active_data.incident_angle
      [qmin,qmax] = _active_data.q_range
      [lmin,lmax] = _active_data.lambda_range
      
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

      [row, column] = self.getCurrentRowColumnSelected()

      self.ui.reductionTable.setItem(row, 4, _item_min)
      self.ui.reductionTable.setItem(row, 5, _item_max)
      self.ui.reductionTable.setItem(row, 2, _item_lmin)
      self.ui.reductionTable.setItem(row, 3, _item_lmax)
      self.ui.reductionTable.setItem(row, 1, _item_incident)

    else: # normalization

      self.ui.normNameOfFile.setText('%s'%filename)

      flag = data.use_it_flag
      self.ui.useNormalizationFlag.setChecked(flag)

#      [peak1,peak2] = data.norm_peak
      peak1 = int(peak1)
      peak2 = int(peak2)
      peak_min = min([peak1, peak2])
      peak_max = max([peak1, peak2])
      self.ui.normPeakFromValue.setValue(peak_min)
      self.ui.normPeakToValue.setValue(peak_max)
      
#      [back1, back2] = data.norm_back
      back1 = int(back1)
      back2 = int(back2)
      back_min = min([back1, back2])
      back_max = max([back1, back2])
      self.ui.normBackFromValue.setValue(back_min)
      self.ui.normBackToValue.setValue(back_max)

#      [lowRes1, lowRes2] = data.norm_low_res
      lowRes1 = int(lowRes1)
      lowRes2 = int(lowRes2)
      lowRes_min = min([lowRes1, lowRes2])
      lowRes_max = max([lowRes1, lowRes2])
      self.ui.normLowResFromValue.setValue(lowRes_min)
      self.ui.normLowResToValue.setValue(lowRes_max)

#      norm_low_res_flag = data.norm_low_res_flag
#      self.ui.normLowResFlag.setChecked(norm_low_res_flag)
      self.ui.normLowResFlag.setChecked(low_res_flag)

#      back_flag = data.norm_back_flag
      self.ui.normBackgroundFlag.setChecked(back_flag)
      
      yt_plot = self.ui.norm_yt_plot
#      yi_plot = self.ui.norm_yi_plot
      yi_plot = self.ui.norm_yi_plot
      it_plot = self.ui.norm_it_plot
      ix_plot = self.ui.norm_ix_plot

    if data.new_detector_geometry_flag:
      ylim = 303
      xlim = 255
    else:
      ylim = 255
      xlim = 303

    # display yt
    if plot_yt:
      
      ## code used to debug XY view (new detector position)
      #yt_plot.imshow(xy, aspect='auto', cmap=self.color, origin='lower',
                     #extent=[0,255,0,303])

      yt_plot.imshow(ytof, log=self.ui.logarithmic_colorscale.isChecked(),
                     aspect='auto', cmap=self.color, origin='lower',
                     extent=[tof_axis[0]*1e-3, tof_axis[-1]*1e-3, 0, data.y.shape[0]-1])
      yt_plot.set_xlabel(u't (ms)')
      yt_plot.set_ylabel(u'y (pixel)')
  
      # display tof range in auto/manual TOF range    #FIXME
      autotmin = tof_range_auto[0]
      autotmax = tof_range_auto[1]
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
  
      yt_plot.draw()

    # display it
    if plot_it:

      it_plot.canvas.ax.plot(tof_axis[0:-1]/1000,countstofdata, color='#0000aa')
      it_plot.canvas.ax.set_xlabel(u't (ms)')
#      u'\u03bcs
      it_plot.canvas.ax.set_ylabel(u'Counts')
      autotmin = tof_range_auto[0]
      autotmax = tof_range_auto[1]
      ta = it_plot.canvas.ax.axvline(autotmin/1000, color='#00aa00')
      tb = it_plot.canvas.ax.axvline(autotmax/1000, color='#00aa00')
      it_plot.canvas.draw()

    # display yi
    if plot_yi:
      
      xaxis = range(len(ycountsdata))
      yi_plot.canvas.ax.plot(ycountsdata,xaxis)
      yi_plot.canvas.ax.set_xlabel(u'counts')
      yi_plot.canvas.ax.set_ylabel(u'y (pixel)')
     
      yi_plot.canvas.ax.set_ylim(0,ylim)      
      y1peak = yi_plot.canvas.ax.axhline(peak1, color='#00aa00')
      y2peak = yi_plot.canvas.ax.axhline(peak2, color='#00aa00')
      if back_flag:
        y1back = yi_plot.canvas.ax.axhline(back1, color='#aa0000')
        y2back = yi_plot.canvas.ax.axhline(back2, color='#aa0000')

      if self.isLog:
        yi_plot.canvas.ax.set_xscale('log')
      else:
        yi_plot.canvas.ax.set_xscale('linear')
      
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
        
      ix_plot.canvas.draw()

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
    
    _tmin = 1e-3 * tmin
    _tmax = 1e-3 * tmax

    stmin = str("%.2f" % _tmin)
    stmax = str("%.2f" % _tmax)
    
    self.ui.TOFmanualFromValue.setText(stmin)
    self.ui.TOFmanualToValue.setText(stmax)
    
  @log_call
  def plot_overview_REFM(self):

    data=self.active_data[self.active_channel]
    xy=data.xydata
    xtof=data.xtofdata
    ref_norm=self.getNorm()
    if self.ui.normalizeXTof.isChecked() and ref_norm is not None:
      ref_norm=ref_norm.Rraw
      # normalize ToF dataset for wavelength distribution
      ref_norm=where(ref_norm>0., ref_norm, 1.)
      xtof=xtof.astype(float)/ref_norm[newaxis, :]
    xy_imin=xy[xy>0].min()
    xy_imax=xy.max()
    tof_imin=xtof[xtof>0].min()
    tof_imax=xtof.max()

    # for lines of the current extraction area
    x_peak=self.ui.refXPos.value()
    x_width=self.ui.refXWidth.value()
    y_pos=self.ui.refYPos.value()
    y_width=self.ui.refYWidth.value()
    bg_pos=self.ui.bgCenter.value()
    bg_width=self.ui.bgWidth.value()

    # XY plot
    if self.ui.tthPhi.isChecked():
      rad_per_pixel=data.det_size_x/data.dist_sam_det/data.xydata.shape[1]
      phi_range=xy.shape[0]*rad_per_pixel*180./pi
      tth_range=xy.shape[1]*rad_per_pixel*180./pi
      phi0=self.ui.refYPos.value()*rad_per_pixel*180./pi
      tth0=(data.dangle-data.dangle0)-(304-data.dpix)*rad_per_pixel*180./pi
      self.ui.xy_overview.clear()
      if self.overview_lines is None:
        self.overview_lines=[]
      else:
        self.overview_lines=self.overview_lines[-2:]

      self.ui.xy_overview.imshow(xy, log=self.ui.logarithmic_colorscale.isChecked(),
                               aspect='auto', cmap=self.color, origin='lower',
                               extent=[tth_range+tth0, tth0, phi0, phi0-phi_range])
      self.ui.xy_overview.set_xlabel(u'2$\\Theta{}$ [°]')
      self.ui.xy_overview.set_ylabel(u'$\\phi{}$ [°]')
      self.ui.xy_overview.cplot.set_clim([xy_imin, xy_imax])
    else:
      self.ui.xy_overview.imshow(xy, log=self.ui.logarithmic_colorscale.isChecked(),
                               aspect='auto', cmap=self.color, origin='lower')
      self.ui.xy_overview.set_xlabel(u'x [pix]')
      self.ui.xy_overview.set_ylabel(u'y [pix]')
      self.ui.xy_overview.cplot.set_clim([xy_imin, xy_imax])

      if self.overview_lines is None or len(self.overview_lines)==2:
        x1=self.ui.xy_overview.canvas.ax.axvline(x_peak-x_width/2., color='#aa0000')
        x2=self.ui.xy_overview.canvas.ax.axvline(x_peak+x_width/2., color='#aa0000')
        y1=self.ui.xy_overview.canvas.ax.axhline(y_pos-y_width/2., color='#00aa00')
        y2=self.ui.xy_overview.canvas.ax.axhline(y_pos+y_width/2., color='#00aa00')
        if self.overview_lines is not None:
          self.overview_lines=[x1, x2, y1, y2]+self.overview_lines
        else:
          self.overview_lines=[x1, x2, y1, y2]
      else:
        self.overview_lines[0].set_xdata([x_peak-x_width/2., x_peak-x_width/2.])
        self.overview_lines[1].set_xdata([x_peak+x_width/2., x_peak+x_width/2.])
        self.overview_lines[2].set_ydata([y_pos-y_width/2., y_pos-y_width/2.])
        self.overview_lines[3].set_ydata([y_pos+y_width/2., y_pos+y_width/2.])
    # XToF plot
    if self.ui.xLamda.isChecked():
      self.ui.xtof_overview.imshow(xtof[::-1], log=self.ui.logarithmic_colorscale.isChecked(),
                                   aspect='auto', cmap=self.color,
                                   extent=[data.lamda[0], data.lamda[-1], 0, data.x.shape[0]-1])
      self.ui.xtof_overview.set_xlabel(u'$\\lambda{}$ [Å]')
    else:
      self.ui.xtof_overview.imshow(xtof[::-1], log=self.ui.logarithmic_colorscale.isChecked(),
                                   aspect='auto', cmap=self.color,
                                   extent=[data.tof[0]*1e-3, data.tof[-1]*1e-3, 0, data.x.shape[0]-1])
      self.ui.xtof_overview.set_xlabel(u'ToF [ms]')
    self.ui.xtof_overview.set_ylabel(u'x [pix]')
    if len(self.overview_lines) in [0, 4]:
      x3=self.ui.xtof_overview.canvas.ax.axhline(x_peak-x_width/2., color='#aa0000')
      x4=self.ui.xtof_overview.canvas.ax.axhline(x_peak+x_width/2., color='#aa0000')
      x5=self.ui.xtof_overview.canvas.ax.axhline(bg_pos-bg_width/2., color='black')
      x6=self.ui.xtof_overview.canvas.ax.axhline(bg_pos+bg_width/2., color='black')
      self.overview_lines+=[x3, x4, x5, x6]
    else:
      self.overview_lines[-4].set_ydata([x_peak-x_width/2., x_peak-x_width/2.])
      self.overview_lines[-3].set_ydata([x_peak+x_width/2., x_peak+x_width/2.])
      self.overview_lines[-2].set_ydata([bg_pos-bg_width/2., bg_pos-bg_width/2.])
      self.overview_lines[-1].set_ydata([bg_pos+bg_width/2., bg_pos+bg_width/2.])
    self.ui.xtof_overview.cplot.set_clim([tof_imin, tof_imax])

    if self.ui.show_colorbars.isChecked() and self.ui.xy_overview.cbar is None:
      self.ui.xy_overview.cbar=self.ui.xy_overview.canvas.fig.colorbar(self.ui.xy_overview.cplot)
      self.ui.xtof_overview.cbar=self.ui.xtof_overview.canvas.fig.colorbar(self.ui.xtof_overview.cplot)
    self.ui.xy_overview.draw()
    self.ui.xtof_overview.draw()

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
        tth0=(dataset.dangle-dataset.dangle0)-(304-dataset.dpix)*rad_per_pixel*180./pi

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

    if instrument.NAME=="REF_L":
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
    [row,col] = self.getCurrentRowColumnSelected()
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
  def _plot_gisans(self):
    gisans=self._gisansThread.gisans
    self._gisansThread=None
    info('Calculating GISANS projection, Done.')
    plots=[self.ui.gisans_pp, self.ui.gisans_mm, self.ui.gisans_pm, self.ui.gisans_mp]
    Imin=10**self.ui.gisansImin.value()
    Imax=10**self.ui.gisansImax.value()

    if len(gisans)>1:
      self.ui.frame_gisans_mm.show()
      if len(gisans)==4:
        self.ui.frame_gisans_sf.show()
      else:
        self.ui.frame_gisans_sf.hide()
    else:
      self.ui.frame_xy_mm.hide()
      self.ui.frame_xy_sf.hide()

    for i, datai in enumerate(gisans):
      plots[i].clear_fig()
      plots[i].pcolormesh(datai.QyGrid, datai.QzGrid, datai.SGrid,
                          log=self.ui.logarithmic_colorscale.isChecked(), imin=Imin, imax=Imax,
                          cmap=self.color)
      plots[i].set_xlabel(u'Q$_y$ [Å$^{-1}$]')
      plots[i].set_ylabel(u'Q$_z$ [Å$^{-1}$]')
      plots[i].set_title(self.channels[i])
      if plots[i].cplot is not None:
        plots[i].cplot.set_clim([Imin, Imax])
      if plots[i].cplot is not None and self.ui.show_colorbars.isChecked() and plots[i].cbar is None:
        plots[i].cbar=plots[i].canvas.fig.colorbar(plots[i].cplot)
      plots[i].draw()

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

  @log_call
  def openByNumber(self, number=None, do_plot=True):
    '''
    Search the data folders for a specific file number and open it.
    '''
    if instrument.NAME == "REF_M":
    
      if number is None:
        number=self.ui.numberSearchEntry.text()
      info('Trying to locate file number %s...'%number)
      QtGui.QApplication.instance().processEvents()
      if self.ui.histogramActive.isChecked():
        search=glob(os.path.join(instrument.data_base, (instrument.BASE_SEARCH%number)+u'histo.nxs'))
      elif self.ui.oldFormatActive.isChecked():
        search=glob(os.path.join(instrument.data_base, (instrument.OLD_BASE_SEARCH%(number, number))+u'.nxs'))
      else:
        search=glob(os.path.join(instrument.data_base, (instrument.BASE_SEARCH%number)+u'event.nxs'))
      if search:
        self.ui.numberSearchEntry.setText('')
        self.fileOpen(os.path.abspath(search[0]), do_plot=do_plot)
        return True
      else:
        info('Could not locate %s...'%number)
        return False

    else: # REF_L instrument

      if number is None:
        number = self.ui.numberSearchEntry.text()
        
      if number.strip() == '':
        return
        
      # check if we are looking at 1 file or more than 1
      listNumber = number.split(',')
      # removing empty element (in case user put too many ',')
      listNumber = filter(None, listNumber)
      
      # check if user wants to add this/those files to a previous selected box
      do_add = False
      #if self.ui.addRunNumbers.isEnabled() and self.ui.addRunNumbers.isChecked():
        #do_add = True
      
      # only 1 run number to load
      if len(listNumber) == 1:
        #try:
        fullFileName = FileFinder.findRuns("REF_L_%d"%int(listNumber[0]))[0]
        self.fileOpen(fullFileName, do_plot=do_plot, do_add=do_add)
        self.ui.numberSearchEntry.setText('')
        #except:
        #  info('Could not locate runs %s ...'%listNumber[0])
        #  return False
      else: # more than 1 file loaded
        notFoundRun = []
        foundRun = []
        for i in range(len(listNumber)):
          try:
            _fullFileName = FileFinder.findRuns("REF_L_%d"%int(listNumber[i]))[0]
            foundRun.append(_fullFileName)
          except:
            notFoundRun.append(listNumber[i])
        
        # inform user of file not found
        if notFoundRun:
          if len(notFoundRun)>1:
            _strListNumber = ",".join(notFoundRun)
          else:
            _strListNumber = notFoundRun[0]
          info('Could not locate runs %s ...' %_strListNumber)
        
        # load runs if any file found
        if foundRun is not None:
          self.fileOpen(foundRun, do_plot=do_plot, do_add=do_add)

        self.ui.numberSearchEntry.setText('')

  @waiting_effects
  def find_peak_back(self):
    
    bigTableData = self.bigTableData
    if bigTableData[0,0] is None:
      return
    
    [row,col] = self.getCurrentRowColumnSelected()
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

  @log_input
  def automaticExtraction(self, filenames):
    '''
    Make use of all automatic algorithms to reduce a full set of data in one run.
    Normalization files are detected by the tth angle to the selected peak position.
    
    The result is shown in the table and can be modified by the user.
    '''
    self.clearRefList(do_plot=False)
    for filename in sorted(filenames):
      # read files data and extract reflectivity
      if filename[-4:]=='.nxs':
        self.fileOpen(filename, do_plot=False)
      else:
        if not self.openByNumber(filename, do_plot=False):
          continue
      last_file=filename
      self.calc_refl()
      if (self.refl.ai*180./pi)<0.05:
        self.setNorm(do_plot=False, do_remove=False)
      else:
        norm=self.getNorm()
        if norm is None:
          warning('There is a dataset without fitting normalization, automatic extraction stopped!',
               extra={'title': 'Automatic extraction failed'})
          break
        # cut regions where the incident intensity drops below 10% of the maximum
        region=where(norm.Rraw>=(norm.Rraw.max()*0.1))[0]
        P0=len(norm.Rraw)-region[-1]
        PN=region[0]
        self.ui.rangeStart.setValue(P0)
        self.ui.rangeEnd.setValue(PN)
        # normalize total reflection or stich together adjecent scans
        self.normalizeTotalReflection()
        self.addRefList(do_plot=False)
    # rest cut options and show the file, which was added last
    self.ui.rangeStart.setValue(0)
    self.ui.rangeEnd.setValue(0)
    if last_file[-4:]=='.nxs':
      self.fileOpen(last_file, do_plot=True)
    else:
      self.openByNumber(last_file, do_plot=True)

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
    self._path_watcher.removePath(self.active_folder)
    if instrument.NAME == "REF_M":
      self.updateFileList(base, folder)
    self.active_folder=folder
    self._path_watcher.addPath(self.active_folder)

  @log_call
  def folderModified(self, flist=None):
    '''
    Called by the path watcher to update the file list when the folder
    has been modified.
    '''
    if instrument.NAME == "REF_L":
      return
    self.updateFileList(self.active_file, self.active_folder)

  @log_call
  def reloadFile(self):
      self.fileOpen(os.path.join(self.active_folder, self.active_file))

  @log_call
  def updateFileList(self, base, folder):
    '''
    Create a new filelist if the folder has changes.
    '''
    if instrument.NAME=='REF_M':
      was_active=self.auto_change_active
      self.auto_change_active=True
      if self.ui.histogramActive.isChecked():
        newlist=glob(os.path.join(folder, '*histo.nxs'))
        self.ui.eventModeEntries.hide()
      elif self.ui.oldFormatActive.isChecked():
        newlist=glob(os.path.join(folder, '*.nxs'))
        self.ui.eventModeEntries.hide()
      elif self.ui.eventActive.isChecked():
        self.ui.eventModeEntries.show()
        newlist=glob(os.path.join(folder, '*event.nxs'))
      else:
        self.ui.histogramActive.setChecked(True)
        return self.updateFileList(base, folder)
    else: 
      self.ui.eventModeEntries.show()
      newlist=glob(os.path.join(folder, '*event.nxs'))
      
    if instrument.NAME == 'REF_M':
      newlist.sort()
      newlist=map(lambda name: os.path.basename(name), newlist)
      oldlist=[self.ui.file_list.item(i).text() for i in range(self.ui.file_list.count())]
      if newlist!=oldlist:
        # only update the list if it has changed
        self.ui.file_list.clear()
        for item in newlist:
          listitem=QtGui.QListWidgetItem(item, self.ui.file_list)
          if item==base:
            self.ui.file_list.setCurrentItem(listitem)
      else:
        try:
          pass
          self.ui.file_list.setCurrentRow(newlist.index(base))
        except ValueError:
          pass
      self.auto_change_active=was_active

  @log_call
  def updateLabels(self):
    '''
    Write file metadata to the labels in the overview tab.
    '''
    
    if instrument.NAME == "REF_M":

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
      if self.ui.dataNormTabWidget.currentIndex() == 0:
        self.ui.dataNameOfFile.setText('%s'%d.filename)
      else:
        self.ui.normNameOfFile.setText('%s'%d.filename)

      self.ui.metadataProtonChargeValue.setText('%.2e'%d.proton_charge)
      self.ui.metadataProtonChargeUnits.setText('%s'%d.proton_charge_units)
      self.ui.metadataLambdaRequestedValue.setText('%.2f'%d.lambda_requested)
      self.ui.metadataLambdaRequestedUnits.setText('%s'%d.lambda_requested_units)
      self.ui.metadatathiValue.setText('%.2f'%d.thi)
      self.ui.metadatathiUnits.setText('%s'%d.thi_units)
      self.ui.metadatatthdValue.setText('%.2f'%d.tthd)
      self.ui.metadatatthdUnits.setText('%s'%d.tthd_units)
      self.ui.metadataS1WValue.setText('%.2f'%d.S1W)
      self.ui.metadataS2WValue.setText('%.2f'%d.S2W)
      self.ui.metadataS1HValue.setText('%.2f'%d.S1H)
      self.ui.metadataS2HValue.setText('%.2f'%d.S2H)
      
  @log_call
  def toggleColorbars(self):
    if instrument.NAME == 'REF_M':
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

  @waiting_effects          
  def bigTable_selection_changed(self, row, column):    

    self.editing_flag = False

    # if selection of same row and not data or column 0 and 6
#    if (self._prev_row_selected == row) and ((column != 0) and (column != 6)):
#      return

    # same row and same column selected
    if (self._prev_row_selected == row) and (self._prev_col_selected == column):
      return

    if (self._prev_row_selected == row) and (self._prev_col_selected < 6) and (column < 6):
      return
    
    if column is 6:
      col = 1
    else:
      col = 0

    _data = self.bigTableData[row,col]
    try:
      self.active_data = _data.active_data
      addButtonStatus = True
    except:
      self.active_data = None
      addButtonStatus = False

    #self.ui.addRunNumbers.setEnabled(addButtonStatus)

    self.userClickedInTable = True # this avoid to re-rerun this method a second time
    if column == 6:
      self.ui.dataNormTabWidget.setCurrentIndex(1)      
    else:
      self.ui.dataNormTabWidget.setCurrentIndex(0)  

    self._prev_row_selected = row
    self._prev_col_selected = column

    cell = self.ui.reductionTable.selectedItems()
    #print cell
    #if cell == []:
      #self.userClickedInTable = False
      #return
      
    # display norm tab
    if column == 6:
      self.ui.dataNormTabWidget.setCurrentIndex(1)
      # if cell is empty
      if cell == []:
        self.clear_plot_overview_REFL(isData=False)
        self.ui.normNameOfFile.setText('')
      else:
        cell = self.ui.reductionTable.selectedItems()[0]
        if cell.text() == '':
  #      cell.text == ''
          self.clear_plot_overview_REFL(isData=False)
          self.ui.normNameOfFile.setText('')
        else:
          cell = self.ui.reductionTable.selectedItems()[0]
          if (self.active_data is not None) and (_data.active_data.nxs is not None):
            self.plot_overview_REFL(plot_ix=True, plot_yt=True, plot_yi=True)
  
          else: # load the data
            _run_number = int(cell.text())
            _first_file_name = FileFinder.findRuns("REF_L%d" %int(_run_number))[0]
            
            _configDataset = self.bigTableData[row,2]
            
            if col == 1:
              isData = False
            else:
              isData = True
            
            event_split_bins = None
            event_split_index = 0
            bin_type = 0
            data = NXSData(_first_file_name, 
                           bin_type = bin_type,
                           bins = self.ui.eventTofBins.value(),
                           callback = self.updateEventReadout,
                           event_split_bins = event_split_bins,
                           event_split_index = event_split_index,
                           metadata_config_object = _configDataset,
                           isData = isData)
            
            r=row
            c=col
  
            self.bigTableData[r,c] = data
            self._prev_row_selected = r
            self._prev_col_selected = c
            
            self._fileOpenDoneREFL(data=data, 
                                   filename=_first_file_name, 
                                   do_plot=True,
                                   update_table=False)

    else: # display data tab
      self.ui.dataNormTabWidget.setCurrentIndex(0)
      # if cell is empty
      cell = self.ui.reductionTable.selectedItems()

      if (self.active_data is not None) and (_data.active_data.nxs is not None):
        self.plot_overview_REFL(plot_ix=True, plot_yt=True, plot_yi=True)
      
      else: # load (the data cell is empty or data not loaded yet)
        [row,col] = self.getTrueCurrentRowColumnSelected()
        if col < 6:
          col = 0
        item = self.ui.reductionTable.item(row,col)

        if item is not None:
          _run_number = int(str(item.text()))
          _first_file_name = FileFinder.findRuns("REF_L%d" %int(_run_number))[0]
          
          _configDataset = self.bigTableData[row,2]
          
          event_split_bins = None
          event_split_index = 0
          bin_type = 0
          data = NXSData(_first_file_name, 
                         bin_type = bin_type,
                         bins = self.ui.eventTofBins.value(),
                         callback = self.updateEventReadout,
                         event_split_bins = event_split_bins,
                         event_split_index = event_split_index,
                         metadata_config_object = _configDataset)
          
          r=row
          c=col
  
          self.bigTableData[r,c] = data
          self._prev_row_selected = r
          self._prev_col_selected = c
          
          self._fileOpenDoneREFL(data=data, 
                                 filename=_first_file_name, 
                                 do_plot=True,
                                 update_table=False)
      
    self.userClickedInTable = False

    self._prev_row_selected = row
    self._prev_col_selected = column

    # select data or norm cell 
    prev_range_selected = QtGui.QTableWidgetSelectionRange(row, 0, row, 6)
    self.ui.reductionTable.setRangeSelected(prev_range_selected, False)

    self.editing_flag = True

    if column < 6:
      _col = 0
    else:
      _col = 6

    range_selected = QtGui.QTableWidgetSelectionRange(row, _col, row, _col)
    self.ui.reductionTable.setRangeSelected(range_selected, True)

    self.enableWidgets(checkStatus=True)

  def data_norm_tab_changed(self, index):
    '''
    When user switch data - Norm, the selection should follow accordingly
    and the display of all the plots as well
    '''
    
    if self.userClickedInTable:
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

  def lin_log_toggle(self):
    
    print 'lin_log_toggle'


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
    if instrument.NAME == "REF_M":
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
    if instrument.NAME is "REF_M":
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

    if instrument.NAME == 'REF_M':

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

  def data_background_switch(self):
    '''
    With or without data background
    '''

    data = self.active_data
    if data is None:
      return

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

  def data_low_res_switch(self):
    '''
    With or without data low resolution range
    '''
        
    data = self.active_data
    if data is None:
      return

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

    data = self.active_data
    if data is None:
      return
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
    
  def normalization_background_switch(self):
    '''
    With or without normalization background
    '''
    
    flag = self.ui.normBackgroundFlag.isChecked()
    
    self.ui.normBackFromLabel.setEnabled(flag)
    self.ui.normBackFromValue.setEnabled(flag)
    self.ui.normBackToLabel.setEnabled(flag)
    self.ui.normBackToValue.setEnabled(flag)
    
    # save new settings
    self.save_new_settings()
    
    self.plot_overview_REFL(plot_yi=True, plot_yt=True)    
    
  def normalization_low_res_switch(self):
    '''
    With or without normalization low resolution range
    '''

    data = self.active_data
    if data is None:
      return

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

  # data peak spinboxes
  def data_peak_spinbox_validation(self):
    '''
    This function, reached when the user is done editing the
    spinboxes (ENTER, leaving the spinbox) 
    will make sure the min value is < max value    
    '''

    data = self.active_data
    if data is None:
      return

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
    self.plot_overview_REFL(plot_ix=True, plot_yt=True, plot_yi=True)
    
    # save new settings
    self.save_new_settings()
    
  # data back spinboxes
  def data_back_spinbox_validation(self):
    '''
    This function, reached when the user is done editing the
    spinboxes (ENTER, leaving the spinbox) 
    will make sure the min value is < max value  
    '''

    # get current row and column selected
    [r,c] = self.getCurrentRowColumnSelected()
    _data = self.bigTableData[r,c]
    data = _data.active_data
    if data is None:
      return
    
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

  # data low resolution spinboxes
  def data_lowres_spinbox_validation(self):
    '''
    This function, reached when the user is done editing the
    spinboxes (ENTER, leaving the spinbox) 
    will make sure the min value is < max value  
    '''

    data = self.active_data
    if data is None:
      return

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
    
  # norm peak spinboxes
  def norm_peak_spinbox_validation(self):
    '''
    This function, reached when the user is done editing the
    spinboxes (ENTER, leaving the spinbox) 
    will make sure the min value is < max value    
    '''

    data = self.active_data
    if data is None:
      return

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

    # refresh plots
    self.plot_overview_REFL(plot_ix=True, plot_yt=True, plot_yi=True)
    
  # norm back spinboxes
  def norm_back_spinbox_validation(self):
    '''
    This function, reached when the user is done editing the
    spinboxes (ENTER, leaving the spinbox) 
    will make sure the min value is < max value  
    '''

    data = self.active_data
    if data is None:
      return

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

    # refresh plots
    self.plot_overview_REFL(plot_ix=True, plot_yt=True, plot_yi=True)

  # data low resolution spinboxes
  def norm_lowres_spinbox_validation(self):
    '''
    This function, reached when the user is done editing the
    spinboxes (ENTER, leaving the spinbox) 
    will make sure the min value is < max value  
    '''

    data = self.active_data
    if data is None:
      return
    
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

  def save_new_settings(self):
    '''
    This function will retrieve all the settings (peak, background...)
    and will save them in the corresponding data or norm file (if any)
    '''
    
    [r,c] = self.getCurrentRowColumnSelected()
    data = self.bigTableData[r,c]

    if data is None:
      return

    _active_data = data.active_data

    data_peak = [self.ui.dataPeakFromValue.value(), 
                 self.ui.dataPeakToValue.value()]
    
    data_back = [self.ui.dataBackFromValue.value(),
                 self.ui.dataBackToValue.value()]
    
    data_low_res = [self.ui.dataLowResFromValue.value(),
                    self.ui.dataLowResToValue.value()]
    
    data_back_flag = self.ui.dataBackgroundFlag.isChecked()
    
    data_low_res_flag = self.ui.dataLowResFlag.isChecked()
    
    tof_range = [self.ui.TOFmanualFromValue.text(),
                 self.ui.TOFmanualToValue.text()]
    
#    if self.ui.TOFmanualMsValue.isChecked():
    tof_units = 'ms'
#    else:
#      tof_units = 'micros'
      
    tof_auto_flag = self.ui.dataTOFautoMode.isChecked()
    
    norm_flag = self.ui.useNormalizationFlag.isChecked()
    
    norm_peak = [self.ui.normPeakFromValue.value(),
                 self.ui.normPeakToValue.value()]
    
    norm_back = [self.ui.normBackFromValue.value(),
                 self.ui.normBackToValue.value()]
    
    norm_back_flag = self.ui.normBackgroundFlag.isChecked()
    
    norm_low_res = [self.ui.normLowResFromValue.value(),
                    self.ui.normLowResToValue.value()]
    
    norm_low_res_flag = self.ui.normLowResFlag.isChecked()
    
    _active_data.data_peak = data_peak
    _active_data.data_back = data_back
    _active_data.data_low_res = data_low_res
    _active_data.data_back_flag = data_back_flag
    _active_data.data_low_res_flag = data_low_res_flag
    _active_data.tof_range = tof_range
    _active_data.tof_units = tof_units
    _active_data.tof_auto_flag = tof_auto_flag
    _active_data.norm_flag = norm_flag
    _active_data.norm_peak = norm_peak
    _active_data.norm_back = norm_back
    _active_data.norm_back_flag = norm_back_flag
    _active_data.norm_low_res = norm_low_res
    _active_data.norm_low_res_flag = norm_low_res_flag
    
    # put back info in right place
    data.active_data = _active_data
    self.bigTableData[r,c] = data


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
  def loading_full_configuration(self):
    '''
    Reached by the load full configuration button
    will populate the GUI with the data retrieved from the configuration file 
    but will also save into memory all the data loaded
    '''
    _path = self.path_config
    filename = QtGui.QFileDialog.getOpenFileName(self,'Open Configuration File', _path)      
    if not(filename == ""):
      
      self.path_config = os.path.dirname(filename)
      
      # make sure the reductionTable is empty
      nbrRow = self.ui.reductionTable.rowCount()
      if nbrRow > 0:
        for _row in range(nbrRow):
          self.ui.reductionTable.removeRow(0)
      
      self.loadFullConfigAndPopulateGui(filename)
      self.enableWidgets(checkStatus=True)

  @log_call
  @waiting_effects
  def loading_configuration(self):
    '''
    Reached by the Load Configuration button
    will populate the GUI with the data retrieved from the configuration file
    '''
    _path = self.path_config
    filename = QtGui.QFileDialog.getOpenFileName(self,'Open Configuration File', _path)      
    if not (filename == ""):
      self.loading_configuration_file(filename)
            
  def loading_configuration_file(self, filename):
    # try:
    self.path_config = os.path.dirname(filename)
    
    # make sure the reductionTable is empty
    nbrRow = self.ui.reductionTable.rowCount()
    if nbrRow > 0:
      for _row in range(nbrRow):
        self.ui.reductionTable.removeRow(0)
    
    self.loadConfigAndPopulateGui(filename)
    self.enableWidgets(checkStatus=True)
    
    if self.reducedFilesLoadedObject is None:
      _reducedFilesLoadedObject = ReducedConfigFilesHandler(self)
    else:
      _reducedFilesLoadedObject = self.reducedFilesLoadedObject
    _reducedFilesLoadedObject.addFile(filename)
    _reducedFilesLoadedObject.updateGui()
    self.reducedFilesLoadedObject = _reducedFilesLoadedObject
      
#  except:
  #  warning('Could not open configuration file!')
    
  @log_call
  def saving_configuration(self):
    '''
    Reached by the Save Configuration button
    will retrieve all the data from the application and will save them using the 
    same format as Mantid
    '''
    
    _path = self.path_config
    filename = QtGui.QFileDialog.getSaveFileName(self, 'Save Configuration File', _path)
    if not(filename == ""):
      
      self.path = os.path.dirname(filename)
      self.saveConfig(filename)
#      self.saveReducedObject(filename)
      
  #@log_call
  #def saveReducedObject(self, filename):
    #'''
    #save reduce data (biTableData)
    #'''
    #pickleFilename = createPickleFilename(filename)
    #_bigTableData = self.bigTableData
    #filehandler = open(pickleFilename, 'w')
    #pickle.dump(_bigTableData, filehandler)
      
  @log_call
  def saveConfig(self, filename):
    
    strArray = []
    strArray.append('<Reduction>\n')
    strArray.append(' <instrument_name>REFL</instrument_name>\n')

    # time stamp
    import datetime
    strArray.append(' <timestamp>' + datetime.datetime.now().strftime("%A, %d. %B %Y %I:%M%p") + '</timestamp>\n')
    
    # python version
    import sys
    strArray.append(' <python_version>' + sys.version + '</python_version>\n')
    
    # platform
    import platform
    strArray.append(' <platform>' + platform.system() + '</platform>\n')
    
    # architecture
    strArray.append(' <architecture>' + platform.machine() + '</architecture>\n')
    
    # mantid version
    import mantid
    strArray.append(' <mantid_version>' + mantid.__version__ + '</mantid_version>\n')
    
    # metadata
    strArray.append(' <DataSeries>\n')
    
    nbrRow = self.ui.reductionTable.rowCount()
    _bigTableData = self.bigTableData
    for row in range(nbrRow):
      
      strArray.append('  <RefLData>\n')
      strArray.append('   <peak_selection_type>narrow</peak_selection_type>\n')

      # retrieve info from data or norm object in priority
      data_info = _bigTableData[row,0]
      if data_info is not None:
        _data = data_info.active_data
      
        data_full_file_name = _data.filename
        if type(data_full_file_name) == type([]):
          data_full_file_name = ','.join(data_full_file_name)
        data_peak = _data.peak
        data_back = _data.back
        data_low_res = _data.low_res
        data_back_flag = _data.back_flag
        data_low_res_flag = _data.low_res_flag
        tof = _data.tof_range
        tof_units = _data.tof_units
        tof_auto_flag = _data.tof_auto_flag
        q_range = _data.q_range
        lambda_range = _data.lambda_range
        incident_angle = _data.incident_angle
      
      else:

        _metadata = _bigTableData[row,2]
        if _metadata is not None: # collect data via previously loaded config
          data_full_file_name = _metadata.data_full_file_name
          data_peak = _metadata.data_peak
          data_back = _metadata.data_back
          data_low_res = _metadata.data_low_res
          data_back_flag = _metadata.data_back_flag
          data_low_res_flag = _metadata.data_low_res_flag
          tof = _metadata.tof
          
          # for old config file that do not have this flag yet
          try:
            q_range = _metadata.q_range
          except:
            q_range = ['0','0']
            
          try:
            lambda_range = _metadata.lambda_range
          except:
            lambda_range = ['0','0']
          
          try:
            incident_angle = _metadata.incident_angle
          except:
            incident_angle = ''
          
          tof_units = _metadata.tof_units
          tof_auto_flag = _metadata.tof_auto_flag

        else:
          data_full_file_name = ''
          data_peak = ['0','0']
          data_back = ['0','0']
          data_low_res = ['0','0']
          data_back_flag = True
          data_low_res_flag = True
          tof = ['0','0']
          tof_units = 'ms'
          tof_auto_flag = True
          q_range = ['0','0']
          lambda_range = ['0','0']
          incident_angle = ''

      norm_info = _bigTableData[row,1]
      if norm_info is not None:
        _norm = norm_info.active_data
               
        norm_full_file_name = _norm.filename
        if type(norm_full_file_name) == type([]):
          norm_full_file_name = ','.join(norm_full_file_name)

        norm_flag = _norm.use_it_flag
        norm_peak = _norm.peak
        norm_back = _norm.back
        norm_back_flag = _norm.back_flag
        norm_low_res = _norm.low_res
        norm_low_res_flag = _norm.low_res_flag
          
      else:

        _metadata = _bigTableData[row,2]
        if _metadata is not None: # collect data via previously loaded config
          norm_full_file_name = _metadata.norm_full_file_name
          norm_flag = _metadata.norm_flag
          norm_peak = _metadata.norm_peak
          norm_back = _metadata.norm_back
          norm_back_flag = _metadata.norm_back_flag
          norm_low_res = _metadata.norm_low_res
          norm_low_res_flag = _metadata.norm_low_res_flag

        else:
            norm_full_file_name = ''
            norm_flag = True
            norm_peak = ['0','0']
            norm_back = ['0','0']
            norm_back_flag = True
            norm_low_res = ['0','0']
            norm_low_res_flag = True
        
      strArray.append('   <from_peak_pixels>' + str(data_peak[0]) + '</from_peak_pixels>\n')
      strArray.append('   <to_peak_pixels>' + str(data_peak[1]) + '</to_peak_pixels>\n')
      strArray.append('   <peak_discrete_selection>N/A</peak_discrete_selection>\n')
      strArray.append('   <background_flag>' + str(data_back_flag) + '</background_flag>\n')
      strArray.append('   <back_roi1_from>' + str(data_back[0]) + '</back_roi1_from>\n')
      strArray.append('   <back_roi1_to>' + str(data_back[1]) + '</back_roi1_to>\n')
      strArray.append('   <back_roi2_from>0</back_roi2_from>\n')
      strArray.append('   <back_roi2_to>0</back_roi2_to>\n')
      strArray.append('   <tof_range_flag>True</tof_range_flag>\n')
      strArray.append('   <from_tof_range>' + str(tof[0]) + '</from_tof_range>\n')
      strArray.append('   <to_tof_range>' + str(tof[1]) + '</to_tof_range>\n')
      strArray.append('   <from_q_range>' + str(q_range[0]) + '</from_q_range>\n')
      strArray.append('   <to_q_range>' + str(q_range[1]) + '</to_q_range>\n')
      strArray.append('   <from_lambda_range>' + str(lambda_range[0]) + '</from_lambda_range>\n')
      strArray.append('   <to_lambda_range>' + str(lambda_range[1]) + '</to_lambda_range>\n')
      strArray.append('   <incident_angle>' + str(incident_angle) + '</incident_angle>\n')

      _data_run_number = self.ui.reductionTable.item(row,0).text()
      strArray.append('   <data_sets>' + _data_run_number + '</data_sets>\n')
      if type(data_full_file_name) == type([]):
        data_full_file_name = ','.join(data_full_file_name)
      strArray.append('   <data_full_file_name>' + data_full_file_name + '</data_full_file_name>\n')
      
      strArray.append('   <x_min_pixel>' + str(data_low_res[0]) + '</x_min_pixel>\n')
      strArray.append('   <x_max_pixel>' + str(data_low_res[1]) + '</x_max_pixel>\n')
      strArray.append('   <x_range_flag>' + str(data_low_res_flag) + '</x_range_flag>\n')
      
      tthd = self.ui.metadatatthdValue.text()
      strArray.append('   <tthd_value>' + tthd + '</tthd_value>\n')
      ths = self.ui.metadatathiValue.text()
      strArray.append('   <ths_value>' + ths + '</ths_value>\n')
    
      strArray.append('   <norm_flag>' + str(norm_flag) + '</norm_flag>\n')
      strArray.append('   <norm_x_range_flag>' + str(norm_low_res_flag) + '</norm_x_range_flag>\n')
      strArray.append('   <norm_x_max>' + str(norm_low_res[1]) + '</norm_x_max>\n')
      strArray.append('   <norm_x_min>' + str(norm_low_res[0]) + '</norm_x_min>\n')
      strArray.append('   <norm_from_peak_pixels>' + str(norm_peak[0]) + '</norm_from_peak_pixels>\n')
      strArray.append('   <norm_to_peak_pixels>' + str(norm_peak[1]) + '</norm_to_peak_pixels>\n')
      strArray.append('   <norm_background_flag>' + str(norm_back_flag) + '</norm_background_flag>\n')
      strArray.append('   <norm_from_back_pixels>' + str(norm_back[0]) + '</norm_from_back_pixels>\n')
      strArray.append('   <norm_to_back_pixels>' + str(norm_back[1]) + '</norm_to_back_pixels>\n')
      
      _norm_run_number_cell = self.ui.reductionTable.item(row,6)
      if _norm_run_number_cell is not None:
        _norm_run_number = _norm_run_number_cell.text()
      else:
        _norm_run_number = ''
      strArray.append('   <norm_dataset>' + _norm_run_number + '</norm_dataset>\n')
      if type(norm_full_file_name) == type([]):
        norm_full_file_name = ','.join(norm_full_file_name)
      strArray.append('   <norm_full_file_name>' + norm_full_file_name + '</norm_full_file_name>\n')
      
      q_min = '0'   #FIXME
      q_max = '0'   #FIXME
      
      strArray.append('   <auto_q_binning>False</auto_q_binning>\n')
      strArray.append('   <overlap_lowest_error>True</overlap_lowest_error>\n')
      strArray.append('   <overlap_mean_value>False</overlap_mean_value>\n');

      angleValue = self.ui.angleOffsetValue.text()
      angleError = self.ui.angleOffsetError.text()
      strArray.append('   <angle_offset>' + angleValue + '</angle_offset>\n')
      strArray.append('   <angle_offset_error>' + angleError + '</angle_offset_error>\n')
      
      scalingFactorFlag = self.ui.scalingFactorFlag.isChecked()
      strArray.append('   <scaling_factor_flag>' + str(scalingFactorFlag) + '</scaling_factor_flag>\n')
      scalingFactorFile = self.ui.scalingFactorFile.text()
      strArray.append('   <scaling_factor_file>' + scalingFactorFile + '</scaling_factor_file>\n')
      scalingFactorSlitsFlag = self.ui.scalingFactorSlitsWidthFlag.isChecked()
      strArray.append('   <slits_width_flag>' + str(scalingFactorSlitsFlag) + '</slits_width_flag>\n')
      
      geometryCorrectionFlag = self.ui.geometryCorrectionFlag.isChecked()
      strArray.append('   <geometry_correction_switch>' + str(geometryCorrectionFlag) + '</geometry_correction_switch>\n')
      
      # incident medium
      allItems = [self.ui.selectIncidentMediumList.itemText(i) for i in range(self.ui.selectIncidentMediumList.count())] 
      finalList = allItems[1:]
      strFinalList = ",".join(finalList)
      strArray.append('   <incident_medium_list>' + strFinalList + '</incident_medium_list>\n')
      
      imIndex = self.ui.selectIncidentMediumList.currentIndex()
      strArray.append('   <incident_medium_index_selected>' + str(imIndex) + '</incident_medium_index_selected>\n')
      
      # output
      fcFlag = self.ui.output4thColumnFlag.isChecked()
      strArray.append('   <fourth_column_flag>' + str(fcFlag) + '</fourth_column_flag>\n')
      
      fcdq0 = self.ui.dq0Value.text()
      strArray.append('   <fourth_column_dq0>' + str(fcdq0) + '</fourth_column_dq0>\n')
      
      fcdqoverq = self.ui.dQoverQvalue.text()
      strArray.append('   <fourth_column_dq_over_q>' + str(fcdqoverq) + '</fourth_column_dq_over_q>\n')
    
      strArray.append('  </RefLData>\n')
    
    strArray.append('  </DataSeries>\n')
    strArray.append('</Reduction>\n')

    # write out XML file
    f = open(filename, 'w')
    f.writelines(strArray)
    f.close()
    
  @waiting_effects          
  @log_call
  def loadFullConfigAndPopulateGui(self, filename):
    '''
    This function will parse the XML config file (Mantid format) and will populate the 
    GUI
    '''
    try:
      dom = minidom.parse(filename)
    except:
      info('No configuration file loaded!')
      return
    
    RefLData = dom.getElementsByTagName('RefLData')
    nbrRowBigTable = len(RefLData)
    
    # reset bigTable
    self.ui.reductionTable.clearContents()
    
    _first_file_name = ''
    
    # load the first data and display it
    self.bigTableData = empty((20,3), dtype=object)
    
    # start parsing xml file
    _row = 0
    for node in RefLData:
      
      self.ui.reductionTable.insertRow(_row)

      # data 
      _data_sets = self.getNodeValue(node,'data_sets')
      self.addItemToBigTable(_data_sets, _row, 0, editableFlag=True)
      
      # norm
      _norm_sets = self.getNodeValue(node,'norm_dataset')
      self.addItemToBigTable(_norm_sets, _row, 6, editableFlag=True)
      
      # incident angle
      try:
        _incident_angle = self.getNodeValue(node,'incident_angle')
      except:
        _incident_angle = 'N/A'
      self.addItemToBigTable(_incident_angle, _row, 1)
      
      # lambda range
      try:
        _from_l = self.getNodeValue(node, 'from_lambda_range')
      except:
        _from_l = 'N/A'
      self.addItemToBigTable(_from_l, _row, 2)
      
      try:
        _to_l = self.getNodeValue(node, 'to_lambda_range')
      except:
        _to_l = 'N/A'
      self.addItemToBigTable(_to_l, _row, 3)
      
      # q range
      try:
        _from_q = self.getNodeValue(node,'from_q_range')
      except:
        _from_q = 'N/A'
      self.addItemToBigTable(_from_q, _row, 4)
      
      try:
        _to_q = self.getNodeValue(node,'to_q_range')
      except:
        _to_q = 'N/A'
      self.addItemToBigTable(_to_q, _row, 5)
      
      # only for first row
      if _row == 0:
        _first_file_name = self.getNodeValue(node, 'data_full_file_name')
        if _first_file_name == '': # no full_file_name defined
          _first_file_name = FileFinder.findRuns("REF_L%d" %int(_data_sets))[0]
        else:
          _first_file_name = _first_file_name.split(',')

        # load general settings for first row only
        scaling_factor_file = self.getNodeValue(node, 'scaling_factor_file')
        self.ui.scalingFactorFile.setText(scaling_factor_file)

        scaling_factor_flag = self.getNodeValue(node, 'scaling_factor_flag')
        self.ui.scalingFactorFlag.setChecked(strtobool(scaling_factor_flag))
        self.sf_widgets_status(strtobool(scaling_factor_flag))
        
        slits_width_flag = self.getNodeValue(node, 'slits_width_flag')
        self.ui.scalingFactorSlitsWidthFlag.setChecked(strtobool(slits_width_flag))

        incident_medium_list = self.getNodeValue(node, 'incident_medium_list')
        im_list = incident_medium_list.split(',')
        self.ui.selectIncidentMediumList.addItems(im_list)

        incident_medium_index_selected = self.getNodeValue(node, 'incident_medium_index_selected')
        self.ui.selectIncidentMediumList.setCurrentIndex(int(incident_medium_index_selected))
        
        fourth_column_flag = self.getNodeValue(node, 'fourth_column_flag')
        self.ui.output4thColumnFlag.setChecked(strtobool(fourth_column_flag))
        fourth_column_dq0 = self.getNodeValue(node, 'fourth_column_dq0')
        self.ui.dq0Value.setText(fourth_column_dq0)
        fourth_column_dq_over_q = self.getNodeValue(node, 'fourth_column_dq_over_q')
        self.ui.dQoverQvalue.setText(fourth_column_dq_over_q)

      try:
        _data_full_file_name = self.getNodeValue(node, 'data_full_file_name')
        _data_full_file_name = _data_full_file_name.split(',')
      except:
        _data_full_file_name = ''
        
      try:
        _norm_full_file_name = self.getNodeValue(node, 'norm_full_file_name')
        _norm_full_file_name = _norm_full_file_name.split(',')
      except:
        _norm_full_file_name = ''

      _metadataObject = self.getMetadataObject(node)
      _metadataObject.data_full_file_name = _data_full_file_name
      _metadataObject.norm_full_file_name = _norm_full_file_name
      self.bigTableData[_row,2] = _metadataObject
      
      _row += 1

    # Load all the Data and Norm into memory

    # default parameters
    event_split_bins = None
    event_split_index = 0
    bin_type = 0
    for j in range(_row):

      # move by default to first data 
      if j == 0:
        # select first data file
        self.ui.dataNormTabWidget.setCurrentIndex(0)
        self.ui.reductionTable.setRangeSelected(QtGui.QTableWidgetSelectionRange(0,0,0,0),True)                                                                                   	
    
      # load data file
      _configDataset = self.bigTableData[j,2]
      _full_file_name = _configDataset.data_full_file_name
      
      data = NXSData(_full_file_name, 
                     bin_type = bin_type,
                     bins = self.ui.eventTofBins.value(),
                     callback = self.updateEventReadout,
                     event_split_bins = event_split_bins,
                     event_split_index = event_split_index,
                     metadata_config_object = _configDataset,
                     angle_offset = self.ui.angleOffsetValue.text())
    
      # make sure that incident_angle, q_range and/or lambda_range have values
      item = self.ui.reductionTable.item(j,1)
      if item is None:
        _item = QtGui.QTableWidgetItem(str(data.active_data.incident_angle))
        self.ui.reductionTable.setItem(j, 1, _item)
      else:    
        incident_angle = item.text()
        if incident_angle == 'N/A' or incident_angle == '':
          _item = QtGui.QTableWidgetItem(str(data.active_data.incident_angle))
          self.ui.reductionTable.setItem(j, 1, _item)
      
      item = self.ui.reductionTable.item(j,4)
      if item is None:
        [_from_q, _to_q] = data.active_data.q_range
        _item = QtGui.QTableWidgetItem(str(_from_q))
        self.ui.reductionTable.setItem(j,4, _item)
        _item = QtGui.QTableWidgetItem(str(_to_q))
        self.ui.reductionTable.setItem(j,5, _item)
      else:
        from_q = item.text()
        if from_q == '':
          [_from_q, _to_q] = data.active_data.q_range
          _item = QtGui.QTableWidgetItem(str(_from_q))
          self.ui.reductionTable.setItem(j,4, _item)
          _item = QtGui.QTableWidgetItem(str(_to_q))
          self.ui.reductionTable.setItem(j,5, _item)
      
      item = self.ui.reductionTable.item(j,2)
      if item is None:
        [_from_l, _to_l] = data.active_data.lambda_range
        _item = QtGui.QTableWidgetItem(str(_from_l))
        self.ui.reductionTable.setItem(j,2, _item)
        _item = QtGui.QTableWidgetItem(str(_to_l))
        self.ui.reductionTable.setItem(j,3, _item)
      else:
        from_lambda = item.text()
        if from_lambda == '':
          [_from_l, _to_l] = data.active_data.lambda_range
          _item = QtGui.QTableWidgetItem(str(_from_l))
          self.ui.reductionTable.setItem(j,2, _item)
          _item = QtGui.QTableWidgetItem(str(_to_l))
          self.ui.reductionTable.setItem(j,3, _item)
          
      self.bigTableData[j,0] = data
      
      if j == 0:
        self._prev_row_selected = 0
        self._prev_col_selected = 0
    
        self._fileOpenDoneREFL(data=data, 
                               filename=_first_file_name, 
                               do_plot=True,
                               update_table=False)
        
        ## load normalization file
        _configDataset = self.bigTableData[j,2]
        try:
          data = NXSData(_first_file_name, 
                         bin_type = bin_type,
                         bins = self.ui.eventTofBins.value(),
                         callback = self.updateEventReadout,
                         event_split_bins = event_split_bins,
                         event_split_index = event_split_index,
                         metadata_config_object = _configDataset,
                         angle_offset = self.ui.angleOffsetValue.text(),
                         isData = False)
        except:
          warning('Could not open file:', exc_info=True)
          return
          
        self.bigTableData[j,1] = data


  @waiting_effects          
  @log_call
  def loadConfigAndPopulateGui(self, filename):
    '''
    This function will parse the XML config file (Mantid format) and will populate the 
    GUI
    '''
    try:
      dom = minidom.parse(filename)
    except:
      info('No configuration file loaded!')
      return
    
    RefLData = dom.getElementsByTagName('RefLData')
    nbrRowBigTable = len(RefLData)
    
    # reset bigTable
    self.ui.reductionTable.clearContents()
    
    _first_file_name = ''
    
    # load the first data and display it
    self.bigTableData = empty((20,3), dtype=object)
    
    # start parsing xml file
    _row = 0
    for node in RefLData:
      
      self.ui.reductionTable.insertRow(_row)

      # data 
      _data_sets = self.getNodeValue(node,'data_sets')
      self.addItemToBigTable(_data_sets, _row, 0, editableFlag=True)
      
      # norm
      _norm_sets = self.getNodeValue(node,'norm_dataset')
      self.addItemToBigTable(_norm_sets, _row, 6, editableFlag=True)
      
      # incident angle
      try:
        _incident_angle = self.getNodeValue(node,'incident_angle')
      except:
        _incident_angle = 'N/A'
      self.addItemToBigTable(_incident_angle, _row, 1)
      
      # lambda range
      try:
        _from_l = self.getNodeValue(node, 'from_lambda_range')
      except:
        _from_l = 'N/A'
      self.addItemToBigTable(_from_l, _row, 2)
      
      try:
        _to_l = self.getNodeValue(node, 'to_lambda_range')
      except:
        _to_l = 'N/A'
      self.addItemToBigTable(_to_l, _row, 3)
      
      # q range
      try:
        _from_q = self.getNodeValue(node,'from_q_range')
      except:
        _from_q = 'N/A'
      self.addItemToBigTable(_from_q, _row, 4)
      
      try:
        _to_q = self.getNodeValue(node,'to_q_range')
      except:
        _to_q = 'N/A'
      self.addItemToBigTable(_to_q, _row, 5)
      
      # only for first row
      if _row == 0:
        _first_file_name = self.getNodeValue(node, 'data_full_file_name')
        if _first_file_name == '': # no full_file_name defined
          _first_file_name = FileFinder.findRuns("REF_L%d" %int(_data_sets))[0]
        else:
          _first_file_name = _first_file_name.split(',')

        # load general settings for first row only
        scaling_factor_file = self.getNodeValue(node, 'scaling_factor_file')
        self.ui.scalingFactorFile.setText(scaling_factor_file)

        scaling_factor_flag = self.getNodeValue(node, 'scaling_factor_flag')
        self.ui.scalingFactorFlag.setChecked(strtobool(scaling_factor_flag))
        self.sf_widgets_status(strtobool(scaling_factor_flag))
        
        slits_width_flag = self.getNodeValue(node, 'slits_width_flag')
        self.ui.scalingFactorSlitsWidthFlag.setChecked(strtobool(slits_width_flag))

        incident_medium_list = self.getNodeValue(node, 'incident_medium_list')
        im_list = incident_medium_list.split(',')
        self.ui.selectIncidentMediumList.addItems(im_list)

        incident_medium_index_selected = self.getNodeValue(node, 'incident_medium_index_selected')
        self.ui.selectIncidentMediumList.setCurrentIndex(int(incident_medium_index_selected))
        
        fourth_column_flag = self.getNodeValue(node, 'fourth_column_flag')
        self.ui.output4thColumnFlag.setChecked(strtobool(fourth_column_flag))
        fourth_column_dq0 = self.getNodeValue(node, 'fourth_column_dq0')
        self.ui.dq0Value.setText(fourth_column_dq0)
        fourth_column_dq_over_q = self.getNodeValue(node, 'fourth_column_dq_over_q')
        self.ui.dQoverQvalue.setText(fourth_column_dq_over_q)

      try:
        _data_full_file_name = self.getNodeValue(node, 'data_full_file_name')
        _data_full_file_name = _data_full_file_name.split(',')
      except:
        _data_full_file_name = ''
        
      try:
        _norm_full_file_name = self.getNodeValue(node, 'norm_full_file_name')
        _norm_full_file_name = _norm_full_file_name.split(',')
      except:
        _norm_full_file_name = ''

      _metadataObject = self.getMetadataObject(node)
      _metadataObject.data_full_file_name = _data_full_file_name
      _metadataObject.norm_full_file_name = _norm_full_file_name
      self.bigTableData[_row,2] = _metadataObject
      
      _row += 1

    # select first data file
    self.ui.dataNormTabWidget.setCurrentIndex(0)
    self.ui.reductionTable.setRangeSelected(QtGui.QTableWidgetSelectionRange(0,0,0,0),True)                                                                                   	
    
    # load first data file
    event_split_bins = None
    event_split_index = 0
    bin_type = 0
    _configDataset = self.bigTableData[0,2]
    data = NXSData(_first_file_name, 
                   bin_type = bin_type,
                   bins = self.ui.eventTofBins.value(),
                   callback = self.updateEventReadout,
                   event_split_bins = event_split_bins,
                   event_split_index = event_split_index,
                   metadata_config_object = _configDataset,
                   angle_offset = self.ui.angleOffsetValue.text())
    
    # make sure that incident_angle, q_range and/or lambda_range have values
    item = self.ui.reductionTable.item(0,1)
    if item is None:
      _item = QtGui.QTableWidgetItem(str(data.active_data.incident_angle))
      _item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)      
      self.ui.reductionTable.setItem(0, 1, _item)
    else:    
      incident_angle = item.text()
      if incident_angle == 'N/A' or incident_angle == '':
        _item = QtGui.QTableWidgetItem(str(data.active_data.incident_angle))
        _item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)      
        self.ui.reductionTable.setItem(0, 1, _item)
    
    item = self.ui.reductionTable.item(0,4)
    if item is None:
      [_from_q, _to_q] = data.active_data.q_range
      _item = QtGui.QTableWidgetItem(str(_from_q))
      _item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)      
      self.ui.reductionTable.setItem(0,4, _item)
      _item = QtGui.QTableWidgetItem(str(_to_q))
      _item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)      
      self.ui.reductionTable.setItem(0,5, _item)
    else:
      from_q = item.text()
      if from_q == '':
        [_from_q, _to_q] = data.active_data.q_range
        _item = QtGui.QTableWidgetItem(str(_from_q))
        _item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)      
        self.ui.reductionTable.setItem(0,4, _item)
        _item = QtGui.QTableWidgetItem(str(_to_q))
        _item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)      
        self.ui.reductionTable.setItem(0,5, _item)
    
    item = self.ui.reductionTable.item(0,2)
    if item is None:
      [_from_l, _to_l] = data.active_data.lambda_range
      _item = QtGui.QTableWidgetItem(str(_from_l))
      _item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)      
      self.ui.reductionTable.setItem(0,2, _item)
      _item = QtGui.QTableWidgetItem(str(_to_l))
      _item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)      
      self.ui.reductionTable.setItem(0,3, _item)
    else:
      from_lambda = item.text()
      if from_lambda == '':
        [_from_l, _to_l] = data.active_data.lambda_range
        _item = QtGui.QTableWidgetItem(str(_from_l))
        _item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)      
        self.ui.reductionTable.setItem(0,2, _item)
        _item = QtGui.QTableWidgetItem(str(_to_l))
        _item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)      
        self.ui.reductionTable.setItem(0,3, _item)
          
    r=0
    c=0
    self.bigTableData[r,c] = data
    self._prev_row_selected = r
    self._prev_col_selected = c

    self._fileOpenDoneREFL(data=data, 
                           filename=_first_file_name, 
                           do_plot=True,
                           update_table=False)


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

    return iMetadata

  def sf_browse_button(self):
    filename = QtGui.QFileDialog.getOpenFileName(self,'Open scaling factor file', '.',"sfConfig (*.cfg)")
    if filename is not '':
      self.ui.scalingFactorFile.setText(filename)
      self.populate_sf_widgets(filename)


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
    

  def sf_widgets_status(self, bool):
    self.ui.label_sf_precision.setEnabled(bool)
    self.ui.sfPrecision.setEnabled(bool)
    self.ui.scalingFactorSlitsWidthFlag.setEnabled(bool)
    self.ui.scalingFactorFile.setEnabled(bool)
    self.ui.selectIncidentMediumList.setEnabled(bool)
    self.ui.sfBrowseButton.setEnabled(bool)

  def select_current_SF(self):
  
    sf_status = 'auto'
    if self.ui.manualSF.isChecked(): 
      sf_status = 'manual'
    elif self.ui.oneSF.isChecked():
      sf_status = '1'
      
    bigTableData = self.bigTableData
    nbr_row = self.ui.reductionTable.rowCount()
    for i in range(nbr_row):
      _data = bigTableData[i,0]
      if sf_status == 'auto':
        _data.sf = _data.sf_auto
      elif sf_status == 'manual':
        _data.sf = _data.sf_manual
      else:
        _data.sf = 1
        bigTableData[i,0] = _data
  
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
      _data = bigTableData[i,0]
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

    # move to stitching table tab
    self.ui.plotTab.setCurrentIndex(1)      


  def plot_stitched_scaled_data(self):
    
    bigTableData = self.bigTableData
    nbr_row = self.ui.reductionTable.rowCount()
    
    _colors = colors.COLOR_LIST
    _colors.append(_colors)

    self.ui.data_stitching_plot.clear()
    self.ui.data_stitching_plot.draw()
    
    for i in range(nbr_row):

      _data = bigTableData[i,0]
      _q_axis = _data.q_axis_for_display
      _y_axis = _data.y_axis_for_display
      _e_axis = _data.e_axis_for_display
      
      sf = _data.sf
      
      _y_axis = _y_axis / sf
      _e_axis = _e_axis / sf
      
      self.ui.data_stitching_plot.errorbar(_q_axis, _y_axis, yerr=_e_axis, color=_colors[i])
      self.ui.data_stitching_plot.draw()

    self.ui.data_stitching_plot.set_xlabel(u'Q (1/Angstroms)')
    self.ui.data_stitching_plot.set_ylabel(u'R')
    self.ui.data_stitching_plot.draw()
    

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
    '''
    plot the data after reduction
    '''
    
    self.clearStitchingTable()
        
    loadedAscii = reducedAsciiLoader(self,asciiFilename='', isLiveReduced=True, bigTableData=self.bigTableData )    
    if self.stitchingAsciiWidgetObject is None:
      self.stitchingAsciiWidgetObject = stitchingAsciiWidgetObject(self, loadedAscii)
    else:
      self.stitchingAsciiWidgetObject.addData(loadedAscii)
    
    self.stitchingAsciiWidgetObject.updateDisplay()
  
    # refresh reductionTable content (lambda range, Q range...etc)
    self.update_reductionTable()
    self.update_stitchingTable()

  def refresh_stitching_ascii_plot(self):
    if self.stitchingAsciiWidgetObject is None:
      return
    
    self.stitchingAsciiWidgetObject.updateStatus()
    self.stitchingAsciiWidgetObject.updateDisplay()


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
      _data = bigTableData[i,0]
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
      reflectivity_plot.draw()
      
    reflectivity_plot.set_xlabel(u'Q (1/Angstroms)')
    type = self.get_selected_output_reduced()    
    if type == 'RvsQ':
      reflectivity_plot.set_ylabel(u'R')
    elif type == 'RQ4vsQ':
      reflectivity_plot.set_ylabel(u'RQ4')
    else:
      reflectivity_plot.set_ylabel(u'Log(Q))')
    reflectivity_plot.draw()
                               
    liveDataSet = reducedAsciiLoader(self, '', True, bigTableData)
    if self.stitchingAsciiWidgetObject is None:
      self.stitchingAsciiWidgetObject = stitchingAsciiWidgetObject(self, liveDataSet)
    else:
      self.stitchingAsciiWidgetObject.addData(liveDataSet)
    
    self.stitchingAsciiWidgetObject.updateDisplay()


  def replot_stitched_data(self):
    '''
    plot the data after stitching
    '''
    bigTableData = self.bigTableData
    nbr_row = self.ui.reductionTable.rowCount()
    
    data_stitching_plot = self.ui.data_stitching_plot
    
    _colors = colors.COLOR_LIST
    _colors.append(_colors)
    
    # start by clearing plot
    data_stitching_plot.clear()
    data_stitching_plot.draw()
    
    for i in range(nbr_row):
      _data = bigTableData[i,0]
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
  def output_selected_data_into_crtof_ascii(self):
    '''
    The RTOF of the selected data set (data or norm) will be output into an ASCII file
    '''
    bigTableData = self.bigTableData
    if bigTableData[0,0] is None and bigTableData[0,1] is None:
      info('No Data!')
      return

    [row,col] = self.getCurrentRowColumnSelected()
    if col == 1:
      table_col = 6
    else:
      table_col = 0
    run_number = self.ui.reductionTable.item(row,table_col).text()
    default_filename = 'REFL_' + run_number + '_crtof.txt'
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

    [row,col] = self.getCurrentRowColumnSelected()
    if col == 1:
      table_col = 6
    else:
      table_col = 0
    run_number = self.ui.reductionTable.item(row,table_col).text()
    default_filename = 'REFL_' + run_number + '_rpx.txt'
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
    default_filename = 'REFL_' + run_number + '_combined_data.txt'
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

  def data_stitching_is_auto(self):
    self.data_stitching_mode('auto')

  def data_stitching_is_manual(self):
    self.data_stitching_mode('manual')
    
  def data_stitching_is_1(self):
    self.data_stitching_mode('1')


  def manual_entry_of_sf_table(self):
    '''
    update sf data of selected row
    '''

    bigTableData = self.bigTableData

    # switch to manual option
    self.ui.manualSF.setChecked(True)
    self.ui.autoSF.setChecked(False)
    self.ui.oneSF.setChecked(False)
    
    # save all manual parameters
    nbr_row = self.ui.dataStitchingTable.rowCount()
    for i in range(nbr_row):
      
      _data = bigTableData[i,0]
      
      _sf_manual = self.ui.dataStitchingTable.cellWidget(i,2).value()
      _data.sf_manual = _sf_manual
    
      bigTableData[i,0] = _data

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
    
    if _data.q_axis_for_display == []:
      return
    
    if type == "auto":
      for i in range(nbr_row):
        _data = bigTableData[i,0]
        _data.sf = _data.sf_auto
        
    elif type == "manual":
      # recover manual input 
      for i in range(nbr_row):
        _data = bigTableData[i,0]
        _data.sf = _data.sf_manual

    else: # no scaling apply, just plot data
      for i in range(nbr_row):
        _data = bigTableData[i,0]
        _data.sf = 1
    
    self.plot_stitched_scaled_data()

  def update_stitchingTable(self):
    '''
    will refresh the table in the stitching table
    '''
    bigTableData = self.bigTableData
    nbr_row = self.ui.reductionTable.rowCount()
    
    for i in range(nbr_row):
      
      _data = bigTableData[i,0]
      _active_data = _data.active_data

      self.ui.dataStitchingTable.insertRow(i)

      _run_number = self.ui.reductionTable.item(i,0).text()
      _run_number_item = QtGui.QTableWidgetItem(_run_number)
      _run_number_item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
      self.ui.dataStitchingTable.setItem(i,0,_run_number_item)

      _brush = QtGui.QBrush()
      if _data.sf_auto_found_match:
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

  def addItemToBigTable(self, value, row, column, editableFlag=False):
    '''
    Add element by element in the BigTable
    '''
    _item = QtGui.QTableWidgetItem(str(value))
    if editableFlag:
      color = QtGui.QColor(13,24,241)
    else:
      color = QtGui.QColor(100,100,150)
    _item.setForeground(color)
    if not editableFlag:
      _item.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
      
    self.ui.reductionTable.setItem(row, column, _item)

  def load_reduced_ascii(self):
    
#    try:
      _path = self.path_config
      filename = QtGui.QFileDialog.getOpenFileName(self,'Open Reduced Data Set', _path)      
      if not(filename == ""):
        self.path_config = os.path.dirname(filename)
      
        loadedAscii = reducedAsciiLoader(self, filename)
        if self.stitchingAsciiWidgetObject is None:
          self.stitchingAsciiWidgetObject = stitchingAsciiWidgetObject(self, loadedAscii)
        else:
          self.stitchingAsciiWidgetObject.addData(loadedAscii)
        
        self.stitchingAsciiWidgetObject.updateDisplay()
          
  #  except:
   #   warning('Could not open ASCII file!')
    

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
    if instrument.NAME == "REF_L":
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
    try:
      from PyQt4.pyqtconfig import Configuration
      pyqtversion=Configuration().pyqt_version_str
    except ImportError:
      pyqtversion='Unknown'

    if instrument.NAME == 'REF_M':
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
      