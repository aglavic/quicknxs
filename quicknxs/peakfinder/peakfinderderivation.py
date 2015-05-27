import numpy as np

class PeakFinderDerivation(object):
    
    peaks = [-1,-1]
    
    def __init__(cls, xdata, ydata, edata, back_offset=3):
        xdata = np.array(xdata)
        ydata = np.array(ydata)
        
    def getPeaks(cls):
        return cls.peaks