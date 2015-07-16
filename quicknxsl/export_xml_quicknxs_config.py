class ExportXMLquickNXSConfig(object):
    
    main_gui = None
    filename = ''
    strArray = []
    
    def __init__(cls, parent=None, filename=''):
        cls.main_gui = parent
        cls.filename = filename
        
        cls.headerPart()
        cls.mainPart()
	cls.saveXML()
        
    def headerPart(cls):
	strArray = cls.strArray
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

	# generator
	strArray.append('<generator>quickNXS</generator>\n')

        # metadata
        strArray.append(' <DataSeries>\n')
        
        cls.strArray = strArray
	
    def mainPart(cls):
	
	strArray = cls.strArray
	self = cls.main_gui
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
                data_low_res_flag = bool(_data.low_res_flag)
                data_lambda_requested = _data.lambda_requested
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
                    data_lambda_requested = _metadata.data_lambda_requested
                    tof = _metadata.tof_range

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
                    data_lambda_requested = -1
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
                norm_lambda_requested = _norm.lambda_requested

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
                    norm_lambda_requested = _metadata.norm_lambda_requested

                else:
                    norm_full_file_name = ''
                    norm_flag = True
                    norm_peak = ['0','0']
                    norm_back = ['0','0']
                    norm_back_flag = True
                    norm_low_res = ['0','0']
                    norm_low_res_flag = True
                    norm_lambda_requested = -1

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
            strArray.append('   <data_lambda_requested>' + str(data_lambda_requested) + '</data_lambda_requested>\n')

            strArray.append('   <norm_flag>' + str(norm_flag) + '</norm_flag>\n')
            strArray.append('   <norm_x_range_flag>' + str(norm_low_res_flag) + '</norm_x_range_flag>\n')
            strArray.append('   <norm_x_max>' + str(norm_low_res[1]) + '</norm_x_max>\n')
            strArray.append('   <norm_x_min>' + str(norm_low_res[0]) + '</norm_x_min>\n')
            strArray.append('   <norm_from_peak_pixels>' + str(norm_peak[0]) + '</norm_from_peak_pixels>\n')
            strArray.append('   <norm_to_peak_pixels>' + str(norm_peak[1]) + '</norm_to_peak_pixels>\n')
            strArray.append('   <norm_background_flag>' + str(norm_back_flag) + '</norm_background_flag>\n')
            strArray.append('   <norm_from_back_pixels>' + str(norm_back[0]) + '</norm_from_back_pixels>\n')
            strArray.append('   <norm_to_back_pixels>' + str(norm_back[1]) + '</norm_to_back_pixels>\n')
            strArray.append('   <norm_lambda_requested>' + str(norm_lambda_requested) + '</norm_lambda_requested>\n')

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
            _exportStitchingAsciiSettings = self.exportStitchingAsciiSettings
            _overlap_lowest_error = _exportStitchingAsciiSettings.use_lowest_error_value_flag
            strArray.append('   <overlap_lowest_error>' + str(_overlap_lowest_error) + '</overlap_lowest_error>\n')

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
            fcFlag = _exportStitchingAsciiSettings.fourth_column_flag
            strArray.append('   <fourth_column_flag>' + str(fcFlag) + '</fourth_column_flag>\n')

            fcdq0 = _exportStitchingAsciiSettings.fourth_column_dq0
            strArray.append('   <fourth_column_dq0>' + str(fcdq0) + '</fourth_column_dq0>\n')

            fcdqoverq = _exportStitchingAsciiSettings.fourth_column_dq_over_q
            strArray.append('   <fourth_column_dq_over_q>' + str(fcdqoverq) + '</fourth_column_dq_over_q>\n')

            useAutoPeakBackSelectionFlag = self.ui.actionAutomaticPeakFinder.isChecked()
            strArray.append('   <auto_peak_back_selection_flag>' + str(useAutoPeakBackSelectionFlag) + '</auto_peak_back_selection_flag>\n')
            autoBackSelectionWidth = self.ui.autoBackSelectionWidth.text()
            strArray.append('   <auto_peak_back_selection_width>' + str(autoBackSelectionWidth) + '</auto_peak_back_selection_width>\n')
            useAutoTofRangeFinderFlag = self.ui.autoTofFlag.isChecked()
            strArray.append('   <auto_tof_range_flag>' + str(useAutoTofRangeFinderFlag) + '</auto_tof_range_flag>\n')

            strArray.append('  </RefLData>\n')

        strArray.append('  </DataSeries>\n')
        strArray.append('</Reduction>\n')
	cls.strArray = strArray

    def saveXML(cls):
	filename = cls.filename
	strArray = cls.strArray
	
        # write out XML file
        f = open(filename, 'w')
        f.writelines(strArray)
        f.close()
	