import unittest
from peakfinderderivation import PeakFinderDerivation
from file_loading_utility import loadCsvFile

class TestPeakFinderDerivation(unittest.TestCase):
    
    def setUp(self):
        pass

    def test_loadcsvfile_xaxis(self):
        '''Step1 - Loading: checking that loadCsvFile works correctly on xaxis'''
        [xdata, ydata, edata] = loadCsvFile('peakfinderalgorithms/easy_data_set.csv')
        xdata10 = xdata[0:10]
        self.assertEqual(xdata10, [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0])
    
    def test_loadcsvfile_yaxis(self):
        '''Step1 - Loading: checking that loadCsvFile works correctly on yaxis'''
        [xdata, ydata, edata] = loadCsvFile('peakfinderalgorithms/easy_data_set.csv')
        ydata10 = ydata[0:10]
        self.assertEqual(ydata10, [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 4.0, 5.0])

    def test_loadcsvfile_eaxis(self):
        '''Step1 - Loading: checking that loadCsvFile works correctly on eaxis'''
        [xdata, ydata, edata] = loadCsvFile('peakfinderalgorithms/easy_data_set.csv')
        edata10 = edata[0:10]
        self.assertEqual(edata10, [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 2.0, 2.236067977])

    def test_get5HighestPoints_xdata(self):
        '''Step2 - 5highest points: using run 125682 to check calculation of 5 highest points - xdata '''
        [xdata, ydata, edata] = loadCsvFile('peakfinderalgorithms/easy_data_set.csv')
        peakfinder1 = PeakFinderDerivation(xdata, ydata, edata)
        [high_x, high_y] = peakfinder1.get5HighestPoints()
        high_x = high_x.tolist()
        self.assertEqual(high_x, [155., 156., 154., 157., 153.])
        
    def test_get5HighestPoints_ydata(self):
        '''Step2 - 5highest points: using run 125682 to check calculation of 5 highest points - ydata '''
        [xdata, ydata, edata] = loadCsvFile('peakfinderalgorithms/easy_data_set.csv')
        peakfinder1 = PeakFinderDerivation(xdata, ydata, edata)
        [high_x, high_y] = peakfinder1.get5HighestPoints()
        high_y = high_y.tolist()
        self.assertEqual(high_y, [32351., 28999., 19351., 9503., 2796.])

    def test_calculatefirstderivative_xaxis(self):
        '''Step3 - derivative: testing the first derivative calculation - axis x'''
        [xdata, ydata, edata] = loadCsvFile('peakfinderalgorithms/easy_data_set.csv')
        peakfinder = PeakFinderDerivation(xdata, ydata, edata)
        [xdata_first, ydata_first] = peakfinder.getFirstDerivative()
        xdata10= xdata_first[0:10]
        self.assertEqual(xdata10, [0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5, 9.5])
    
    def test_calculatefirstderivative_yaxis(self):
        '''Step3 - derivative: testing the first derivative calculation - axis y'''
        [xdata, ydata, edata] = loadCsvFile('peakfinderalgorithms/easy_data_set.csv')
        peakfinder = PeakFinderDerivation(xdata, ydata, edata)
        [xdata_first, ydata_first] = peakfinder.getFirstDerivative()
        ydata10= ydata_first[0:10]
        self.assertEqual(ydata10, [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 4.0, 1.0, -1.0])


    #def test_case_easy_data_set(self):
        #'''using run 125682'''
        #[xdata, ydata, edata] = loadCsvFile('peakfinderalgorithms/easy_data_set.csv')
        #peakfinder1 = PeakFinderDerivation(xdata, ydata, edata)
        #peaks = peakfinder1.getPeaks()
        #self.assertEqual(peaks, [151, 159])
    
    #def test_case_medium_data_set(self):
        #'''using run 124211'''
        #[xdata, ydata, edata] = loadCsvFile('peakfinderalgorithms/medium_data_set.csv')
        #peakfinder1 = PeakFinderDerivation(xdata, ydata, edata)
        #peaks = peakfinder1.getPeaks()
        #self.assertEqual(peaks, [151, 159])
    
    #def test_case_hard_data_set(self):
        #'''using run 124135'''
        #[xdata, ydata, edata] = loadCsvFile('peakfinderalgorithms/hard_data_set.csv')
        #peakfinder1 = PeakFinderDerivation(xdata, ydata, edata)
        #peaks = peakfinder1.getPeaks()
        #self.assertEqual(peaks, [145,164])

    
if __name__ == '__main__':
    unittest.main()