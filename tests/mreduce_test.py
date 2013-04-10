
import os
import unittest
from math import pi
from quick_nxs import mreduce

TEST_DATASET=os.path.join(os.path.dirname(os.path.abspath(__file__)), u'test1_histo.nxs')

class GeneralClassTest(unittest.TestCase):

  def test_wrong_keyword(self):
    # make sure the classes don't accept a wrong keyword argument
    self.assertRaises(ValueError, mreduce.NXSData, '', blabli=12)
    self.assertRaises(ValueError, mreduce.NXSMultiData, [''], blabli=12)
    self.assertRaises(ValueError, mreduce.Reflectivity, None, blabli=12)
    self.assertRaises(ValueError, mreduce.OffSpecular, None, blabli=12)
    self.assertRaises(ValueError, mreduce.GISANS, None, blabli=12)

  def test_no_file(self):
    self.assertTrue(mreduce.NXSData('nonexisting') is None)

  def test_read_file(self):
    obj=mreduce.NXSData(TEST_DATASET)
    self.assertTrue(isinstance(obj, mreduce.NXSData), 'NXS file readout')
    self.assertEqual(obj.origin, TEST_DATASET, 'make sure right file name is saved')
    self._attr_check(obj, 'measurement_type')
    self.assertEqual(len(obj), 1)

  def _attr_check(self, obj, attr, msg=None):
    result=getattr(obj, attr, None)
    self.assertFalse(result is None, msg=msg)

class DataConsistencyChecks(unittest.TestCase):

  def setUp(self):
    self.data=mreduce.NXSData(TEST_DATASET)
    self.assertFalse(self.data is None, 'setting up data object')

  def test_origin(self):
    self.assertEqual(self.data.origin, self.data[0].origin[0])

  def test_options(self):
    self.assertEqual(self.data._options, self.data[0].read_options)

  def test_data_shape(self):
    d=self.data[0]
    x, y, tof=d.x, d.y, d.tof
    self.assertEqual(d.xdata.shape, x.shape)
    self.assertEqual(d.ydata.shape, y.shape)
    self.assertEqual(d.tofdata.shape, tof.shape)

    self.assertEqual(d.xydata.shape, (y.shape[0], x.shape[0]))
    self.assertEqual(d.xtofdata.shape, (x.shape[0], tof.shape[0]))
    self.assertEqual(d.data.shape, (x.shape[0], y.shape[0], tof.shape[0]))

  def test_counts(self):
    d=self.data[0]
    # compare total counts attribute with all three arrays
    self.assertEqual(d.total_counts, d.xydata.sum())
    self.assertEqual(d.total_counts, d.xtofdata.sum())
    self.assertEqual(d.total_counts, d.data.sum())
    # compare sum over full data axes with combined arrays
    self.assertTrue((d.data.sum(axis=1)==d.xtofdata).all())
    self.assertTrue((d.data.sum(axis=2)==d.xydata.transpose()).all())

  def test_properies(self):
    d=self.data[0]

    self.assertTrue(((d.tof_edges[:-1]+d.tof_edges[1:])/2.==d.tof).all())
    v_n=d.dist_mod_det/d.tof*1e6 #m/s
    lamda_n=mreduce.H_OVER_M_NEUTRON/v_n*1e10 #A
    self.assertTrue((lamda_n==d.lamda).all())

  def test_addition(self):
    d=self.data[0]
    d2=d+d
    self.assertEqual(d.total_counts*2, d2.total_counts)
    self.assertTrue((d.data*2==d2.data).all())

  def test_multi(self):
    d=self.data[0]
    d2=mreduce.NXSMultiData([TEST_DATASET])[0]
    self.assertEqual(d.origin, d2.origin)
    self.assertEqual(d.total_counts, d2.total_counts)
    self.assertTrue((d.data==d2.data).all())


class DataReductionTests(unittest.TestCase):
  def setUp(self):
    self.data=mreduce.NXSData(TEST_DATASET)
    self.assertFalse(self.data is None, 'setting up data object')

  def test_1reflectivity(self):
    res=mreduce.Reflectivity(self.data[0])
    self.assertTrue(isinstance(res, mreduce.Reflectivity))

  def test_metadata(self):
    d=self.data[0]
    res=mreduce.Reflectivity(d)
    self.assertEqual(res.read_options, d.read_options)
    self.assertEqual(res.origin, d.origin)
  
  def test_shapes(self):
    res=mreduce.Reflectivity(self.data[0])
    res=mreduce.Reflectivity(self.data[0], normalization=res, tth=0.5, x_pos=206., dpix=206.)
    rshape=len(self.data[0].tof_edges)-1
    # as Q and R are calculated from tof/lamda/I etc., there is no need to test each one
    self.assertEqual(res.Q.shape[0], rshape)
    self.assertEqual(res.R.shape[0], rshape)
    self.assertEqual(res.dR.shape[0], rshape)
    self.assertEqual(res.dQ.shape[0], rshape)

  def test_self_normalization(self):
    res=mreduce.Reflectivity(self.data[0], x_pos=206.)
    res2=mreduce.Reflectivity(self.data[0], x_pos=206., normalization=res, scale=0.5)
    self.assertTrue((res2.R[res.Rraw>0]==0.5).all())

  def test_background(self):
    res=mreduce.Reflectivity(self.data[0], x_pos=206., x_width=10.,
                                            bg_pos=206., bg_width=10.)
    self.assertTrue((res.R==0.).all())
  
  def test_angle_calculation(self):    
    res=mreduce.Reflectivity(self.data[0], x_pos=206., x_width=10.,
                                            bg_pos=206., bg_width=10.,
                                            tth=0., dpix=206.)
    self.assertEqual(res.ai, 0.)
    res=mreduce.Reflectivity(self.data[0], x_pos=206., x_width=10.,
                                            bg_pos=206., bg_width=10.,
                                            tth=1., dpix=206.)
    self.assertEqual(res.ai, 0.5/180.*pi)

  def test_offspec(self):
    res=mreduce.OffSpecular(self.data[0])
    self.assertTrue(isinstance(res, mreduce.Reflectivity))

  def test_gisans(self):
    res=mreduce.GISANS(self.data[0])
    self.assertTrue(isinstance(res, mreduce.Reflectivity))


suite=unittest.TestLoader().loadTestsFromTestCase(GeneralClassTest)
suite.addTest(unittest.TestLoader().loadTestsFromTestCase(DataConsistencyChecks))
suite.addTest(unittest.TestLoader().loadTestsFromTestCase(DataReductionTests))
