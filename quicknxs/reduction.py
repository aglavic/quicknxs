from mantid.simpleapi import *
from .qreduce import NXSData
import logbook
import numpy as np
import math
import os
import constants
import utilities
from qreduce import LRDataset

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
    
    # normalized data (data / normalization file)
    normalized_data = []
    normalized_data_error = []
    
    # scaled data (after normalization)
    scaled_normalized_data = []
    scaled_normalized_data_error = []
    
    # after conversion of axis from TOF to Q
    scaled_normalized_data_reverse = []
    scaled_normalized_data_error_reverse = []
    q_axis = []
    
    q_workspace = None
    
    main_gui = None
    
    sf_auto_found_match = False
    
    final_q_axis = []
    final_y_axis = []
    final_e_axis = []
    
    def __init__(self, main_gui, dataCell, normCell, oData, oNorm, oConfig):
        '''
        Initialize the reduction object by 
        setting data and normalization files
        '''
        self.main_gui = main_gui
        
        self.dataCell = dataCell
        self.normCell = normCell
        
        self.oConfig = oConfig

        self.logbook('Initialize reduction objects (data and norm)')

        # if the oData is empty, retrieve info from oConfig
        if oData is None:
            self.logbook('-> data: oData is None => we need to retrieve it from config object')
            oData = self.populate_data_object(main_gui, oConfig, 'data')
        self.oData = oData
        
        # retrieve norm if user wants norm and if normCell is not empty
        if normCell != '':
            self.logbook('-> normCell is not empty: %s'% normCell)
            if oNorm is None:
                self.logbook('--> oNorm is None')
                # make sure the norm flag is on in the config file
                if oConfig.norm_flag:
                    self.logbook('---> yes, we want to use normalization file')
                    oNorm = self.populate_data_object(main_gui, oConfig, 'norm')
                else:
                    self.logbook('---> no, we do not want to use normalization file')
            else: # make sure the flag is ON         
                self.logbook('--> oNorm exist')
                if not(oNorm.active_data.use_it_flag):
                    self.logbook('---> no, we do not want to use normalization file')
                    oNorm = None
                else:
                    self.logbook('---> yes, we want to use normalization file')
                                    
        self.oNorm = oNorm

    def cleanup(self):
        '''
        cleaning data
        '''

        self.logbook('-> cleaning up data (error>data or data<1e-12) ... PROCESSING')

        q_axis = self.final_q_axis
        y_axis = self.final_y_axis
        e_axis = self.final_e_axis
        
        nbr_q = np.shape(q_axis)[0]
        
        for q in range(nbr_q):
            
            _data = y_axis[q]
            _error = e_axis[q]
            
            if abs(_error) >= abs(_data):
                
                _data_tmp = 0
                _error_tmp = 1
                
            elif (_data < 1e-12):
                
                _data_tmp = 0
                _error_tmp = 1
                
            else:
                
                _data_tmp = _data
                _error_tmp = _error
                
            y_axis[q] = _data_tmp
            e_axis[q] = _error_tmp
            
        
        # remove first and last point
        new_q_axis = q_axis[1:]
        new_y_axis = y_axis[1:]
        new_e_axis = e_axis[1:]
        
        self.final_q_axis = new_q_axis
        self.final_y_axis = new_y_axis
        self.final_e_axis = new_e_axis

        self.logbook('-> cleaning up data (error>data or data<1e-12) ... DONE', False)


    def create_q_workspace(self):
        '''
        create the Q workspace that will be used to rebin the Q according to the parameters defined
        by the user
        '''
        self.logbook('-> create Q workspace ... PROCESSING')
        
        data = self.scaled_normalized_data_reverse
        error = self.scaled_normalized_data_error_reverse
        q_axis = self.q_axis
        
        [nbr_pixel, nbr_q] = np.shape(q_axis)
        
        q_axis_1d = q_axis.flatten()
        data_1d = data.flatten()
        error_1d = error.flatten()
        
        q_workspace = CreateWorkspace(DataX = q_axis_1d,
                                      DataY = data_1d,
                                      DataE = error_1d,
                                      Nspec = nbr_pixel,
                                      UnitX = "Wavelength")
        q_workspace.setDistribution(True)
        self.q_workspace = q_workspace

        self.logbook('-> create Q workspace ... DONE', False)
        
    def rebin_q_workspace(self):
        '''
        rebin q_workspace using binning paramter defined in main GUI
        '''
        
        self.logbook('-> rebin q_workspace:')
        q_range = self.oData.active_data.q_range
        q_bin = self.main_gui.ui.qStep.text()
        self.logbook('--> from q: %s' % q_range[0])
        self.logbook('-->   to q: %s' % q_range[1])
        self.logbook('-->    bin: %s' % q_bin)
        
        q_parameters = [float(q_range[0]), -float(q_bin), float(q_range[1])]
        q_workspace = Rebin(InputWorkspace=self.q_workspace,
                                 Params=q_parameters,
                                 PreserveEvents = True)
        
        self.q_workspace = q_workspace
        
        self.logbook('-> rebin q_workspace ... DONE')

    def mean_peak(self):    
        '''
        getting the mean value of the peak
        '''
        
        self.logbook('-> calculate mean of peak ... PROCESSING')
        wks = self.q_workspace
        
        final_x_axis = wks.readX(0)[:]
        nbr_q = np.shape(final_x_axis)[0]
        
        nbr_pixel = int(self.oData.active_data.peak[1]) - int(self.oData.active_data.peak[0]) + 1

        big_y = np.zeros((nbr_pixel, nbr_q-1))
        big_e = np.zeros((nbr_pixel, nbr_q-1))
        
        for x in range(nbr_pixel):
            
            _tmp_y = wks.readY(x)[:]
            big_y[x,:] = _tmp_y
            
            _tmp_e = wks.readE(x)[:]
            big_e[x,:] = _tmp_e

        final_y = np.zeros(nbr_q)
        final_e = np.zeros(nbr_q)
        
        for q in range(nbr_q-1):
            
            _tmp_y = big_y[:,q]
            _tmp_y_error = big_e[:,q]
            
            [_y, _y_error] = self.sum_with_error(_tmp_y, _tmp_y_error)
            
            final_y[q] = _y
            final_e[q] = _y_error

        self.final_q_axis = final_x_axis
        self.final_y_axis = final_y
        self.final_e_axis = final_e
    
        self.logbook('-> calculate mean of peak ... DONE', False)
    
    def rebin(self):
        '''
        rebin the data and normalization according to parameters defined
        '''
        self.logbook('-> rebin DATA ... PROCESSING')

        data = self.oData.active_data
        nxs = data.nxs
        
        tof_range = data.tof_range
        if data.tof_units == 'ms':
            tof_range[0] = float(tof_range[0])*1000
            tof_range[1] = float(tof_range[1])*1000
        
        tof_bin = float(self.main_gui.ui.eventTofBins.text())
        
        rebin_params = [float(tof_range[0]), tof_bin, float(tof_range[1])]
        self.logbook('--> from TOF : \t' + str(tof_range[0]) + ' microS')
        self.logbook('-->   to TOF : \t' + str(tof_range[1]) + ' microS')
        self.logbook('-->  TOF bin : \t' + str(tof_bin) + ' microS')

        nxs_histo = Rebin(InputWorkspace=nxs, Params=rebin_params, PreserveEvents=True)
        nxs_histo = NormaliseByCurrent(InputWorkspace=nxs_histo)

        [_tof_axis, Ixyt, Exyt] = LRDataset.getIxyt(nxs_histo, data.new_detector_geometry_flag)

        data.tof_axis = _tof_axis
        data.Ixyt = Ixyt
        data.Exyt = Exyt
        self.oData.active_data = data

        self.logbook('-> rebin DATA ... DONE')

        if self.oNorm is not None:
            
            self.logbook('-> rebin NORMALIZATION ... PROCESSING')

            norm = self.oNorm.active_data
            norm_nxs = norm.nxs
            
            norm_nxs_histo = Rebin(InputWorkspace=norm_nxs, Params=rebin_params, PreserveEvents=True)
            norm_nxs_histo = NormaliseByCurrent(InputWorkspace=norm_nxs_histo)
            
            [_tof_axis, Ixyt, Exyt] = LRDataset.getIxyt(norm_nxs_histo, norm.new_detector_geometry_flag)
            
            norm.tof_axis = _tof_axis
            norm.Ixyt = Ixyt
            norm.Exyt = Exyt
            self.oNorm.active_data = norm
            
            self.logbook('-> rebin NORMALIZATION ... DONE')

    def convert_to_Q(self):
        '''
        function convert to Q data
        '''
        
        self.logbook('-> Convert to Q')
        
        if self.main_gui.ui.geometryCorrectionFlag.isChecked():
