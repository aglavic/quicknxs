#-*- coding: utf-8 -*-
'''
A database to keep track of datafile parameters for fast search of e.g. suitable
direct beam measurements.
'''

import os
from numpy import *
from .buzhug import Base
from .qreduce import NXSData
from .qcalc import get_xpos, get_yregion
from .config import instrument as config
from .decorators import log_call
from logging import debug

class DatabaseHandler(object):
  '''
  Objects with database handling methods to store and process information about
  nexus files for quick reference.
  '''
  db=None
  fields=[]
  
  def __init__(self):
    self.fields=[('file_id', int), ('file_path', unicode),
            ('no_states', int), ('no_bins', int), ('first_bin', float), ('last_bin', float),
            ('xpix', float), ('ycenter', float), ('ywidth', float),
            ('ai', float), ('lambda_center', float)]
    self.fields+=[(item[0], item[2]) for item in config.DATABASE_ADDITIONAL_FIELDS]

  @log_call
  def create_db(self):
    self.db=Base(config.database_file)
    self.db.create(*self.fields)

  @log_call
  def load_db(self):
    self.db=Base(config.database_file)
    self.db.open()

  @log_call
  def close_db(self):
    if self.db is not None:
      self.db.close()
      self.db=None

  def get_database(self):
    if self.db is None and os.path.exists(config.database_file):
      self.load_db()
    elif self.db is None:
      self.create_db()
    return self.db

  @log_call
  def get_record(self, dataset):
    '''
    Return the database record corresponding to a given dataset.
    
    :param NXSData dataset: the dataset to analyze
    '''
    output=[int(dataset.number)]
    output.append(dataset.origin) # file_name

    output.append(len(dataset))
    data=dataset[0]
    output.append(len(data.tof))
    output.append(float(data.tof[0]))
    output.append(float(data.tof[-1]))

    xpix=float(get_xpos(data))
    output.append(xpix) # xpix
    ycenter, ywidth, ignore=get_yregion(data)
    output.append(float(ycenter)), output.append(float(ywidth))

    grad_per_pixel=data.det_size_x/data.dist_sam_det/data.xydata.shape[1]*180./pi
    tth=(data.dangle-data.dangle0)+(data.dpix-xpix)*grad_per_pixel
    output.append(float(tth/2.)) # ai
    output.append(float(data.lambda_center))
  
    for ignore, key, ftype in config.DATABASE_ADDITIONAL_FIELDS:
      output.append(ftype(data.logs[key]))
    return output
  
  @log_call
  def add_record(self, dataset):
    '''
    Create a database record for a dataset and add it to the database.
    
    :param NXSData dataset: the dataset to add
    
    :returns bool: If the dataset is in the database after this operation
    '''
    db=self.get_database()
    if type(dataset) is int:
      if len(db(file_id=dataset))>0:
        debug('Item already in database %s'%repr(dataset))
        return True
      try:
        dataset=NXSData(dataset, use_caching=False)
      except KeyboardInterrupt:
        raise KeyboardInterrupt
      except:
        debug('Could not load dataset with index %i:'%dataset, exc_info=True)
        return False
      else:
        if dataset is None:
          return False
    try:
      record=self.get_record(dataset)
    except:
      debug('Could not create record for dataset %s:'%repr(dataset), exc_info=True)
      return False
    if len(db(file_id=dataset.number))>0:
      debug('Item already in database %s'%repr(dataset))
      return True
    db.insert(*record)
    return True

  def __del__(self):
    if self.db is None:
      self.close_db()

  def __len__(self):
    db=self.get_database()
    return len(db())

  def __call__(self, *args, **opts):
    '''
    Call the database select method when the handler is called.
    
    Usage example:
      DatabaseHandler(ai=[0.1, 0.2], lambda_center=[3., 4.])
      # return all datasets whith alpha_i between 0.1 and 0.2 and lambda_center between 3 and 4.
    '''
    db=self.get_database()
    if len(args)==0:
      return db(**opts)
    elif len(args)==1:
      return db.select(None, args[0], **opts)
    elif len(args)==2:
      return db.select(*args, **opts)
    else:
      raise ValueError, '__call__ expects 0 to 2 non keyword arguments'


  def find_direct_beams(self, dataset):
    '''
    Search the database for a direct beam measurement that fits the given dataset.
    
    :param NXSData dataset: the dataset to search a direct beam run for
    
    :return: result of the database query for the appropriate direct beam runs
    '''
    data=dataset[0]

    lambda_center=float(data.lambda_center)

    cmp_vals={'ai': [-0.1, 0.1],
              'lambda_center': [lambda_center-0.01, lambda_center+0.01],
              'no_bins': len(data.tof),
              'first_bin': float(data.tof[0]),
              'last_bin': float(data.tof[-1])}

    for key, log, ctype, diff in config.DATABASE_DIRECT_BEAM_COMPARE:
      val=ctype(data.logs[log])
      cmp_vals[key]=[val-diff, val+diff]

    return self(**cmp_vals)
