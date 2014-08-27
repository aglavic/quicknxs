import math

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

  
def ouput_big_ascii_file(file_name,
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