#            convert_to_Q_with_geometry_correction()
            self.logbook('--> With geometry correction')
        else:
            self.logbook('--> Without geometry correction --- PROCESSING')
            self.convert_to_Q_no_geometry_correction()

    def convert_to_Q_no_geometry_correction(self):
        '''
        No geometry correction
        Will convert the tof axis into a Q axis using Q range specified
        '''
        
        _const = 4. * math.pi * constants.mn * self.oData.active_data.dMD / constants.h
        theta = self.oData.active_data.theta
        _q_axis = 1e-10 * _const * math.sin(self.oData.active_data.theta) / (self.oData.active_data.tof_axis * 1e-6)

        nbr_q = len(_q_axis)
        
        [nbr_pixel, nbr_tof] = np.shape(self.scaled_normalized_data)
        
        q_axis_2d = np.zeros((nbr_pixel, nbr_q))
        for p in range(nbr_pixel):
            q_axis_2d[p,:] = _q_axis
            
        q_axis_2d = np.fliplr(q_axis_2d)
        scaled_normalized_data_reverse = np.fliplr(self.scaled_normalized_data)
        scaled_normalized_data_error_reverse = np.fliplr(self.scaled_normalized_data_error)
        
        self.q_axis = q_axis_2d
        self.scaled_normalized_data_reverse = scaled_normalized_data_reverse
        self.scaled_normalized_data_error_reverse = scaled_normalized_data_error_reverse
        
        self.logbook('--> Without geometry correction --- DONE', False)

        ## DEBUGGING
        #utilities.output_big_Q_ascii_file('/mnt/hgfs/j35/Matlab/compareMantidquickNXS/data/quicknxs_after_conversion_to_q_without_SF.txt',
                                          #q_axis_2d,
                                          #scaled_normalized_data_reverse,
                                          #scaled_normalized_data_error_reverse)
        

    def logbook(self, text, appendFlag=True):
        if appendFlag:
            self.main_gui.ui.logbook.append(text)
        else:
            self.main_gui.ui.logbook.undo()
            self.main_gui.ui.logbook.append(text)

    def apply_scaling_factor(self):
        '''
        This function will apply the scaling factor of the scaling factor file (.txt)
        which has been created by the sfCalculator program
        '''
        
        self.logbook('-> Apply scaling factor')
        main_gui = self.main_gui
        
        self.scaled_normalized_data = self.normalized_data
        self.scaled_normalized_data_error = self.normalized_data_error
        
        if not main_gui.ui.scalingFactorFlag.isChecked():
            self.logbook('--> User do not want scaling factor!')
            self.scaled_normalized_data = self.normalized_data
            self.scaled_normalized_data_error = self.normalized_data_error
            return
        
        sf_full_file_name = main_gui.ui.scalingFactorFile.text()
        self.logbook('--> scaling factor file: ' + sf_full_file_name)
        if os.path.isfile(sf_full_file_name):
            self.logbook('---> scaling factor file FOUND!')
            
            # parse file and put info into an array
            sfFactorTable = self.parse_scaling_factor_file(sf_full_file_name)
            [nbr_row, nbr_column] = np.shape(sfFactorTable)
            self.logbook('---> File has ' + str(nbr_row) + ' incident media listed')
            
            # incident medium selected
            _incident_medium = main_gui.ui.selectIncidentMediumList.currentText().strip()
            self.logbook('---> incident medium: ' + _incident_medium)
            
            # get lambda requested
            _lambda_requested = self.oData.active_data.lambda_requested
            self.logbook('---> lambda requested: ' + str(_lambda_requested) + ' lambda')

            # retrieve slits parameters
            s1h_value = abs(self.oData.active_data.S1H)
            s1w_value = abs(self.oData.active_data.S1W)
            if self.oData.active_data.isSiThere:
                si2h_value = abs(self.oData.active_data.SiH)
                si2w_value = abs(self.oData.active_data.SiW)
            else:
                si2h_value = abs(self.oData.active_data.S2H)
                si2w_value = abs(self.oData.active_data.S2W)
                
            self.logbook('---> s1h: ' + str(s1h_value))
            self.logbook('---> s1w: ' + str(s1w_value))
            if self.oData.active_data.isSiThere:
                self.logbook('---> sih: ' + str(si2h_value))
                self.logbook('---> siw: ' + str(si2w_value))
            else:
                self.logbook('---> s2h: ' + str(si2h_value))
                self.logbook('---> s2w: ' + str(si2w_value))
            
            # precision requested
            value_precision = float(self.main_gui.ui.sfPrecision.text())
            
            self.logbook('---> looping through all media listed in file:')
            for i in range(nbr_row):
                
                _file_incident_medium = self.get_table_field_value(sfFactorTable, i, 0)
                if (_file_incident_medium.strip() == _incident_medium.strip()):

                    # check that lambda requested match
                    _file_lambda_requested = self.get_table_field_value(sfFactorTable, i, 1)
                    if (self.is_within_precision_range(_file_lambda_requested, 
                                                       _lambda_requested,
                                                       value_precision)):
                        
                        # check that s1h match
                        _file_s1h = self.get_table_field_value(sfFactorTable, i, 2)
                        if (self.is_within_precision_range(_file_s1h,
                                                           s1h_value,
                                                           value_precision)):
                            
                            # check that si2h match
                            _file_si2h = self.get_table_field_value(sfFactorTable, i, 3)
                            if (self.is_within_precision_range(_file_si2h,
                                                               si2h_value,
                                                               value_precision)):
            
                                if self.main_gui.ui.scalingFactorSlitsWidthFlag.isChecked():

                                    # check that s1w match
                                    _file_s1w = self.get_table_field_value(sfFactorTable, i, 4)
                                    if (self.is_within_precision_range(_file_s1w,
                                                                       s1w_value,
                                                                       value_precision)):
                
                                        # check that si2w match
                                        _file_si2w = self.get_table_field_value(sfFactorTable, i, 5)
                                        if (self.is_within_precision_range(_file_si2w,
                                                                           si2w_value,
                                                                           value_precision)):
                
                                            self.logbook('----> Perfect Match (with slits width checked): FOUND !')
                                            self.sf_auto_found_match = True
                                            
                                            # retrieve parameters
                                            a = float(self.get_table_field_value(sfFactorTable, i, 6))
                                            b = float(self.get_table_field_value(sfFactorTable, i, 7))
                                            a_error = float(self.get_table_field_value(sfFactorTable, i, 8))
                                            b_error = float(self.get_table_field_value(sfFactorTable, i, 9))
                                            
                                            self.apply_scaling_factor_to_data(a, b, a_error, b_error)
                                            return
                                        
                                else: # we do not want width precision
                                    
                                    self.logbook('----> Perfect Match (without slits width checked): FOUND !')
                                    self.sf_auto_found_match = True
                                    
                                    # retrieve parameters
                                    a = float(self.get_table_field_value(sfFactorTable, i, 6))
                                    b = float(self.get_table_field_value(sfFactorTable, i, 7))
                                    a_error = float(self.get_table_field_value(sfFactorTable, i, 8))
                                    b_error = float(self.get_table_field_value(sfFactorTable, i, 9))
                                    
                                    self.apply_scaling_factor_to_data(a, b, a_error, b_error)
                                    return
                            
                            else: # no si2h match
                                
                                self.logbook('----> Perfect Match: NOT FOUND !')
                                    
            
            self.logbook('---> Perfect Match:  NOT FOUND !')
        
        

    def apply_scaling_factor_to_data(self, a, b, a_error, b_error):
        '''
        This function will create for each x-axis value, the corresponding
        scaling factor using the formula y=a+bx
        '''
        tof_axis = self.oData.active_data.tof_axis
        nbr_tof = len(tof_axis)
        
        x_axis_factor = np.zeros(nbr_tof)
        x_axis_factor_error = np.zeros(nbr_tof)
        
        _scaled_normalized_data = self.normalized_data
        _scaled_normalized_data_error = self.normalized_data_error
        
        for i in range(nbr_tof):
            
            _x_value = float(tof_axis[i])
            _factor = _x_value * b + a
            x_axis_factor[i] = _factor
            _factor_error = _x_value * b_error + a_error
            x_axis_factor_error[i] = _factor_error
            
        [nbr_pixel, nbr_tof] = np.shape(_scaled_normalized_data)
        
        scaled_normalized_data = np.zeros((nbr_pixel, nbr_tof))
        scaled_normalized_data_error = np.zeros((nbr_pixel, nbr_tof))
        
        for x in range(nbr_pixel):
            
            [ratio_array, ratio_array_error] = self.divide_arrays(_scaled_normalized_data[x,:],
                                                                  _scaled_normalized_data_error[x,:],
                                                                  x_axis_factor,
                                                                  x_axis_factor_error)
            
            scaled_normalized_data[x,:] = ratio_array[:]
            scaled_normalized_data_error[x,:] = ratio_array_error[:]
        
        self.scaled_normalized_data = scaled_normalized_data
        self.scaled_normalized_data_error = scaled_normalized_data_error


    def divide_arrays(self, num_array, num_array_error, den_array, den_array_error):
        '''
        This function calculates the ratio of two arrays and calculate the respective error values
        '''

        nbr_elements = np.shape(num_array)[0]
        
        # calculate the ratio array
        ratio_array = np.zeros(nbr_elements)
        for i in range(nbr_elements):
            if den_array[i] is 0:
                _tmp_ratio = 0
            else:
                _tmp_ratio = num_array[i] / den_array[i]
            ratio_array[i] = _tmp_ratio
            
        # calculate the error of the ratio array
        ratio_error_array = np.zeros(nbr_elements)
        for i in range(nbr_elements):
            
            if (num_array[i] == 0) or (den_array[i] == 0): 
                ratio_error_array[i] = 0 
            else:
                tmp1 = pow(num_array_error[i] / num_array[i],2)
                tmp2 = pow(den_array_error[i] / den_array[i],2)
                ratio_error_array[i] = math.sqrt(tmp1+tmp2)*(num_array[i]/den_array[i])
    
        return [ratio_array, ratio_error_array]        


    def is_within_precision_range(self, value1, value2, precision):
        diff = abs(float(value2))-abs(float(value1))
        if abs(diff) <= precision:
            return True
        else:
            return False
        

    def get_table_field_value(self, table, row, column):
        _tag_value = table[row][column]
        _tag_value_split = _tag_value.split('=')
        return _tag_value_split[1]

    def parse_scaling_factor_file(self, sf_full_file_name):
        '''
        will parse the scaling factor file
        '''
        f = open(sf_full_file_name,'r')
        sfFactorTable = []
        for line in f.read().split('\n'):
            if (len(line) > 0) and (line[0] != '#'):
                sfFactorTable.append(line.split(' '))
        f.close()
        return sfFactorTable        
        
    def integrate_over_low_res_range(self):
        '''
        This will integrate over the low resolution range of the data and norm objects
        '''
        self.logbook('-> integrate_over_low_res_range ... PROCESSING')

        data = self.oData.active_data       
