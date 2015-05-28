import numpy as np
import math

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
    deri_min = 1
    deri_max = -1
    deri_min_pixel_value = -1
    deri_max_pixel_value = -1
    mean_counts_firstderi = -1
    std_deviation_counts_firstderi = -1
    peak_max_final_value = -1
    peak_min_final_value = -1
    
    def __init__(cls, xdata, ydata, edata=[], back_offset=3):
        cls.initArrays()

        cls.xdata = np.array(xdata)
        cls.ydata = np.array(ydata)
        cls.edata = np.array(edata)
        
        cls.calculate5HighestPoints() #step2
        cls.calculatePeakPixel() #step3

        cls.calculateFirstDerivative() #step4
        cls.calculateMinMaxDerivativePixels() #step5
        cls.calculateAvgAndStdDerivative() #step6
        cls.calculateMinMaxSignalPixel() #step7
        
    def initArrays(cls):
        cls.xdata_firstderi = []
        cls.ydata_firstderi = []
        cls.edata_firstderi = []
        cls.peaks = [-1, -1]
        cls.five_highest_ydata = []
        cls.five_highest_xdata = []
        cls.sum_five_highest_ydata = -1
        cls.peak_pixel = -1
        cls.deri_min = 1
        cls.deri_max = -1
        cls.deri_min_pixel_value = -1
        cls.deri_max_pixel_value = -1
        cls.mean_counts_firstderi = -1
        cls.std_deviation_counts_firstderi = -1
        cls.peak_max_final_value = -1
        cls.peak_min_final_value = -1

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
        
    def calculateMinMaxDerivativePixels(cls):
        _pixel = cls.xdata_firstderi
        _counts_firstderi = cls.ydata_firstderi
        
        _sort_counts_firstderi = np.sort(_counts_firstderi)
        cls.deri_min = _sort_counts_firstderi[0]
        cls.deri_max = _sort_counts_firstderi[-1]
        
        _sort_index = np.argsort(_counts_firstderi)
        cls.deri_min_pixel_value = min([_pixel[_sort_index[0]], _pixel[_sort_index[-1]]])
        cls.deri_max_pixel_value = max([_pixel[_sort_index[0]], _pixel[_sort_index[-1]]])
        
    def calculateAvgAndStdDerivative(cls):
        _counts_firstderi = np.array(cls.ydata_firstderi)
        cls.mean_counts_firstderi = np.mean(_counts_firstderi)
        _mean_counts_firstderi = np.mean(_counts_firstderi * _counts_firstderi)
        cls.std_deviation_counts_firstderi = math.sqrt(_mean_counts_firstderi)

    def calculateMinMaxSignalPixel(cls):
        _counts = cls.ydata_firstderi
        _pixel = cls.xdata_firstderi

        _deri_min_pixel_value = cls.deri_min_pixel_value
        _deri_max_pixel_value = cls.deri_max_pixel_value

        _std_deviation_counts_firstderi = cls.std_deviation_counts_firstderi

        px_offset = 0
        while abs(_counts[int(_deri_min_pixel_value - px_offset)]) > _std_deviation_counts_firstderi:
            px_offset += 1
        _peak_min_final_value = _pixel[int(_deri_min_pixel_value - px_offset)]
            
        px_offset = 0
        while abs(_counts[int(round(_deri_max_pixel_value + px_offset))]) > _std_deviation_counts_firstderi:
            px_offset += 1
        _peak_max_final_value = _pixel[int(round(_deri_max_pixel_value + px_offset))]
        
        cls.peaks = [int(_peak_min_final_value), np.ceil(_peak_max_final_value)]

    # getters

    def getAverageOfFirstDerivationCounts(cls):
        return cls.mean_counts_firstderi

    def getStdDeviationOfFirstDerivationCounts(cls):
        return cls.std_deviation_counts_firstderi

    def getMinDerivativeValue(cls):
        return cls.deri_min
    
    def getMaxDerivativeValue(cls):
        return cls.deri_max

    def getMinDerivationPixelValue(cls):
        return cls.deri_min_pixel_value
    
    def getMaxDerivationPixelValue(cls):
        return cls.deri_max_pixel_value
    
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
    