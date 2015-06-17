import unittest
import math
import numpy as np
from quicknxs.isis_calculate_sf import CalculateSF

class Mock:
    """Helper class to instantiate arbitrary objects"""
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

def mockMainGui(rowCount = 0):
    """Mocks the behaviour required from main_gui"""
    return Mock(ui = Mock(reductionTable = Mock(rowCount = lambda: rowCount)))

def mockData(functions):
    """Creates histogram data sets in the given ranges with the given functions

    input: a list of tuples of the form (start, end, f) where start and end
           specify the range of x values to cover, and f is a function from
           x to y

    returns: an np.ndarray of the form expected by CalculateSF, containing
             the histogram data generated from the input values
    """
    data = np.empty((len(functions), 3), dtype=object)
    for i in range(len(functions)):
        (start, end, f) = functions[i]
        data[i,0] = Mock(
            reduce_q_axis = np.asarray(range(start, end+1)),
            reduce_y_axis = np.asarray(map(f, range(start, end))),
            reduce_e_axis = np.zeros(end - start),
            sf_auto = 0.0
            )
    return data

class CalculateSFTest(unittest.TestCase):
    def test_simple(self):
        """scale a straight line"""
        main_gui = mockMainGui(rowCount=2)
        data = mockData([
            (0, 100, lambda x: x),
            (75, 175, lambda x: 2 * x)
            ])
        newData = CalculateSF(data, main_gui).getAutoScaledData()
        self.assertEqual(newData[0,0].sf_auto, 1.0)
        self.assertEqual(newData[1,0].sf_auto, 0.5)

    def test_exponential(self):
        """two identical exponential functions, with a constant offset"""
        main_gui = mockMainGui(rowCount=2)
        data = mockData([
            ( 0, 100, lambda x: 500 - 0.01 * x * x),
            (75, 175, lambda x: 300 - 0.01 * x * x),
            ])
        newData = CalculateSF(data, main_gui).getAutoScaledData()
        self.assertEqual(newData[0,0].sf_auto, 1.0)
        self.assertAlmostEqual(newData[1,0].sf_auto, 1.8937, places=4)

    def test_complex(self):
        """the same function as in test_exp, with with some noise provided by sin"""
        main_gui = mockMainGui(rowCount=2)
        data = mockData([
            ( 0, 100, lambda x: 500 - 0.01 * x * x - 3 * math.sin(x)),
            (75, 175, lambda x: 300 - 0.01 * x * x - 3 * math.sin(x)),
            ])
        newData = CalculateSF(data, main_gui).getAutoScaledData()
        self.assertEqual(newData[0,0].sf_auto, 1.0)
        self.assertAlmostEqual(newData[1,0].sf_auto, 1.8937, places=4)

    def test_triple(self):
        """scale multiple lines to fit"""
        main_gui = mockMainGui(rowCount=3)
        data = mockData([
            (  0, 100, lambda x: x * 3),
            ( 75, 175, lambda x: x * 6),
            (150, 250, lambda x: x * 1),
            ])
        newData = CalculateSF(data, main_gui).getAutoScaledData()
        self.assertEqual(newData[0,0].sf_auto, 1.0)
        self.assertEqual(newData[1,0].sf_auto, 0.5)
        self.assertEqual(newData[2,0].sf_auto, 3.0)

suite=unittest.TestLoader().loadTestsFromTestCase(CalculateSFTest)
