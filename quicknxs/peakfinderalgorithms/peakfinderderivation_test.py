import unittest
from peakfinderderivation import PeakFinderDerivation
from file_loading_utility import loadCsvFile

class TestPeakFinderDerivation(unittest.TestCase):
    
    def setUp(self):
        pass

    def test_loadcsvfile_xaxis(self):
        '''checking that loadCsvFile works correctly on xaxis'''
        [xdata, ydata, edata] = loadCsvFile('peakfinderalgorithms/easy_data_set.csv')
        xdata10 = xdata[0:10]
        self.assertEqual(xdata10, [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0])
    
    def test_calculatefirstderivative_xaxis(self):
        '''testing the first derivative calculation - axis x'''
        [xdata, ydata, edata] = loadCsvFile('peakfinderalgorithms/easy_data_set.csv')
        peakfinder = PeakFinderDerivation(xdata, ydata, edata)
        [xdata_first, ydata_first] = peakfinder.getFirstDerivative()
        xdata10= xdata_first[0:10]
        self.assertEqual(xdata10, [0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5, 9.5])
    
    def test_calculatefirstderivative_yaxis(self):
        '''testing the first derivative calculation - axis y'''
        [xdata, ydata, edata] = loadCsvFile('peakfinderalgorithms/easy_data_set.csv')
        peakfinder = PeakFinderDerivation(xdata, ydata, edata)
        [xdata_first, ydata_first] = peakfinder.getFirstDerivative()
        ydata10= ydata_first[0:10]
        self.assertEqual(ydata10, [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 4.0, 1.0, -1.0])

    def test_case_easy_data_set(self):
        '''using run 125682'''
        [xdata, ydata, edata] = loadCsvFile('peakfinderalgorithms/easy_data_set.csv')
        peakfinder1 = PeakFinderDerivation(xdata, ydata, edata)
        peaks = peakfinder1.getPeaks()
        self.assertEqual(peaks, [151, 159])
    
    def test_case_medium_data_set(self):
        '''using run 124211'''
        [xdata, ydata, edata] = loadCsvFile('peakfinderalgorithms/medium_data_set.csv')
        peakfinder1 = PeakFinderDerivation(xdata, ydata, edata)
        peaks = peakfinder1.getPeaks()
        self.assertEqual(peaks, [151, 159])
    
    def test_case_hard_data_set(self):
        '''using run 124135'''
        [xdata, ydata, edata] = loadCsvFile('peakfinderalgorithms/hard_data_set.csv')
        peakfinder1 = PeakFinderDerivation(xdata, ydata, edata)
        peaks = peakfinder1.getPeaks()
        self.assertEqual(peaks, [145,164])

if __name__ == '__main__':
    unittest.main()