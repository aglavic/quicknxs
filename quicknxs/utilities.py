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

    
    