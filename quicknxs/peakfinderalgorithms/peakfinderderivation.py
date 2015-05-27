import numpy as np

class PeakFinderDerivation(object):
    
    peaks = [-1,-1]
    xdata_firstderi = []
    ydata_firstderi = []
    edata_firstderi = []
    five_highest_ydata = []
    five_highest_xdata = []
    sum_peak_counts = -1
    sum_peak_counts_time_pixel = -1
    peak_pixel = -1
    
    def __init__(cls, xdata, ydata, edata, back_offset=3):
        cls.initArrays()

        cls.xdata = np.array(xdata)
        cls.ydata = np.array(ydata)
        cls.edata = np.array(edata)
        
        cls.calculate5HighestPoints()
        cls.calculatePeakPixel()
        cls.calculateFirstDerivative()
        
    def initArrays(cls):
        cls.xdata_firstderi = []
        cls.ydata_firstderi = []
        cls.edata_firstderi = []
        cls.peaks = [-1, -1]
        cls.five_highest_ydata = []
        cls.five_highest_xdata = []
        cls.sum_five_highest_ydata = -1
        cls.peak_pixel = -1

    def calculateFirstDerivative(cls):
        xdata = cls.xdata
        ydata = cls.ydata
        
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
        
    def calculate5HighestPoints(cls):
        _xdata = cls.xdata
        _ydata = cls.ydata
        
        _sort_ydata = np.sort(_ydata)
        _decreasing_sort_ydata = _sort_ydata[::-1]
        cls.five_highest_ydata = _decreasing_sort_ydata[0:5]
        
        _sort_index = np.argsort(_ydata)
        _decreasing_sort_index = _sort_index[::-1]
        _5decreasing_sort_index = _decreasing_sort_index[0:5]
        cls.five_highest_xdata = _xdata[_5decreasing_sort_index]
        
    def calculatePeakPixel(cls):    
        cls.sum_peak_counts = sum(cls.five_highest_ydata)
        _sum_peak_counts_time_pixel = -1
        for index,yvalue in enumerate(cls.five_highest_ydata):
            _sum_peak_counts_time_pixel += yvalue * cls.five_highest_xdata[index]
        cls.sum_peak_counts_time_pixel = _sum_peak_counts_time_pixel
        cls.peak_pixel = round(cls.sum_peak_counts_time_pixel / cls.sum_peak_counts)
    
    def getPeakPixel(cls):
        return cls.peak_pixel
        
    def getSumPeakCounts(cls):
        return cls.sum_peak_counts
    
    def getSumPeakCountsTimePixel(cls):
        return cls.sum_peak_counts_time_pixel

    def get5HighestPoints(cls):
        return [cls.five_highest_xdata, cls.five_highest_ydata]
        
    def getFirstDerivative(cls):
        return [cls.xdata_firstderi, cls.ydata_firstderi]
        
    def getPeaks(cls):
        return cls.peaks
    
if __name__ == "__main__":
    from file_loading_utility import loadCsvFile
    [xdata, ydata, edata] = loadCsvFile('easy_data_set.csv')
    peakfinder1 = PeakFinderDerivation(xdata, ydata, edata)
    [high_x, high_y] = peakfinder1.get5HighestPoints()
    