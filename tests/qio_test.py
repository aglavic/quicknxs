#-*- coding: utf-8 -*-

import os, sys
import unittest
import tempfile

from numpy import float64, float32, loadtxt, array, testing
from quicknxs.qreduce import NXSData, Reflectivity
from quicknxs.qio import HeaderCreator, HeaderParser, Exporter

TEST_DATASET=os.path.join(os.path.dirname(os.path.abspath(__file__)), u'test1_histo.nxs')
TEST_EVENT=os.path.join(os.path.dirname(os.path.abspath(__file__)), u'test1_event.nxs')

class FakeData():
  def setUp(self):
    # create dummy data
    self.ds=NXSData(TEST_DATASET)
    norm=Reflectivity(self.ds[0])
    norm2=Reflectivity(self.ds[0], bg_poly_regions=[[(1., 10.),
                                                    (1.1, 10.),
                                                    (1.1, 30.),
                                                    (1., 30.)]])
    self.ref1=Reflectivity(self.ds[0], normalization=norm)
    self.ds[0].read_options=dict(self.ds[0].read_options)
    self.ref2=Reflectivity(self.ds[0], normalization=norm2, bg_poly_regions=[[(1., 10.),
                                                                            (4., 10.),
                                                                            (4., 30.),
                                                                            (1., 30.)]])

class HeaderTest(FakeData, unittest.TestCase):
  def test_creation(self):
    header=HeaderCreator([self.ref1, self.ref2])
    self.assertTrue(type(header.get_data_header(['a', 'b', 'c'], ['', '', ''])) is unicode)
    ignore=unicode(header)

  def test_creation_event(self):
    ds=NXSData(TEST_EVENT)
    ref=Reflectivity(ds[0])
    ref2=Reflectivity(ds[0], normalization=ref)
    header=HeaderCreator([ref2, self.ref1, self.ref2])
    self.assertTrue(type(header.get_data_header(['a', 'b', 'c'], ['', '', ''])) is unicode)
    ignore=unicode(header)

  def test_recreation(self):
    header=HeaderCreator([self.ref1, self.ref2])
    parser=HeaderParser(unicode(header), parse_meta=False)
    self._process=None
    parser.parse(callback=self._cb_test)
    self.assertFalse(self._process is None)
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

  def test_recreation_event(self):
    ds=NXSData(TEST_EVENT)
    ref=Reflectivity(ds[0])
    ref2=Reflectivity(ds[0], normalization=ref)
    header=HeaderCreator([ref2, self.ref1, self.ref2])
    parser=HeaderParser(unicode(header), parse_meta=False)
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

  def _cb_test(self, process):
    self._process=process


class ExportTest(FakeData, unittest.TestCase):
  def test_create_data(self):
    exporter=Exporter(self.ds.keys(), [self.ref1, self.ref2])
    exporter.extract_reflectivity()
    exporter.extract_offspecular()
    exporter.extract_offspecular_corr()
    exporter.smooth_offspec({
                           'grid': (20, 20),
                           'sigma': (3., 3.),
                           'sigmas': 3.,
                           'region': (10, 90, 5 , 95),
                           'xy_column': 0,
                           })
    exporter.smooth_offspec({
                           'grid': (20, 20),
                           'sigma': (3., 3.),
                           'sigmas': 3.,
                           'region': (10, 90, 5 , 95),
                           'xy_column': 1,
                           })
    exporter.smooth_offspec({
                           'grid': (20, 20),
                           'sigma': (3., 3.),
                           'sigmas': 3.,
                           'region': (10, 90, 5 , 95),
                           'xy_column': 2,
                           })

  def test_write_all(self):
    exporter=Exporter(self.ds.keys(), [self.ref1, self.ref2])
    exporter.extract_reflectivity()
    exporter.extract_offspecular()
    expfile=os.path.join(tempfile.gettempdir(), 'testexport.dat')
    exporter.export_data(tempfile.gettempdir(), 'testexport.dat',
                      multi_ascii=True, combined_ascii=True,
                      matlab_data=True, numpy_data=True)
    exporter.create_gnuplot_scripts(tempfile.gettempdir(), 'testexport.dat')
    exporter.create_genx_file(tempfile.gettempdir(), 'testexport.dat')
    os.remove(expfile)

  def test_write_consistent(self):
    exporter=Exporter([self.ds.keys()[0]], [self.ref1])
    exporter.extract_reflectivity()
    expfile=os.path.join(tempfile.gettempdir(), 'testexport.dat')
    exporter.export_data(tempfile.gettempdir(), 'testexport.dat',
                      multi_ascii=True, combined_ascii=False,
                      matlab_data=False, numpy_data=False)
    tdata=array([self.ref1.Q, self.ref1.R, self.ref1.dR]).transpose()
    if sys.version_info[0]>=3:
      rdata=loadtxt(open(expfile, 'rb'))
    else:
      rdata=loadtxt(expfile)
    self.assertEqual(self.ref1.Q.shape[0], rdata.shape[0])
    testing.assert_allclose(rdata[:, 0], tdata[:, 0], rtol=1e-6, atol=1e-20, verbose=True)
    testing.assert_allclose(rdata[:, 1], tdata[:, 1], rtol=1e-6, atol=1e-20, verbose=True)
    testing.assert_allclose(rdata[:, 2], tdata[:, 2], rtol=1e-6, atol=1e-20, verbose=True)
    os.remove(expfile)

suite=unittest.TestLoader().loadTestsFromTestCase(HeaderTest)
suite.addTest(unittest.TestLoader().loadTestsFromTestCase(ExportTest))
