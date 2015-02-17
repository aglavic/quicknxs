#!/usr/bin/env python
#-*- coding: utf-8 -*-
'''
Script triggered when REF_M file is translated. It will analyze the translated file and
put the results in the sample database from QuickNXS. After adding it to the database it will
check if a ReflectivityBuilder daemon is running and either notify it of the new file or
start a new one otherwise.
'''

import logging
import sys, os
import time

# for testing use latest quicknxs test version instead of the installed one
sys.path.insert(0, u'/SNS/users/agf/software/QuickNXS/')
for path in "/SNS/software/lib/python2.6/site-packages:/SNS/software/lib/python2.6/site-packages/HLRedux:/SNS/software/lib64/python2.6/site-packages/DOM:/SNS/software/lib/python2.6/site-packages/sns_common_libs:/SNS/software/lib/python2.6/site-packages:/SNS/users/agf/python/lib64/python2.6/site-packages:/SNS/users/agf/python/lib/python2.6/site-packages".split(":"):
    sys.path.append(path)
#sys.path.insert(0, u'/home/agf/Software/Scripte/QuickNXS/')

from quicknxs.console_logging import setup_logging
from quicknxs.version import str_version

LOG_LEVEL=logging.INFO
FILE_PREFIX=u'/SNS/REF_M/shared/autoreduce/logfiles/reduce_REF_M_'
#FILE_PREFIX=u'/tmp/reduce_'

def update_database(filename):
  '''load file, run analysis and add parameters to the database'''
  from quicknxs.database_updater import database
  from quicknxs.qreduce import NXSData
  nb=int(filename.split('_')[-2])
  dataset=NXSData(nb, use_caching=False)
  db=database.DatabaseHandler()
  added=db.add_record(dataset)
  db.close_db()
  return added, dataset

def trigger_autorefl(fnumber, fname=None, image_path=None):
  '''
    Call autorefl script with current run number. 
    The script will handle communication with running instance
    or start of new instance of the script.
  '''
  from quicknxs.auto_reflectivity import ReflectivityBuilder, FileCom
  if FileCom.check_running():
    FileCom.send_new_file(fnumber, fname, image_path)
  else:
    ReflectivityBuilder.spawn_daemon(fnumber, fname, image_path)

def kill_autorefl():
  from quicknxs.auto_reflectivity import FileCom
  FileCom.kill_daemon()

def wait_image(ofile):
  '''
  Wait a maximum of 10min for the plot to be created.
  The script needs to exit afterwards for the image
  to show up on the analysis data homepage.
  '''
  for ignore in range(600):
    if not os.path.exists(ofile):
      time.sleep(1.)
      continue
    else:
      return True
  return False

if __name__=="__main__":
  # initialize logging to file and console
  # console log level is given by LOG_LEVEL
  # while file log level is always DEBUG
  setup_logging(log_level=LOG_LEVEL,
                filename=FILE_PREFIX+time.strftime('%Y_%m_%d-%H_%M_%S')+'.log')
  logging.info('*** reduce_REF_M using QuickNXS %s Logging started ***'%str_version)
  if len(sys.argv)==2 and sys.argv[1]=='kill':
    kill_autorefl()
  elif (len(sys.argv)!=3):
    logging.error("autoreduction code requires a filename and an output directory")
  elif not(os.path.isfile(sys.argv[1])):
    logging.error("data file '%s' not found"%sys.argv[1])
  else:
    filename=unicode(sys.argv[1])
    outdir=unicode(sys.argv[2])

    logging.info('Analyze dataset and add to sample database')
    result=update_database(filename)
    if result[0]:
      logging.info('Trigger autorefl script for index %i'%result[1].number)
      ofile=outdir+'REF_M_%i_autoreduced.png'%result[1].number
      trigger_autorefl(result[1].number, filename, ofile)
      logging.info('Wait for image to be generated.')
      img_result=wait_image(ofile)
      if img_result:
        logging.info('Image created')
      else:
        logging.info('No image created')
    else:
      logging.warning('Could not add run to database, check logs for details')

  logging.info('*** reduce_REF_M using QuickNXS %s Logging ended ***'%str_version)