#        print 'data: '
#        print '-> data_low_res_flag: %s' %data.data_low_res_flag
        if data.low_res_flag:
            from_pixel = int(data.low_res[0])
            to_pixel = int(data.low_res[1])
        else:
            from_pixel = int(data.low_resolution_range[0])
            to_pixel = int(data.low_resolution_range[1])
        
        self.logbook('--> from pixel: ' + str(from_pixel))
        self.logbook('--> to pixel: ' + str(to_pixel))
        
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

        # work with Normalization
        if self.oNorm is not None:
            norm = self.oNorm.active_data
        
            if norm.low_res_flag:
                from_pixel = int(norm.low_res[0])
                to_pixel = int(norm.low_res[1])
            else:
                from_pixel = int(norm.low_resolution_range[0])
                to_pixel = int(norm.low_resolution_range[1])
        
            Ixyt = norm.Ixyt   # for example [303,255,471]
            Exyt = norm.Exyt
        
            # calculate y axis
            Ixyt_crop = Ixyt[from_pixel:to_pixel+1,:,:]
            self.norm_y_axis = Ixyt_crop.sum(axis=0)
            
            # calculate error axis
            Exyt_crop = Exyt[from_pixel:to_pixel+1,:,:]
            Exyt_crop_sq = Exyt_crop * Exyt_crop
            _y_error_axis = Exyt_crop_sq.sum(axis=0)
            self.norm_y_error_axis = np.sqrt(_y_error_axis)

        self.logbook('-> integrate_over_low_res_range ... DONE !')

    def get_error_0counts(self, data):
        '''
        return the default error value when error of data is 0
        '''
        _proton_charge_nxs = data.proton_charge / 3.6
        return 1./float(_proton_charge_nxs)


    def substract_background(self):
        '''
        Substract background of data and normalization
        '''
        
        self.logbook('-> substract background ... PROCESSING')
        
        # work with data ===========
        data_y_axis = self.data_y_axis
        data_y_error_axis = self.data_y_error_axis
        
        # retrieve data peak range
        data = self.oData.active_data       
        peak = data.peak
        back = data.back
        back_flag = data.back_flag
        
        [final_y_axis, final_y_error_axis] = self.substract_data_background(peak, back,
                                                                            data,
                                                                            data_y_axis,
                                                                            data_y_error_axis,
                                                                            back_flag)
        self.data_y_axis = final_y_axis
        self.data_y_error_axis = final_y_error_axis
                
        
        # work with normalizaton =========

        # we don't have a norm object
        if self.oNorm is None:
            return
        
        # we don't want to use the normalization file
        if not self.oNorm.active_data.use_it_flag:
            return
        
        norm_y_axis = self.norm_y_axis
        norm_y_error_axis = self.norm_y_error_axis
        
        # retrieve data peak range
        norm = self.oNorm.active_data       
        peak = norm.peak
        back = norm.back
        back_flag = norm.back_flag
        
        [final_y_axis, final_y_error_axis] = self.substract_data_background(peak, back,
                                                                            norm,
                                                                            norm_y_axis,
                                                                            norm_y_error_axis,
                                                                            back_flag)

        # integrate norm data 2D -> 1D
        [final_y_axis_integrated, final_y_error_axis_integrated] = self.full_sum_with_error(final_y_axis,
                                                                                            final_y_error_axis)
        
        self.norm_y_axis = final_y_axis_integrated
        self.norm_y_error_axis = final_y_error_axis_integrated

        ## DEBUGGING
        #data_tof_axis = self.oNorm.active_data.tof_axis
        #utilities.output_ascii_file('/mnt/hgfs/j35/Matlab/compareMantidquickNXS/data/quicknxs_data_divided_by_norm_integrated.txt',
                                         #data_tof_axis,
                                         #final_y_axis_integrated,
                                         #final_y_error_axis_integrated)
        
        self.logbook('-> substract background ... DONE!', False)

    def data_over_normalization(self):
        '''
        Divide data by normalization
        '''
        
        self.logbook('-> data_over_normalization .... PROCESSING')

        norm = self.oNorm
        if norm is None:
            self.logbook('-> data_over_normalization .... DONE! (no normalization file)', False)
            return
        
        data = self.data_y_axis
        data_error = self.data_y_error_axis
        
        norm = self.norm_y_axis
        norm_error = self.norm_y_error_axis
        
        # get size of data
        [nbr_pixel, nbr_tof] = np.shape(data)

        normalized_data = np.zeros((nbr_pixel, nbr_tof))
        normalized_data_error = np.zeros((nbr_pixel, nbr_tof))
        
        for t in range(nbr_tof):

            if (norm[t] != 0):
                tmp_error2 = pow(float(norm_error[t]) / float(norm[t]),2)
    
                for x in range(nbr_pixel):
    
                    if (norm[t] != 0) and (data[x,t] != 0):
                        
                        tmp_value = float(data[x,t]) / float(norm[t])
                        
                        tmp_error1 = pow(float(data_error[x,t]) / float(data[x,t]),2)
                        tmp_error = math.sqrt(tmp_error1 + tmp_error2) * abs(float(data[x,t]) / float(norm[t]))
                        
                        normalized_data[x,t] = tmp_value
                        normalized_data_error[x,t] = tmp_error
                    
        self.normalized_data = normalized_data
        self.normalized_data_error = normalized_data_error

        ## DEBUGGING
        #data_tof_axis = self.oData.active_data.tof_axis
        #utilities.ouput_big_ascii_file('/mnt/hgfs/j35/Matlab/compareMantidquickNXS/data/quicknxs_data_divided_by_norm_not_integrated.txt',
                                         #data_tof_axis,
                                         #normalized_data,
                                         #normalized_data_error)

        self.logbook('-> data_over_normalization .... DONE!', False)

    def full_sum_with_error(self, data, error):
        '''
        Integrate data with error
        '''

        [nbr_pixel, nbr_tof] = np.shape(data)
        
        final_data = np.zeros(nbr_tof)
        final_error = np.zeros(nbr_tof)
        
        for t in range(nbr_tof):
            [tmp_data, tmp_error] = self.sum_with_error(data[:,t], error[:,t])

            final_data[t] = tmp_data
            final_error[t] = tmp_error

        return [final_data, final_error]


    def sum_with_error(self, data, error):
        
        sum_value = sum(data)
        
        tmp_sum_error = 0
        for i in range(len(data)):
            tmp_value = pow(error[i],2)
            tmp_sum_error += tmp_value
        
        sum_error = math.sqrt(tmp_sum_error)
        
        return [sum_value, sum_error]


    def substract_data_background(self, peak, back, data, data_y_axis, data_y_error_axis, back_flag):
        '''
        substract background of data and norm
        '''
        
        peak_min = int(peak[0])
        peak_max = int(peak[1])
        back_min = int(back[0])
        back_max = int(back[1])

        if back_flag:

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
        
        return [final_y_axis, final_y_error_axis]


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


    def histogram_q_axis(self):
        '''
        will take the center of each bin and will output this new array
        '''

        qaxis = self.oData.reduce_q_axis
        sz = np.size(qaxis)
        new_qaxis = np.zeros(sz-1)
        for i in range(sz-1):
            _left = qaxis[i]
            _right = qaxis[i+1]
            _center = (_left+_right)/2.
            new_qaxis[i] = _center
            
        return new_qaxis


    def populate_data_object(self, main_gui, oConfig, type):
        '''
        will retrieve all the info from the oConfig table and will populate the oData object
        type is either 'data' or 'norm'
        '''
        
        is_data = True
        
        # check first if we have a full file name already
        if oConfig is not None:
            if type == 'data':
                full_file_name = oConfig.data_full_file_name
                if full_file_name == u'' or full_file_name == [''] :
                    _run_number = oConfig.data_sets
                    full_file_name = FileFinder.findRuns("REF_L%d" %int(_run_number))[0]
            else:
                is_data = False
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
                            is_data = is_data)
        
            return oData

        return None

