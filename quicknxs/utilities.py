import math
import os
import numpy as np

def convert_angle (angle=0, from_units='degree', to_units='rad'):
    '''
    To convert angles from degree/rad to rad/degree
    '''
    
    if from_units == to_units:
        return angle
    
    if from_units == 'degree' and to_units == 'rad':
        coeff = math.pi / float(180)
    elif from_units == 'rad' and to_units == 'degree':
        coeff = float(180) / math.pi
    else:
        coeff = 1

    return float(angle) * coeff

  
def output_big_ascii_file(file_name,
                         x_axis,
                         y_axis,
                         y_error_axis):

    f=open(file_name,'w')

    sz = y_axis.shape # (nbr_pixel, nbr_tof)
    nbr_tof = sz[1]
    nbr_pixel = sz[0]

    for t in range(nbr_tof):
        _tmp_str = str(x_axis[t])
        for x in range(nbr_pixel):
            _tmp_str += ' ,' + str(y_axis[x,t]) + " ," + str(y_error_axis[x,t])

        _tmp_str += '\n'
        f.write(_tmp_str)

    f.close

def output_ascii_file(file_name,
                      x_axis,
                      y_axis,
                      y_error_axis):
    
    f=open(file_name,'w')

    sz_x_axis = len(x_axis)
    for i in range(sz_x_axis-1):
        f.write(str(x_axis[i]) + "," + str(y_axis[i]) + "," + str(y_error_axis[i]) + "\n");

    f.close
    
    
def output_big_Q_ascii_file(file_name,
                            x_axis,
                            y_axis,
                            y_error_axis):
    
    f=open(file_name,'w')
    
    sz = y_axis.shape # (nbr_pixel, nbr_tof)
    nbr_tof = sz[1]
    nbr_pixel = sz[0]
    
    for t in range(nbr_tof):
        _tmp_str = ''
        for x in range(nbr_pixel):
            _tmp_str += str(x_axis[x,t]) +  ',' + str(y_axis[x,t]) + " ," + str(y_error_axis[x,t]) + ',,'
        _tmp_str += '\n'
        f.write(_tmp_str)
   
    f.close
        

def createPickleFilename(filename):
    '''
    will create the new pickeFilename based on the filename given
    (new extension but same base file name)
    '''
    
    filename, fileExtension = os.path.splitext(filename)
    new_fileExtension = '_quicknx.dat'
    new_filename = filename +  new_fileExtension
    return new_filename

    
def weighted_mean(data_array, error_array):
    '''
    weighted mean of an array        
    '''
    sz = len(data_array)

    # calculate the numerator of mean
    dataNum = 0;
    for i in range(sz):
        if not (data_array[i] == 0):
            tmpFactor = float(data_array[i]) / float((pow(error_array[i],2)))
            dataNum += tmpFactor

    # calculate denominator
    dataDen = 0;
    for i in range(sz):
        if not (error_array[i] == 0):
            tmpFactor = 1./float((pow(error_array[i],2)))
            dataDen += tmpFactor

    if dataDen == 0:
        mean = 0
        mean_error = 0
    else:
        mean = float(dataNum) / float(dataDen)
        mean_error = math.sqrt(1/dataDen)

    return [mean, mean_error]


def write_ascii_file(filename, text):
    '''
    produce the output ascii file
    '''    
    f = open(filename, 'w')
    for _line in text:
        f.write(_line + '\n')
    f.close()


def weighted_sum(dataArray, errorArray, axisToSum=0):

    inputDim = len(dataArray.shape)

    if inputDim == 2:
        [sumArray, errorArray] = weighted_sum_dim2(dataArray, errorArray, axisToSum)
        return [sumArray, errorArray]
    elif inputDim == 3:
        [sumArray, errorArray] = weighted_sum_dim3(dataArray, errorArray, axisToSum)
        return [sumArray, errorArray]
    else: # dim = 1
        [sumValue, errorValue] = weighted_sum_dim1(dataArray, errorArray)
        return [sumValue, errorValue]

    
def weighted_sum_dim3(dataArray, errorArray, axisToSum=0):
    
    _shapeArray = dataArray.shape
    _nbrElementAxis0 = _shapeArray[0]
    _nbrElementAxis1 = _shapeArray[1]
    _nbrElementAxis2 = _shapeArray[2]
    
    if axisToSum == 0:
        
        sumValueArray = np.zeros((_nbrElementAxis1, _nbrElementAxis2))
        sumErrorArray = np.zeros((_nbrElementAxis1, _nbrElementAxis2))
        
        for j in range(_nbrElementAxis2):
            
            [_value, _error] = weighted_sum_dim2(dataArray[:,:,j], errorArray[:,:,j], axisToSum)
            sumValueArray[:,j] = _value
            sumErrorArray[:,j] = _error
    
    elif axisToSum == 1:
        
        sumValueArray = np.zeros((_nbrElementAxis0, _nbrElementAxis2))
        sumErrorArray = np.zeros((_nbrElementAxis0, _nbrElementAxis2))
        
        for j in range(_nbrElementAxis0):
            
            [_value, _error] = weighted_sum_dim2(dataArray[j,:,:], errorArray[j,:,:], axisToSum-1)
            sumValueArray[j,:] = _value
            sumValueArray[j,:] = _value
            
    else: # axisToSum == 2
    
        sumValueArray = np.zeros((_nbrElementAxis0, _nbrElementAxis1))
        sumErrorArray = np.zeros((_nbrElementAxis0, _nbrElementAxis1))
        
        for j in range(_nbrElementAxis0):
            
            [_value, _error] = weighted_sum_dim2(dataArray[j,:,:], errorArray[j,:,:], axisToSum-1)
            sumValueArray[j,:] = _value
            sumValueArray[j,:] = _value
        
    return [sumValueArray, sumErrorArray]
    
    
def weighted_sum_dim2(dataArray, errorArray, axisToSum=0):
    
    _shapeArray = dataArray.shape
    _nbrElementAxis0 = _shapeArray[0]
    _nbrElementAxis1 = _shapeArray[1]

    if axisToSum == 0:
        
        sumValueArray = np.zeros(_nbrElementAxis1)
        sumErrorArray = np.zeros(_nbrElementAxis1)
        
        for i in range(_nbrElementAxis1):
            [_value, _error] = weighted_sum_dim1(dataArray[:,i], errorArray[:,i])
            sumValueArray[i] = _value
            sumErrorArray[i] = _error
            
    else:
        
        sumValueArray = np.zeros(_nbrElementAxis0)
        sumErrorArray = np.zeros(_nbrElementAxis0)
        
        for i in range(_nbrElementAxis0):
            [_value, _error] = weighted_sum_dim1(dataArray[i,:], errorArray[i,:])
            sumValueArray[i] = _value
            sumErrorArray[i] = _error
        
    return [sumValueArray, sumErrorArray]
    
    
def weighted_sum_dim1(dataArray, errorArray):
    
    _sumValue = sum(dataArray)
    
    sz = len(dataArray)
    _tmpSumError = 0
    for i in range(sz):
        _tmpError = pow(errorArray[i],2)
        _tmpSumError += _tmpError
        
    _sumError = math.sqrt(_tmpSumError)
    
    return [_sumValue, _sumError]


    
    
    