#-*- coding: utf-8 -*-
'''
Keeping the sample database up to date by adding any additional files found
on the file system.
'''

import os
import logging
from threading import Thread, Event
from . import database, qreduce
from .config import instrument

class DatabaseUpdater(Thread):
  '''
  A background thread updating the dataset database whenever a new
  dataset is available.
  '''
  daemon=True

  current_index=None
  sleep_time=30.
  live_data_last_index=0
  live_data_last_mtime=0

  def __init__(self, start_idx=None):
    '''
    Create the thread with a database handle and quit event and
    initialize the first index to look for.
    '''
    Thread.__init__(self, name='DatabaseUpdateThread')
    self.quit_event=Event()
    self.quit_event.clear()
    self.db=database.DatabaseHandler()

    # define which file index will be indexed first
    # this can be either given on command line, read from the database
    # or guessed from the LiveData files
    if start_idx is None:
      res=self.db()
      if len(res)==0:
        self.index_from_live_data()
      else:
        res.sort_by('-file_id')
        self.current_index=res[0].file_id+1
    else:
      self.current_index=start_idx

  def run(self):
    while not self.quit_event.is_set():
      try:
        self.check()
        self.check_live_index()
      except:
        logging.warning('Error in DatabaseUpdater thread:', exc_info=True)
      self.quit_event.wait(self.sleep_time)

  def in_db(self, idx=None):
    '''
    Check if file index is in database without trying to add it.
    '''
    if idx is None:
      return len(self.db(file_id=self.current_index))>0
    else:
      return len(self.db(file_id=idx))>0

  def check(self):
    '''
    Increase current_index as long as there are data files available.
    '''
    # don't try to locate a file that's already in the database
    while self.in_db(): self.current_index+=1

    # check if the file actually exists before trying to add it
    fname=qreduce.locate_file(self.current_index, verbose=False)
    while fname is not None and not self.quit_event.is_set():
      res=self.db.add_record(self.current_index)
      if res:
        logging.info('New file added with index %i.'%self.current_index)
      self.current_index+=1

      # don't try to locate a file that's already in the database
      while self.in_db(): self.current_index+=1

      # check if the file actually exists before trying to add it
      fname=qreduce.locate_file(self.current_index, verbose=False)

  def check_live_index(self):
    '''
    Make sure we can step over missing files with self.check().
    '''
    if not os.path.exists(instrument.LIVE_DATA):
      return
    if self.current_index==self.live_data_last_index and\
        os.path.getmtime(instrument.LIVE_DATA)==self.live_data_last_mtime:
      # don't check for live data index if we are waiting for it's index and
      # the live data file has not been updated
      return
    live_ds=qreduce.NXSData(instrument.LIVE_DATA)
    self.live_data_last_index=live_ds.number
    self.live_data_last_mtime=os.path.getmtime(instrument.LIVE_DATA)
    if live_ds is not None and live_ds.number>(self.current_index+1)\
        and not self.quit_event.is_set():
      for i in range(self.current_index, live_ds.number):
        if self.in_db(i):
          self.current_index=i+1
          return
        res=self.db.add_record(i)
        if res:
          logging.info('New file found with index %i.'%i)
          self.current_index=i
          return

  def index_from_live_data(self):
    '''
    If there is no database yet, start with file index 100 smaller than the current
    measurement.
    '''
    live_ds=qreduce.NXSData(instrument.LIVE_DATA)
    if live_ds is not None:
      self.current_index=live_ds.number-100
    else:
      self.current_index=10000

