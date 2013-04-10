#-*- coding: utf-8 -*-

import os
import unittest
from time import sleep
from PyQt4.QtGui import QApplication, QMainWindow
from PyQt4.QtTest import QTest
from PyQt4.QtCore import QLocale#, Qt

from quick_nxs.main_gui import MainGUI
from quick_nxs.mreduce import NXSData, Reflectivity

dot=QLocale().decimalPoint()

TEST_DATASET=os.path.join(os.path.dirname(os.path.abspath(__file__)), u'test1_histo.nxs')

class MainGUIGeneral(unittest.TestCase):
  def setUp(self):
    self.app=QApplication([])
    self.gui=MainGUI([])

  def tearDown(self):
    self.gui.trigger.stay_alive=False
    self.gui.trigger.wait()

  def test_1startup(self):
    self.assertTrue(isinstance(self.gui, QMainWindow))

  def test_2loadfile(self):
    self.gui.fileOpen(TEST_DATASET, do_plot=False)
    self.assertTrue(isinstance(self.gui.active_data, NXSData), 'dataset loaded')
    folder, basename=os.path.split(TEST_DATASET)
    self.assertEqual(self.gui.active_folder, folder)
    self.assertEqual(self.gui.active_file, basename)

  def test_2loadfile_plot(self):
    self.gui.fileOpen(TEST_DATASET, do_plot=True)
    self.assertFalse(self.gui.ui.xtof_overview.cplot is None, 'plot created')
    self.assertFalse(self.gui.ui.xy_overview.cplot is None, 'plot created')
    self.assertTrue(isinstance(self.gui.refl, Reflectivity))

  def test_3setxy(self):
    xstart=self.gui.ui.refXPos.value()
    ystart=self.gui.ui.refYPos.value()
    ywstart=self.gui.ui.refYWidth.value()
    self.gui.fileOpen(TEST_DATASET, do_plot=True)
    self.assertNotEqual(xstart, self.gui.ui.refXPos.value(), 'x-fitting')
    self.assertNotEqual(ystart, self.gui.ui.refYPos.value(), 'y-fitting')
    self.assertNotEqual(ywstart, self.gui.ui.refYWidth.value(), 'yw-fitting')


class MainGUIActions(unittest.TestCase):
  def setUp(self):
    self.app=QApplication([])
    self.gui=MainGUI([])
    self.gui.fileOpen(TEST_DATASET, do_plot=True)

  def waitTrigger(self):
    # make sure the trigger got called
    sleep(self.gui.trigger.delay*2.5)

  def tearDown(self):
    self.gui.trigger.stay_alive=False
    self.gui.trigger.wait()

  def test_1normalization(self):
    self.gui.ui.actionNorm.trigger()
    self.waitTrigger()
    self.assertTrue((self.gui.refl.R[self.gui.refl.R>0]==1.).all(),
                    'reflectivity self normalized %s'%repr(self.gui.refl))

  def test_change(self):
    self.assertFalse(self.gui.auto_change_active)

    self.gui.ui.refXPos.selectAll()
    QTest.keyClicks(self.gui.ui.refXPos, "200"+dot+"5")
    self.gui.ui.refXWidth.selectAll()
    QTest.keyClicks(self.gui.ui.refXWidth, "20")
    self.gui.ui.refYPos.selectAll()
    QTest.keyClicks(self.gui.ui.refYPos, "150")
    self.gui.ui.refYWidth.selectAll()
    QTest.keyClicks(self.gui.ui.refYWidth, "60")
    self.gui.ui.bgCenter.selectAll()
    QTest.keyClicks(self.gui.ui.bgCenter, "20")
    self.gui.ui.bgWidth.selectAll()
    QTest.keyClicks(self.gui.ui.bgWidth, "30")
    self.gui.ui.refScale.selectAll()
    QTest.keyClicks(self.gui.ui.refScale, "2")
    self.assertEqual(self.gui.ui.refXPos.value(), 200.5)
    self.assertEqual(self.gui.ui.refXWidth.value(), 20.)
    self.assertEqual(self.gui.ui.refYPos.value(), 150.)
    self.assertEqual(self.gui.ui.refYWidth.value(), 60.)
    self.assertEqual(self.gui.ui.bgCenter.value(), 20.)
    self.assertEqual(self.gui.ui.bgWidth.value(), 30.)
    self.assertEqual(self.gui.ui.refScale.value(), 2.)

    # make sure reflectivity got extracted with new params
    self.gui.ui.actionNorm.trigger()
    self.waitTrigger()
    self.assertEqual(self.gui.refl.options['x_pos'], 200.5)
    self.assertEqual(self.gui.refl.options['x_width'], 20.)
    self.assertEqual(self.gui.refl.options['y_pos'], 150.)
    self.assertEqual(self.gui.refl.options['y_width'], 60.)
    self.assertEqual(self.gui.refl.options['bg_pos'], 20.)
    self.assertEqual(self.gui.refl.options['bg_width'], 30.)
    self.assertEqual(self.gui.refl.options['scale'], 100.)

suite=unittest.TestLoader().loadTestsFromTestCase(MainGUIGeneral)
suite.addTest(unittest.TestLoader().loadTestsFromTestCase(MainGUIActions))
