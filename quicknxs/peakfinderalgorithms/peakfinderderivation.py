import numpy as np

class PeakFinderDerivation(object):
    
    peaks = [-1,-1]
    xdata_firstderi = []
    ydata_firstderi = []
    edata_firstderi = []
    
    def __init__(cls, xdata, ydata, edata, back_offset=3):
        cls.xdata_firstderi = []
        cls.ydata_firstderi = []
        cls.edata_firstderi = []
        cls.peaks = [-1, -1]

        xdata = np.array(xdata)
        ydata = np.array(ydata)
        edata = np.array(edata)
        
        cls.calculateFirstDerivative(xdata, ydata, edata)
        
    def calculateFirstDerivative(cls, xdata, ydata, edata):
        _xdata_firstderi = []
        _ydata_firstderi = []
        for i in range(len(xdata)-1):
            _left_x = xdata[i]
            _right_x = xdata[i+1]
            _xdata_firstderi.append(np.mean([_left_x, _right_x]))
            
            _left_y = ydata[i]
            _right_y = ydata[i+1]
            _ydata_firstderi.append((_right_y - _left_y)/(_right_x - _left_x))
        
        cls.xdata_firstderi = _xdata_firstderi
        cls.ydata_firstderi = _ydata_firstderi
    
    def getFirstDerivative(cls):
        return [cls.xdata_firstderi, cls.ydata_firstderi]
        
    def getPeaks(cls):
        return cls.peaks