from PyQt4 import QtGui, QtCore
from numpy import empty
from xml.dom import minidom
from qreduce import NXSData
from distutils.util import strtobool
from logging import info
import nexus_utilities

class ImportXMLquickNXSConfig(object):
    
    def __init__(cls, parent=None, filename=''):
        self = parent
        
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
                    _first_file_name = nexus_utilities.findNeXusFullPath(int(_data_sets))         #FIXME           
                else:
                    _first_file_name = _first_file_name.split(',')

                # load general settings for first row only
                scaling_factor_file = self.getNodeValue(node, 'scaling_factor_file')
                self.ui.scalingFactorFile.setText(scaling_factor_file)
                scaling_factor_flag = self.getNodeValue(node, 'scaling_factor_flag')
                self.ui.scalingFactorFlag.setChecked(strtobool(scaling_factor_flag))
                self.useScalingFactorConfigCheckBox(strtobool(scaling_factor_flag))
                slits_width_flag = self.getNodeValue(node, 'slits_width_flag')
                self.ui.scalingFactorSlitsWidthFlag.setChecked(strtobool(slits_width_flag))
                incident_medium_list = self.getNodeValue(node, 'incident_medium_list')
                im_list = incident_medium_list.split(',')
                self.ui.selectIncidentMediumList.clear()
                self.ui.selectIncidentMediumList.addItems(im_list)
                incident_medium_index_selected = self.getNodeValue(node, 'incident_medium_index_selected')
                self.ui.selectIncidentMediumList.setCurrentIndex(int(incident_medium_index_selected))

                try:
                    useAutoPeakBackSelectionFlag = strtobool(self.getNodeValue(node,'auto_peak_back_selection_flag'))
                    autoBackSelectionWidth = int(self.getNodeValue(node, 'auto_peak_back_selection_width'))
                    useAutoTofRangeFinderFlag = strtobool(self.getNodeValue(node,'auto_tof_range_flag'))
                except:
                    useAutoPeakBackSelectionFlag = True
                    autoBackSelectionWidth = 4
                    useAutoTofRangeFinderFlag = True
                self.ui.actionAutomaticPeakFinder.setChecked(useAutoPeakBackSelectionFlag)
                self.useAutoPeakBackSelectionCheckBox(useAutoPeakBackSelectionFlag)
                self.ui.autoBackSelectionWidth.setValue(autoBackSelectionWidth)
                self.ui.autoTofFlag.setChecked(useAutoTofRangeFinderFlag)

                _exportStitchingAsciiSettings = self.exportStitchingAsciiSettings
                fourth_column_flag = self.getNodeValue(node, 'fourth_column_flag')
                _exportStitchingAsciiSettings.fourth_column_flag = fourth_column_flag
                fourth_column_dq0 = self.getNodeValue(node, 'fourth_column_dq0')
                _exportStitchingAsciiSettings.fourth_column_dq0 = fourth_column_dq0
                fourth_column_dq_over_q = self.getNodeValue(node, 'fourth_column_dq_over_q')
                _exportStitchingAsciiSettings.fourth_column_dq_over_q = fourth_column_dq_over_q
                self.exportStitchingAsciiSettings = _exportStitchingAsciiSettings

                _useGeometryCorrection = self.getNodeValue(node,'geometry_correction_switch')
                self.useGeometryCorrectionCheckBox(strtobool(_useGeometryCorrection))
                self.ui.geometryCorrectionFlag.setChecked(strtobool(_useGeometryCorrection))
                _angle_offset = self.getNodeValue(node,'angle_offset')
                self.ui.angleOffsetValue.setText(_angle_offset)
                _angle_offset_error = self.getNodeValue(node,'angle_offset_error')
                self.ui.angleOffsetError.setText(_angle_offset_error)

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

            # data 
            _data_sets = self.getNodeValue(node,'data_sets')
	    _isOk = self.isPeakBackSelectionOkFromConfig(_metadataObject, type='data')
            self.addItemToBigTable(_data_sets, _row, 0, isCheckOk=True, isOk=_isOk)

            # norm
            _norm_sets = self.getNodeValue(node,'norm_dataset')
	    _isOk = self.isPeakBackSelectionOkFromConfig(_metadataObject, type='norm')
            self.addItemToBigTable(_norm_sets, _row, 6, isCheckOk=True, isOk=_isOk)

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
        