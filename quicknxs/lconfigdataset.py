class LConfigDataset(object):
    '''
    This class will be used when loading an XML configuration file and will
    keep record of all the information loaded, such as peak, back, TOF range...
    until the data/norm file has been loaded
    '''
    proton_charge = -1

    data_sets = ''
    data_full_file_name = ''
    data_peak = ['0','0']
    data_back = ['0','0']
    data_low_res = ['50','200']
    data_back_flag = True
    data_low_res_flag = True
    data_lambda_requested = -1

    tof_range = ['0','0'] 
    tof_units = 'ms'
    tof_auto_flag = True

    norm_sets = ''
    norm_full_file_name = ''
    norm_flag = True
    norm_peak = ['0','0']
    norm_back = ['0','0']
    norm_back_flag = True
    norm_low_res = ['50','200']
    norm_low_res_flag = True
    norm_lambda_requested = -1

    q_range =['0','0']
    lambda_range = ['0','0']

    reduce_q_axis = []
    reduce_y_axis = []
    reduce_e_axis = []
    sf_auto = 1 # auto scaling calculated by program
    sf_auto_found_match = False 
    sf_manual = 1 # manual scaling defined by user
    sf = 1 #scaling factor apply to data (will be either the auto, manual or 1)

    q_axis_for_display = []
    y_axis_for_display = []
    e_axis_for_display = []

    # use in the auto SF class
    tmp_y_axis = []
    tmp_e_axis = []