#-*- coding: utf-8 -*-
'''
Use the sample database to try to automatically generate reflectivity plots
from the most current mesurements.
'''

import logging
from time import sleep


class ReflectivityBuilder(object):
  current_items=None

  def __init__(self):
    self.current_items=[]

  def run(self):
    while True:
      try:
        self._run()
      except KeyboardInterrupt:
        return
      except:
        logging.debug('Error in ReflectivityBuilder:', exc_info=True)
        sleep(1.)

  def _run(self):
    sleep(1.)

