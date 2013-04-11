#-*- coding: utf-8 -*-

import unittest
from numpy import *
from quick_nxs.mrcalc import refine_gauss, get_scaling
from quick_nxs.mreduce import MRDataset, Reflectivity

class FitTest(unittest.TestCase):
  def setUp(self):
    self.x=linspace(-10, 10, 500)
    self.y=1e4*exp(-0.5*(self.x/2.)**2) # gaussian with sigma 2
    self.y+=sqrt(self.y)*random.randn(500) # put some errors on the data

  def test_absolute(self):
    # testing the absolute results
    res=refine_gauss(self.y, 200, 200, return_params=True)
    self.assertAlmostEqual(res[0], 1e4, msg='I', delta=50.)
    self.assertAlmostEqual(res[1], 249.5, msg='x0', delta=1.)
    self.assertAlmostEqual(res[2], 249.5, msg='sigma', delta=1.)

  def test_left_right(self):
    # testing different starting conditions far left and far right
    res1=refine_gauss(self.y, 50, 200, return_params=True)
    res2=refine_gauss(self.y, 450, 200, return_params=True)
    self.assertAlmostEqual(res1[0], res2[0], msg='I left vs. right', places=5)
    self.assertAlmostEqual(res1[1], res2[1], msg='x0 left vs. right', places=5)
    self.assertAlmostEqual(res1[2], res2[2], msg='sigma left vs. right', places=5)


class StitchTest(unittest.TestCase):
  def setUp(self):
    # create dummy data
    ds=MRDataset()
    ds.tof_edges=linspace(10000., 25000., 40)
    tof=(ds.tof_edges[1:]+ds.tof_edges[:-1])/2.
    # the data arrays
    ds.proton_charge=1e13
    ds.data=ones((304, 256, 39))*(tof[newaxis, newaxis, :])
    ds.data[:4]=0.
    ds.xydata=ds.data.sum(axis=2)
    ds.read_options=None
    self.ref1=Reflectivity(ds, x_pos=200, dpix=210, tth=0., bg_pos=2, bg_width=4)
    self.ref2=Reflectivity(ds, x_pos=190, dpix=210, tth=0., bg_pos=2, bg_width=4)

  def test_linear(self):
    yscale, ignore, ignore=get_scaling(self.ref2, self.ref1, polynom=2)
    self.assertAlmostEqual(yscale, 1., delta=0.0001)
    self.ref2.R/=2
    yscale, ignore, ignore=get_scaling(self.ref2, self.ref1, polynom=2)
    self.assertAlmostEqual(yscale, 2., delta=0.0001)

  def test_degrees(self):
    yscale, ignore, ignore=get_scaling(self.ref2, self.ref1, polynom=2)
    for i in range(3, 8):
      yscale2, ignore, ignore=get_scaling(self.ref2, self.ref1, polynom=i)
      self.assertAlmostEqual(yscale, yscale2, places=3)

suite=unittest.TestLoader().loadTestsFromTestCase(FitTest)
suite.addTest(unittest.TestLoader().loadTestsFromTestCase(StitchTest))
