from mantid.simpleapi import *
from .qreduce import NXSData
import numpy as np

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
    
    def __init__(self, main_gui, dataCell, normCell, oData, oNorm, oConfig):
        '''
        Initialize the reduction object by 
        setting data and normalization files
        '''
        self.dataCell = dataCell
        self.normCell = normCell
        
        self.oConfig = oConfig

        # if the oData is empty, retrieve info from oConfig
        if oData is None:
            oData = self.populate_data_object(main_gui, oConfig, 'data')
        self.oData = oData
        
        # retrieve norm if user wants norm and if normCell is not empty
        if normCell != '':
            if oNorm is None:
                # make sure the norm flag is on in the config file
                if oConfig.norm_flag:
                    oNorm = self.populate_data_object(main_gui, oConfig, 'norm')
            else: # make sure the flag is ON         
                if not(oNorm.active_data.norm_flag):
                    oNorm = None
                
        self.oNorm = oNorm

    def integrate_over_low_res_range(self):
        '''
        This will integrate over the low resolution range of the data and norm objects
        '''
        print 'integrate_over_low_res_range'

        data = self.oData.active_data       
#        print 'data: '
#        print '-> data_low_res_flag: %s' %data.data_low_res_flag
        if data.low_res_flag:
            from_pixel = int(data.low_res[0])
            to_pixel = int(data.low_res[1])
        else:
            from_pixel = int(data.low_resolution_range[0])
            to_pixel = int(data.low_resolution_range[1])
            
#        print '-> from_pixel: %d' % from_pixel
#        print '-> to_pixel: %d' % to_pixel

        Ixyt = data.Ixyt   # for example [303,256,471]
        Exyt = data.Exyt
         
#        x_dim = np.size(Ixyt,0)
#        y_dim = np.size(Ixyt,1)
#        tof_dim = np.size(Ixyt,2)
        
#        _y_error_axis = np.zeros((y_dim, tof_dim))
        
#        x_size = to_pixel - from_pixel + 1
#        x_range = np.arange(x_size) + from_pixel
        
