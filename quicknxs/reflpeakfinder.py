import numpy as np

class ReflPeakFinder(object):
    
    peak_max = [-1,-1]
    
    def __init__(cls, xdata, ydata, resolution=4):
        xdata = np.array(xdata)
        ydata = np.array(ydata)
        
        index_max_value = np.argmax(ydata)
        cls.peak_max[0] = index_max_value - resolution
        cls.peak_max[1] = index_max_value + resolution
        
    def getPeaks(cls):
        return [cls.peak_max]