class REFLReduction(object):

    main_gui = None

    def logbook(cls, text):
        # add log book message
        cls.main_gui.ui.logbook.append(text)

    def __init__(cls, main_gui):
        '''
        Initialize the REFL reduction
        '''

        cls.main_gui = main_gui
        cls.logbook('Running data reduction ...')
        cls.logbook('')

        # retrive full data to reduce
        bigTableData = main_gui.bigTableData
        
        # number of reduction process to run
        nbrRow = main_gui.ui.reductionTable.rowCount()
        
        for row in range(nbrRow):

            dataCell = main_gui.ui.reductionTable.item(row,0).text()
            if main_gui.ui.reductionTable.item(row,6) is not None:
                normCell = main_gui.ui.reductionTable.item(row,6).text()
            else:
                normCell = ''
            
            cls.logbook('Working with DATA: %s and NORM: %s' %(dataCell, normCell))
            
            dataObject = bigTableData[row,0]
            normObject = bigTableData[row,1]
            configObject = bigTableData[row,2]
            
            red1 = ReductionObject(main_gui, dataCell, normCell, dataObject, normObject, configObject)
            bigTableData[row,0] = red1.oData
            bigTableData[row,1] = red1.oNorm
    
            # rebin 
            red1.rebin()
            
            # integrate low res range of data and norm
            red1.integrate_over_low_res_range()
            
            # subtract background
            red1.substract_background()
            
            # data / normalization 
            red1.data_over_normalization()
    
            # apply scaling factor
            red1.apply_scaling_factor()
    
            # convert to Q
            red1.convert_to_Q()
    
            # create workspace
            red1.create_q_workspace()
    
            # rebin Q workspace
            red1.rebin_q_workspace()
    
            # integrate spectra 
            red1.mean_peak()
            
            # cleanup data
            red1.cleanup()
            
            # save data back into bigTableData
            red1.oData.reduce_q_axis = red1.final_q_axis.copy()
            red1.oData.reduce_y_axis = red1.final_y_axis.copy()
            red1.oData.reduce_e_axis = red1.final_e_axis.copy()
            red1.oData.sf_auto_found_match = red1.sf_auto_found_match
            
            # align data with center of Q axis
            red1.oData.q_axis_for_display = red1.histogram_q_axis()
            final_y_axis = red1.final_y_axis.copy()
            final_e_axis = red1.final_e_axis.copy()
            red1.oData.y_axis_for_display = final_y_axis[:-1]
            red1.oData.e_axis_for_display = final_e_axis[:-1]

            
            ## DEBUGGING
            #utilities.output_ascii_file('/mnt/hgfs/j35/Matlab/compareMantidquickNXS/data/quicknxs_after_final_cleaning.txt',
                                        #red1.final_q_axis,
                                        #red1.final_y_axis,
                                        #red1.final_e_axis)

            bigTableData[row,0] = red1.oData
            
            cls.logbook('')

        # put back the object created in the bigTable to speed up next preview / load
        main_gui.bigTableData = bigTableData
        
        cls.logbook('data reduction ... DONE !')
        cls.logbook('================================================')