#        y_range = np.arange(y_dim)

        # calculate y axis
        Ixyt_crop = Ixyt[from_pixel:to_pixel+1,:,:]
        self.data_y_axis = Ixyt_crop.sum(axis=0)
        
        # calculate error axis
        Exyt_crop = Exyt[from_pixel:to_pixel+1,:,:]
        Exyt_crop_sq = Exyt_crop * Exyt_crop
        _y_error_axis = Exyt_crop_sq.sum(axis=0)
        self.data_y_error_axis = np.sqrt(_y_error_axis)

        if self.oNorm is not None:
            norm = self.oNorm.active_data
        
            if data.low_res_flag:
                from_pixel = int(data.low_res[0])
                to_pixel = int(data.low_res[1])
            else:
                from_pixel = int(data.low_resolution_range[0])
                to_pixel = int(data.low_resolution_range[1])
        
            # calculate y axis
            Ixyt_crop = Ixyt[from_pixel:to_pixel+1,:,:]
            self.norm_y_axis = Ixyt_crop.sum(axis=0)
            
            # calculate error axis
            Exyt_crop = Exyt[from_pixel:to_pixel+1,:,:]
            Exyt_crop_sq = Exyt_crop * Exyt_crop
            _y_error_axis = Exyt_crop_sq.sum(axis=0)
            self.norm_y_error_axis = np.sqrt(_y_error_axis)

    def get_error_0counts(self, data):
        '''
        return the default error value when error of data is 0
        '''
        _proton_charge_nxs = data.proton_charge / 3.6
        return 1./float(_proton_charge_nxs)

    def substract_data_background(self):
        '''
        substract background of data and norm
        '''
        print 'substract_background'
        
        data_y_axis = self.data_y_axis
        data_y_error_axis = self.data_y_error_axis

        peak_min = peak[0]
        peak_max = peak[1]
        back_min = back[0]
        back_max = back[1]

        # retrieve data peak range
        data = self.oData.active_data       
        if data.back_flag:
            peak = data.peak
            back = data.back

            error_0 = self.get_error_0counts(data)
            
            tof_dim = np.size(data_y_axis,1)
            
            szPeak = int(peak_max) - int(peak_min) + 1
            
            final_y_axis = np.zeros((szPeak, tof_dim))
            final_y_error_axis = np.zeros((szPeak, tof_dim))
            
            for t in range(tof_dim):
                
                # by default, no space for background subtraction below and above peak
                bMinBack = False
                bMaxBack = False
                
                if back_min < peak_min:

                    bMinBack = True
                    _backMinArray = data_y_axis[back_min:peak_min, t]
                    _backMinErrorArray = data_y_error_axis[back_min:peak_min, t]
                    [_backMin, _backMinError] = self.weighted_mean(_backMinArray, 
                                                                   _backMinErrorArray,
                                                                   error_0)
                if peak_max < back_max:
                    
                    bMaxBack = True
                    _backMaxArray = data_y_axis[peak_max+1:back_max+1, t]
                    _backMaxErrorArray = data_y_error_axis[peak_max+1:back_max+1, t]
                    [_backMax, _backMaxError] = self.weighted_mean(_backMaxArray,
                                                                   _backMaxErrorArray,
                                                                   error_0)

                # if no max background use min background only
                if not bMaxBack:
                    background = _backMin
                    background_error = _backMinError
                
                # if no min background use max background only
                if not bMinBack:
                    background = _backMax
                    background_error = _backMaxError
                
                if bMinBack and bMaxBack:
                    [background, background_error] = self.weighted_mean([_backMin, _backMax], 
                                                                        [_backMinError, _backMaxError],
                                                                        error_0)

                # remove background for each pixel of the peak
                for x in range(szPeak):
                    final_y_axis[x,t] = float(data_y_axis[peak_min+x,t]) - float(background)
                    final_y_error_axis[x,t] = float(np.sqrt(pow(data_y_error_axis[peak_min + x, t],2) +
                                                            pow(background_error,2)))
            
        else: # no background
            
            final_y_axis = data_y_axis[peak_min:peak_max+1,:]
            final_y_error_axis = data_y_error_axis[peak_min:peak_max+1,:]
            
        
        self.data_y_axis = final_y_axis
        self.data_y_error_axis = final_y_error_axis


    def weighted_mean(self, data_array, error_array, error_0):
        '''
        weighted mean of an array        
        '''
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
            data_mean = np.NAN
            mean_error = np.NAN
        else:            
            data_mean = float(dataNum) / float(dataDen)
            mean_error = math.sqrt(1/dataDen)     
    
        return [data_mean, mean_error]        


    def populate_data_object(self, main_gui, oConfig, type):
        '''
        will retrieve all the info from the oConfig table and will populate the oData object
        type is either 'data' or 'norm'
        '''
        
        isData = True
        
        # check first if we have a full file name already
        if oConfig is not None:
            if type == 'data':
                full_file_name = oConfig.data_full_file_name
                if full_file_name == u'':
                    _run_number = oConfig.data_sets
                    full_file_name = FileFinder.findRuns("REF_L%d" %int(_run_number))[0]
            else:
                isData = False
                if oConfig.norm_flag:
                    full_file_name = oConfig.norm_full_file_name
                    if full_file_name == u'' or full_file_name == ['']:
                        _run_number = oConfig.norm_sets
                        full_file_name = FileFinder.findRuns("REF_L%d" %int(_run_number))[0]

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
                            isData = isData)
        
            return oData

        return None

class REFLReduction(object):

    # bigTableData = None

    def __init__(cls, main_gui):
        '''
        Initialize the REFL reduction
        '''

        # retrive full data to reduce
        bigTableData = main_gui.bigTableData
        
        # number of reduction process to run
        nbrRow = main_gui.ui.reductionTable.rowCount()
        
        nbrRow = 1 #FIXME
        for row in range(nbrRow):

            dataCell = main_gui.ui.reductionTable.item(row,0).text()
            if main_gui.ui.reductionTable.item(row,6) is not None:
                normCell = main_gui.ui.reductionTable.item(row,6).text()
            else:
                normCell = ''
            
            print 'working with DATA %s and NORM %s' %(dataCell, normCell)
            
            dataObject = bigTableData[row,0]
            normObject = bigTableData[row,1]
            configObject = bigTableData[row,2]
            
            red1 = ReductionObject(main_gui, dataCell, normCell, dataObject, normObject, configObject)
            bigTableData[row,0] = red1.oData
            bigTableData[row,1] = red1.oNorm

            # integrate low res range of data and norm
            red1.integrate_over_low_res_range()
            
            # subtract background
            red1.substract_data_background()
            











        # put back the object created in the bigTable to speed up next preview / load
        main_gui.bigTableData = bigTableData
        
        
        