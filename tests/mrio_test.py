#-*- coding: utf-8 -*-

import os
import unittest
import tempfile

from numpy import float64, float32, loadtxt, array, testing
from quick_nxs.mreduce import NXSData, Reflectivity
from quick_nxs.mrio import HeaderCreator, HeaderParser, Exporter

TEST_DATASET=os.path.join(os.path.dirname(os.path.abspath(__file__)), u'test1_histo.nxs')

class FakeData():
  def setUp(self):
    # create dummy data
    self.ds=NXSData(TEST_DATASET)
    norm=Reflectivity(self.ds[0])
    self.ref1=Reflectivity(self.ds[0], normalization=norm)
    self.ds[0].read_options=dict(self.ds[0].read_options)
    self.ref2=Reflectivity(self.ds[0], normalization=norm, bg_poly_regions=[[(100., 10.),
                                                                          (100., 10.),
                                                                          (100., 10.),
                                                                          (100., 10.)]])

class HeaderTest(FakeData, unittest.TestCase):
  def test_creation(self):
    header=HeaderCreator([self.ref1, self.ref2])
    self.assertTrue(type(header.get_data_header(['a', 'b', 'c'], ['', '', ''])) is unicode)
    ignore=unicode(header)
  
  def test_recreation(self):
    header=HeaderCreator([self.ref1, self.ref2])
    parser=HeaderParser(unicode(header))
    parser.parse()
    prefl=parser.refls[0]
    for key, value in self.ref1.options.items():
      if key=='normalization':
        continue
      if type(value) in (float, float32, float64):
        value=float("%g"%value)
      self.assertEqual(prefl.options[key], value,
                       'Refl option %s %s vs. %s'%(key, prefl.options[key], value))
    prro=prefl.read_options
    for key, value in self.ds[0].read_options.items():
      if type(value) in (float, float32, float64):
        value=float("%g"%value)
      self.assertEqual(prro[key], value, 'Reader option %s %s vs. %s'%(key, prro[key], value))      
    

class ExportTest(FakeData, unittest.TestCase):
  def test_create_data(self):
    exporter=Exporter(self.ds.keys(), [self.ref1, self.ref2])
    exporter.extract_reflectivity()
    exporter.extract_offspecular()
    exporter.extract_offspecular_corr()

  def test_write_all(self):
    exporter=Exporter(self.ds.keys(), [self.ref1, self.ref2])
    exporter.extract_reflectivity()
    expfile=os.path.join(tempfile.gettempdir(), 'testexport.dat')
    exporter.export_data(tempfile.gettempdir(), 'testexport.dat',
                      multi_ascii=True, combined_ascii=True,
                      matlab_data=True, numpy_data=True)
    os.remove(expfile)
     
  def test_write_consistent(self):
    exporter=Exporter(self.ds.keys(), [self.ref1])
    exporter.extract_reflectivity()
    expfile=os.path.join(tempfile.gettempdir(), 'testexport.dat')
    exporter.export_data(tempfile.gettempdir(), 'testexport.dat',
                      multi_ascii=True, combined_ascii=False,
                      matlab_data=False, numpy_data=False)
    tdata=array([self.ref1.Q, self.ref1.R, self.ref1.dR]).transpose()[::-1]
    rdata=loadtxt(expfile)
    self.assertEqual(self.ref1.Q.shape[0], rdata.shape[0])
    testing.assert_allclose(rdata[:, 0], tdata[:, 0], rtol=1e-6, atol=1e-20, verbose=True)
    testing.assert_allclose(rdata[:, 1], tdata[:, 1], rtol=1e-6, atol=1e-20, verbose=True)
    testing.assert_allclose(rdata[:, 2], tdata[:, 2], rtol=1e-6, atol=1e-20, verbose=True)
    os.remove(expfile)

suite=unittest.TestLoader().loadTestsFromTestCase(HeaderTest)
suite.addTest(unittest.TestLoader().loadTestsFromTestCase(ExportTest))
