#-*- coding: utf-8 -*-

import unittest
from numpy import *
from quick_nxs.mrcalc import refine_gauss, get_scaling, get_xpos, get_yregion, get_total_reflection
from quick_nxs.mreduce import MRDataset, Reflectivity

class FitTest(unittest.TestCase):
  def setUp(self):
    self.x=linspace(-10, 10, 501)
    self.y=1e4*exp(-0.5*(self.x/2.)**2) # gaussian with sigma 2

  def test_absolute(self):
    # testing the absolute results
    res=refine_gauss(self.y, 200, 40, return_params=True)
    self.assertAlmostEqual(res[0], 1e4, places=10)
    self.assertAlmostEqual(res[1], 250., places=10)
    self.assertAlmostEqual(res[2], 50., places=10)

  def test_left_right(self):
    # testing different starting conditions far left and far right
    res1=refine_gauss(self.y, 50, 50, return_params=True)
    res2=refine_gauss(self.y, 450, 50, return_params=True)
    self.assertAlmostEqual(res1[0], res2[0], msg='I left vs. right', places=10)
    self.assertAlmostEqual(res1[1], res2[1], msg='x0 left vs. right', places=10)
    self.assertAlmostEqual(res1[2], res2[2], msg='sigma left vs. right', places=10)

class FakeData():
  def setUp(self):
    # create dummy data
    self.ds=MRDataset()
    self.ds.tof_edges=linspace(10000., 25000., 40)
    tof=(self.ds.tof_edges[1:]+self.ds.tof_edges[:-1])/2.
    self.ds.proton_charge=1e13
    self.ds.data=ones((304, 256, 39))*(tof[newaxis, newaxis, :])
    self.ds.data[:4]=0.
    self.ds.data[180:211]*=10.
    self.ds.data[:, :80]=0.
    self.ds.data[:,-80:]=0.
    self.ds.xydata=self.ds.data.sum(axis=2).transpose()
    self.ds.read_options=None
    # create two dummi reflectivities
    self.ref1=Reflectivity(self.ds, x_pos=200, dpix=210, tth=0., bg_pos=2, bg_width=4)
    self.ref2=Reflectivity(self.ds, x_pos=190, dpix=210, tth=0., bg_pos=2, bg_width=4)

class StitchTest(FakeData, unittest.TestCase):
  def test_linear(self):
    yscale, ignore, ignore=get_scaling(self.ref2, self.ref1, polynom=2)
    self.assertAlmostEqual(yscale, 1., places=4)
    self.ref2.R/=2
    yscale, ignore, ignore=get_scaling(self.ref2, self.ref1, polynom=2)
    self.assertAlmostEqual(yscale, 2., places=4)

  def test_degrees(self):
    yscale, ignore, ignore=get_scaling(self.ref2, self.ref1, polynom=2)
    for i in range(3, 8):
      yscale2, ignore, ignore=get_scaling(self.ref2, self.ref1, polynom=i)
      self.assertAlmostEqual(yscale, yscale2, places=3)
  
  def test_totref(self):
    self.ref1.R[20:]=100.
    self.ref1.R[:20]=0.1
    self.ref1.dR=ones_like(self.ref1.R)
    scale, npoints=get_total_reflection(self.ref1, return_npoints=True)
    self.assertEqual(scale, 1./100.)
    self.assertEqual(npoints, 20)

class PositionTest(FakeData, unittest.TestCase):
  def test_xpos(self):
    self.ds.dpix=220.
    self.ds.dangle=self.ds.dangle0
    self.ds.sangle=0.5
    self.ds.xydata[:, 180:211]+=50*exp(-0.5*((arange(31)-15.)/2.)**2)
    x_pos=get_xpos(self.ds)
    self.assertAlmostEqual(x_pos, 195., places=8)
  
  def test_ypos(self):
    y_pos, y_width, bg=get_yregion(self.ds)
    self.assertEqual(y_pos, 128.)
    self.assertEqual(y_width, 96.)
    self.assertEqual(bg, 0.)

suite=unittest.TestLoader().loadTestsFromTestCase(FitTest)
suite.addTest(unittest.TestLoader().loadTestsFromTestCase(StitchTest))
suite.addTest(unittest.TestLoader().loadTestsFromTestCase(PositionTest))
