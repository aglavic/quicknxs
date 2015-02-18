#-*- coding: utf-8 -*-
'''
Use the sample database to try to automatically generate reflectivity plots
from the most current mesurements.
'''

import os, sys
import logging
import numpy
import atexit
from numpy import sin, pi, where

from cPickle import dumps, loads
from threading import Thread, Event, _Event
from xml.etree import ElementTree

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.gridspec import GridSpec
from matplotlib import cm, colors
cmap=colors.LinearSegmentedColormap.from_list('default',
                  ['#0000ff', '#00ff00', '#ffff00', '#ff0000', '#bd7efc', '#000000'], N=256)
cm.register_cmap('default', cmap=cmap)
from matplotlib.colors import LogNorm

from . import database, qreduce, qcalc, console_logging
from .config import instrument
from .version import str_version

class GroupEvent(_Event):
  '''
  A threading Event that will also trigger a root event when it is set.
  This is useful to wait for any of several events to get triggered.
  '''
  def __init__(self, root_event):
    self.root_event=root_event
    _Event.__init__(self)

  def set(self):
    self.root_event.set()
    _Event.set(self)

class FileCom(Thread):
  '''
  A thread that allows the daemon to communicate with other instances through
  a file as analysis servers don't allow socket communication.
  This is used to notify the daemon about new translated files.
  '''
  bind_path=instrument.autorefl_folder+'REF_M_autorefl.com'
  parent=None
  MAX_READ_TIME=1
  daemon=True
  last_com=0.

  def __init__(self, parent):
    Thread.__init__(self, name='FileCom')
    self.parent=parent
    self.quit=Event()
    self.quit.clear()

  def run(self):
    logging.debug('FileCom started')
    logging.debug('Creating communication file %s'%self.bind_path)
    self.clear_com()
    atexit.register(os.remove, self.bind_path)

    while not self.quit.isSet():
      try:
        self._run()
      except KeyboardInterrupt:
        return
      except:
        logging.warning('Error in FileCom:', exc_info=True)
        self.quit.wait(30.)

    logging.debug('FileCom closed')

  def _run(self):
    while not self.quit.isSet():
      mtime=os.path.getmtime(self.bind_path)
      if mtime==self.last_com:
        self.quit.wait(1.)
        continue
      logging.info('External program has established connection')
      try:
        xml=ElementTree.parse(self.bind_path)
      except:
        logging.warn('Communication error, could not parse xml string:', exc_info=True)
        self.clear_com()
        continue
      self.clear_com()

      root=xml.getroot()
      if root.tag!='QuickNXS_FileCom':
        logging.warn('Root element of XML %s!=QuickNXS_FileCom'%root.tag)
      message_dict={}
      for subele in root:
        key=subele.tag
        pickled=bool(eval(subele.get('pickled', 'False')))
        if pickled:
          value=loads(subele.get('value'))
        else:
          value=eval(subele.get('value'))
        message_dict[key]=value
      if not 'action' in message_dict:
        logging.warn('Message contains no action, discarded')
        continue
      action=message_dict['action']
      if action=='Kill':
        logging.info('Kill action received, shutting down main thread')
        self.parent.quit.set()
        self.quit.set()
      elif action=='NewFile':
        logging.info('New file received, ID=%i ; path=%s ; image_path=%s'%(
                                                                 message_dict['fid'],
                                                                 message_dict['fname'],
                                                                 message_dict['image_path']))
        self.parent.newFileId=message_dict['fid']
        self.parent.newFileName=message_dict['fname']
        self.parent.newFileImage=message_dict['image_path']
        if self.parent.live_data_idx<=self.parent.newFileId:
          self.parent.live_data_idx=self.parent.newFileId+1
        self.parent.newFile.set()
      else:
        logging.warn('Message action "%s" unknown, discarded'%action)
        continue

  def clear_com(self):
    open(self.bind_path, 'w').write('\n')
    self.last_com=os.path.getmtime(self.bind_path)
    try:
      os.chmod(self.bind_path, 0666)
    except OSError:
      pass

  @classmethod
  def _send_message(cls, message_dict):
    '''
    Create xml string and send it through the socket to a running server instance.
    '''
    logging.debug('Creating xml for socket communication')
    root=ElementTree.Element('QuickNXS_FileCom')
    for key, value in sorted(message_dict.items()):
      attrib={'type': type(value).__name__}
      if type(value) in [str, unicode, int, float, bool, type(None)]:
        attrib['pickled']='False'
        attrib['value']=repr(value)
      else:
        attrib['pickled']='True'
        attrib['value']=dumps(value)
      sub=ElementTree.Element(key, attrib=attrib)
      root.append(sub)
    xml=ElementTree.ElementTree(root)
    logging.debug('Sending data')
    xml.write(cls.bind_path)
    try:
      os.chmod(cls.bind_path, 0666)
    except OSError:
      pass
    logging.debug('Communication finished')

  @classmethod
  def kill_daemon(cls):
    '''Send message to shutdown the reflectivity daemon process'''
    cls._send_message({'action': 'Kill'})

  @classmethod
  def send_new_file(cls, fid, fname=None, image_path=None):
    '''Send a message for a new run file number'''
    cls._send_message({'action': 'NewFile', 'fid': fid, 'fname': fname,
                      'image_path': image_path})

  @classmethod
  def ping(cls):
    '''Send a message over the socket and wait for reply'''
    raise NotImplementedError

  @classmethod
  def check_running(cls):
    '''
     Check if socket path exists and if a daemon process is running,
     otherwise delete the socket path and return False.
    '''
    if os.path.exists(cls.bind_path):
      if os.path.exists(ReflectivityBuilder.PID_FILE):
          return True
      else:
        logging.warn('Found com file but no PID file, deleting socket file')
        os.remove(cls.bind_path)
        return False
    else:
      return False

class FileWatchDog(Thread):
  '''
  Thread that watches the LiveData file for changes to notify
  the daemon thread about the changes.
  '''
  daemon=True
  live_data_last_mtime=0

  def __init__(self, parent):
    Thread.__init__(self, name='FileWatchDog')
    self.parent=parent

    self.quit=Event()
    self.quit.clear()

  def run(self):
    logging.debug('FileWatchDog started')
    while not self.quit.isSet():
      try:
        self._run()
      except KeyboardInterrupt:
        return
      except:
        logging.warning('Error in FileWatchDog:', exc_info=True)
        self.quit.wait(30.)
    logging.debug('FileWatchDog closed')
  
  def _run(self):
    self.live_data_last_mtime=os.path.getmtime(instrument.LIVE_DATA)
    while not self.quit.isSet():
      new_mtime=os.path.getmtime(instrument.LIVE_DATA)
      if new_mtime!=self.live_data_last_mtime:
        logging.debug('Live data updated, mtime %.2f->%.2f'%(
                            self.live_data_last_mtime, new_mtime))
        self.parent.newLiveData.set()
        self.live_data_last_mtime=os.path.getmtime(instrument.LIVE_DATA)
      self.quit.wait(10.)


class ReflectivityBuilder(Thread):
  '''
  Analyze the most recent datafiles to search for corresponding runs to build
  a reflectivity from. Stepping back the sample angle is the main indicator
  of finishing one reflectivity and starting a new one.
  Each run will be normalized by a corresponding direct beam and scaled
  according to the previous runs/total reflection.
  Finished reflecitvities are stored in the shared folder of the associated beamtime.
  '''
  current_index=None

  reflectivity_items=None
  reflectivity_states=None
  reflectivity_last_Q_center=None
  reflectivity_last_path=None
  reflectivity_active=False
  state_names=None

  live_data_tof_overwrite=None

  PID_FILE=instrument.autorefl_folder+'autorefl.pid'

  @classmethod
  def spawn_daemon(cls, index, fname=None, image_path=None):
    '''
    Spawn a new daemon process for reflectivity reduction and setup
    sockets for communication with this thread.
    '''
    # start the daemon process
    logging.debug('Spawning daemon process')
    pid = os.fork()
  
    if pid != 0:
      logging.debug('Daemon spawned with PID %i'%pid)
      try:
        open(cls.PID_FILE, 'w').write(str(pid)+'\n')
      except:
        logging.warn('Could not store pid %i in file:', exc_info=True)
      return


    # reset logging to change the logfile
    logging.root.removeHandler(console_logging.logfile_handler)
    console_logging.setup_logging(filename=instrument.autorefl_folder+'autorefl.log',
                                  setup_console=False)

    pid=os.getpid()
    atexit.register(os.remove, cls.PID_FILE)
    logging.info('*** QuickNXS %s ReflectivityBuilder daemon started PID: %i ***'%(str_version, pid))

    rb=cls(index)
    rb.start()
    
    rb.newFileId=index
    rb.newFileName=fname
    rb.newFileImage=image_path
    rb.newFile.set()

    while rb.isAlive():
      # keep MainThread alive until at least one day of inactivity
      last_idx=rb.current_index
      rb.quit.wait(24.*3600)
      if rb.current_index==last_idx:
        logging.info('Shutting down due to long period of inactivity')
        rb.quit.set()
        rb.join(120.)
        break

    logging.info('*** QuickNXS %s ReflectivityBuilder daemon closed PID: %i ***'%(str_version, pid))
    sys.exit(0)

  def __init__(self, start_idx=None):
    Thread.__init__(self, name='ReflectivityBuilder')
    self.db=database.DatabaseHandler()
    self.live_data_idx=start_idx

    self.com=FileCom(self)
    self.com.start()

    self.watch=FileWatchDog(self)
    self.watch.start()

    self.action=Event()
    self.action.set() # make sure the first cycle starts the reflectivity

    self.quit=GroupEvent(self.action)
    self.quit.clear()
    self.newFile=GroupEvent(self.action)
    self.newFile.clear()
    self.newFileId=None
    self.newFileName=None
    self.newFileImage=None

    self.newLiveData=GroupEvent(self.action)
    self.newLiveData.clear()

  def run(self):
    logging.debug('ReflectivityBuilder started')
    while not self.quit.isSet():
      try:
        self._run()
      except KeyboardInterrupt:
        break
      except:
        logging.warning('Error in ReflectivityBuilder:', exc_info=True)
        self.quit.wait(30.)
    self.com.quit.set()
    self.watch.quit.set()
    logging.debug('ReflectivityBuilder closed')

  def _run(self):
    '''
    Main loop that monitors the live data and follows the files corresponding to
    one reflectivity set.
    '''
    if self.current_index is None:
      # when started the first time, set the current_index variable
      self.set_start_index(self.live_data_idx)

    while not self.quit.isSet():
      self.action.wait()
      if self.quit.isSet():
        return
      self.action.clear()

      if self.newFile.isSet() and self.live_data_idx<=self.newFileId:
        self.live_data_idx=self.newFileId+1

      #+++++++++++++ Adding data to the plot that has already been translated ++++++++++++++++#
      while self.live_data_idx>self.current_index:
        if self.quit.isSet():
          return
        if not self.reflectivity_active:
          self.start_new_reflectivity()
        if not self.get_dsinfo(self.current_index):
          # if for some reason the run never existed, continue directly
          if len(self.db('file_id>fid', fid=self.current_index))>0:
            logging.debug('Skipping run with no existing NeXus file %i.'%self.current_index)
            self.finish_reflectivity()
            self.current_index+=1
            continue

          # if dataset not yet available, wait for translation service to create the file
          if not (self.newFile.isSet() or self.quit.isSet()):
            self.action.wait()
            self.action.clear()
        else:
          self.add_dataset()
          self.check_and_plot_newfile()
      #------------- Adding data to the plot that has already been translated ----------------#

      if not self.newLiveData.isSet():
        # the live data file has not changed, wait and try again
        continue
      self.newLiveData.clear()

      #+++++++++++++ Plotting the current reflectivity including the live data +++++++++++++++#
      # When all files up to the live data index have been added
      # we reread the live data to add it to the plot
      live_ds=qreduce.NXSData(instrument.LIVE_DATA, use_caching=False,
                              event_tof_overwrite=self.live_data_tof_overwrite)
      if live_ds is None:
        continue
      if live_ds.number>self.current_index:
        # if the current run has finished we increment the live data index and add
        # the dataset after translation, which is done in the first step of the main loop
        logging.debug('Increment live_data_idx to %i'%live_ds.number)
        self.live_data_idx=live_ds.number
        continue
      if live_ds.number<self.current_index:
        # if the live data is a direct beam run, ignore it, this will just loop over
        # wait times until the live data index is incremented
        continue
      if not self.reflectivity_active:
        self.start_new_reflectivity(live_ds)

      # create reflectivity from live data and plot the result to the live reflectivity file
      live_refl=self.create_live_refl(live_ds)
      if live_refl is None:
        continue
      data=self.combine_reflectivity(live_add=[live_refl])
      title='+'.join([r[0].options['number'] for r in self.reflectivity_items])
      title+='+LiveData'
      self.plot_reflectivity(data, instrument.AUTOREFL_LIVE_IMAGE, title, False)
      open(instrument.AUTOREFL_LIVE_INDEX, 'w').write('%i\n'%live_ds.number)
      #------------- Plotting the current reflectivity including the live data ---------------#

  def check_and_plot_newfile(self):
    '''
    Check if the newFile flag is set and the current_index has reached it
    already. If it is a valid reflectivity save the image.
    '''
    # In case the action got triggered by LiveData and not the FileCom
    # wait a few seconds for pending communiction.
    if self.newLiveData.is_set() and not self.newFile.isSet():
      self.newFile.wait(60.)
    if self.newFile.isSet() and self.current_index>=(self.newFileId+1):
      # create image for the autoreduce script
      self.newFile.clear()
      if self.newFileImage is not None and self.current_index==(self.newFileId+1):
        if self.reflectivity_active:
          logging.debug('Generate autoreduce image at %s'%self.newFileImage)
          data=self.combine_reflectivity(sep_last=True)
          numbers='+'.join([r[0].options['number'] for r in self.reflectivity_items])
          self.plot_reflectivity(data, self.newFileImage, numbers, this_run=self.newFileId)
        else:
          logging.debug('Generate autoreduce raw image at %s'%self.newFileImage)
          try:
            self.plot_raw_only(self.newFileImage, self.newFileId)
          except:
            logging.warn('Error in plot_raw_only:', exc_info=True)
      self.newFileId=None
      self.newFileImage=None
      self.newFileName=None

  def set_start_index(self, start_idx=None):
    '''
    Look back from the current live data index to find the first index that
    is not direct beam and has no preceding file with lower Q.
    '''
    if start_idx is None:
      if not os.path.exists(instrument.LIVE_DATA):
        raise RuntimeError, 'Cannont create automatic reflectivity without live data present'
      live_ds=qreduce.NXSData(instrument.LIVE_DATA, use_caching=False)
      if live_ds is None:
        raise RuntimeError, 'Cannont create automatic reflectivity, live data is not readable'
      self.current_index=live_ds.number
      self.live_data_idx=live_ds.number
      last_ai=self.get_ai(live_ds)
      last_channels=len(live_ds)
      last_lambda=live_ds.lambda_center
    else:
      self.current_index=start_idx
      ds=qreduce.NXSData(start_idx, use_caching=False)
      last_ai=self.get_ai(ds)
      last_channels=len(ds)
      last_lambda=ds.lambda_center
    last_Q_center=4.*pi/last_lambda*sin(last_ai/180.*pi)

    results=self.db('file_id>=start_id and file_id<end_id',
                    start_id=self.current_index-20,
                    end_id=self.current_index)
    results=results.sort_by('-file_id')
    for result in results:
      if abs(result.ai)<0.1:
        break
      result_Q_center=4.*pi/result.lambda_center*sin(result.ai/180.*pi)
      if result_Q_center>last_Q_center:
        break
      if result.no_states!=last_channels:
        break
      last_ai=result.ai
      last_lambda=result.lambda_center
      last_Q_center=result_Q_center
      self.current_index=result.file_id

  def start_new_reflectivity(self, live_ds=None):
    '''
    Prepare the creation of a new reflectivity set. Read some data for the first dataset
    to be able to compare it to following datasets.
    '''
    if live_ds:
      # The first dataset is from live data, use it's information to begin the reflecivity
      if self.get_ai(live_ds)<0.1:
        self.current_index+=1
        return False
      logging.info('Creating new reflectivity starting at Live Data (index %i).'%self.current_index)
      self.reflectivity_items=[]
      self.reflectivity_last_Q_center=4.*pi/live_ds.lambda_center*sin(self.get_ai(live_ds)/180.*pi)
      self.reflectivity_states=len(live_ds.keys())
      self.reflectivity_last_path=None
      self.reflectivity_active=True
      self.state_names=None
      return True
    else:
      # the first dataset is already translated, use database information to begin reflecitvity
      dsinfo=self.get_dsinfo(self.current_index)
      if dsinfo is False:
        return False
      if dsinfo is None:
        # dataset could not be processed properly, increment index
        self.current_index+=1
        return False
      elif dsinfo.ai<0.1:
        self.current_index+=1
        return False
      logging.info('Creating new reflectivity starting at index %i.'%self.current_index)
      self.reflectivity_items=[]
      self.reflectivity_last_Q_center=4.*pi/dsinfo.lambda_center*sin(dsinfo.ai/180.*pi)
      self.reflectivity_states=dsinfo.no_states
      self.reflectivity_last_path=os.path.dirname(dsinfo.file_path)
      self.reflectivity_active=True
      self.state_names=None
      return True

  def add_dataset(self):
    '''
    Read the file for the current index and create the reflecitvity for each state.
    If the parameters do not match the last run in the reflectivity, finish
    the reflectivity and start a new one with this as the first dataset.
    '''
    if not self.reflectivity_active:
      # nothing to do, as there is no reflectivity beeing created
      return False
    dsinfo=self.get_dsinfo(self.current_index)
    if dsinfo is False:
      # dataset is not yet in database, go back to the main loop, which will wait for it
      return False
    if dsinfo is None:
      # current dataset was not readable properly, finish reflectivity and increment index
      logging.debug('Could not read dataset info properly.')
      self.finish_reflectivity()
      self.current_index+=1
      return True
    Q_center=4.*pi/dsinfo.lambda_center*sin(dsinfo.ai/180.*pi)
    file_path=os.path.dirname(dsinfo.file_path)
    if Q_center<self.reflectivity_last_Q_center or dsinfo.no_states!=self.reflectivity_states or\
       (self.reflectivity_last_path is not None and self.reflectivity_last_path!=file_path):
      # The currenct reflectivity is finished, as this dataset does not correspond to
      # it. Return to the main loop, which will try to add the dataset again.
      logging.debug('Next dataset at lower Q, from different experiment or number of states different:'+\
                    '\n           Q: %g->%g\n          #States: %i->%i\n          Paths: %s->%s'%
                    (self.reflectivity_last_Q_center, Q_center,
                     self.reflectivity_states, dsinfo.no_states,
                     self.reflectivity_last_path, file_path))
      self.finish_reflectivity()
      return True

    logging.info('Extracting reflectivity for index %i.'%self.current_index)
    # load the dataset
    data=qreduce.NXSData(dsinfo.file_path, use_caching=False)
    # search for fitting direct beams in database
    results=self.db.find_direct_beams(data)
    if len(results)==0:
      # There are no corresponding direct beam runs for this dataset measured before.
      # We have no way of fixing this, so we ignore it and just start from scratch
      # with the next dataset.
      logging.debug('No direct beam for current dataset.')
      self.finish_reflectivity()
      self.current_index+=1
      return True
    results.sort_by('-file_id')
    compat=numpy.array([abs(r.s1w-dsinfo.s1w)+abs(r.s3w-dsinfo.s3w) for r in results])
    match=results[compat.argmin()]
    # read run for normalization
    norm_data=qreduce.NXSData(match.file_path, use_caching=False)
    norm=qreduce.Reflectivity(norm_data[0],
                             x_pos=match.xpix, x_width=9,
                             y_pos=match.ycenter, y_width=match.ywidth,
                             number=str(match.file_id),
                             )

    refls=[]
    P0, PN=self.get_cut_pts(data)
    # create first channel reflectivity to determine the scaling factor
    r0=qreduce.Reflectivity(data[0],
                            x_pos=dsinfo.xpix, x_width=9,
                            y_pos=dsinfo.ycenter, y_width=dsinfo.ywidth,
                            number=str(dsinfo.file_id),
                            normalization=norm,
                            P0=P0, PN=PN,
                            )
    if len(self.reflectivity_items)==0:
      # scale the first dataset to total reflectivity and store it's state names for the plot
      self.state_names=data.keys()
      scale=qcalc.get_total_reflection(r0, return_npoints=False)
    else:
      # try to match both datasets by fitting a polynomiral to the overlapping region
      scale, _xfit, _yfit=qcalc.get_scaling(r0, self.reflectivity_items[-1][0], 1, polynom=3)

    # extract reflectivities for all states
    for i in range(self.reflectivity_states):
      refls.append(qreduce.Reflectivity(data[i],
                                        x_pos=dsinfo.xpix, x_width=9,
                                        y_pos=dsinfo.ycenter, y_width=dsinfo.ywidth,
                                        number=str(dsinfo.file_id),
                                        normalization=norm, scale=scale,
                                        P0=P0, PN=PN,
                                        ))
    # adding the dataset was successful, add it and increment the index.
    self.reflectivity_items.append(refls)
    self.current_index+=1
    self.reflectivity_last_Q_center=Q_center
    self.live_data_tof_overwrite=data[0].tof_edges
    return True

  def create_live_refl(self, live_ds):
    '''
    Read the file for the current index and create the reflecitvity for each state.
    '''
    if not self.reflectivity_active:
      return None
    xpix=float(qcalc.get_xpos(live_ds[0], refine=self.db.refine_xpos, max_width=self.db.maxw_xpos))
    ycenter, ywidth, ignore=qcalc.get_yregion(live_ds[0])

    # search for fitting direct beams in database
    results=self.db.find_direct_beams(live_ds)
    if len(results)==0:
      return None
    logging.info('Extracting reflectivity for Live Data.')

    results.sort_by('-file_id')
    compat=numpy.array([abs(r.s1w-live_ds[0].logs['S1HWidth'])+
                        abs(r.s3w-live_ds[0].logs['S3HWidth']) for r in results])
    match=results[compat.argmin()]
    norm_data=qreduce.NXSData(match.file_path, use_caching=True)
    norm=qreduce.Reflectivity(norm_data[0],
                             x_pos=match.xpix, x_width=9,
                             y_pos=match.ycenter, y_width=match.ywidth,
                             number=str(match.file_id),
                             )

    refls=[]
    P0, PN=self.get_cut_pts(live_ds)
    r0=qreduce.Reflectivity(live_ds[0],
                            x_pos=xpix, x_width=9,
                            y_pos=ycenter, y_width=ywidth,
                            number=str(live_ds.number),
                            normalization=norm,
                            P0=P0, PN=PN,
                            )

    Q_center=4.*pi/live_ds.lambda_center*sin(r0.ai)
    if Q_center<self.reflectivity_last_Q_center:
      logging.debug('Live dataset has lower Q, finish current reflectivity. Qnew: %g, Qold: %g'%
                    (Q_center, self.reflectivity_last_Q_center))
      self.finish_reflectivity()
      self.start_new_reflectivity(live_ds)
    if len(self.reflectivity_items)==0:
      self.state_names=live_ds.keys()
      scale=qcalc.get_total_reflection(r0, return_npoints=False)
    else:
      # try to match both datasets by fitting a polynomiral to the overlapping region
      scale, _xfit, _yfit=qcalc.get_scaling(r0, self.reflectivity_items[-1][0], 1, polynom=3)

    for i in range(self.reflectivity_states):
      refls.append(qreduce.Reflectivity(live_ds[i],
                                        x_pos=xpix, x_width=9,
                                        y_pos=ycenter, y_width=ywidth,
                                        number=str(live_ds.number),
                                        normalization=norm, scale=scale,
                                        P0=P0, PN=PN,
                                        ))
    return refls

  def finish_reflectivity(self):
    '''
    Plot a finished reflectivity and save it to the shared folder of the current
    experiment for easy access of the user.
    '''
    if self.reflectivity_active:
      self.reflectivity_active=False
      if len(self.reflectivity_items)==0:
        # don't export empty reflectivities
        return
      data=self.combine_reflectivity()
      numbers='+'.join([r[0].options['number'] for r in self.reflectivity_items])
      fpath=instrument.AUTOREFL_RESULT_IMAGE%{
               'origin_path': os.path.dirname(self.reflectivity_items[0][0].origin[0]),
               'numbers': numbers,
                                             }
      self.plot_reflectivity(data, fpath, numbers, True)

  def get_dsinfo(self, index):
    '''
    Get information about a dataset at a given index. First tries to access it
    from the database, if it is not in there it tries to add it to the database
    and then return it.
    If both approaches don't work it returns None.
    '''
    try:
      dsinfo=self.db(file_id=index)[0]
    except IndexError:
#      res=self.db.add_record(index)
#      if res:
#        return self.db(file_id=index)[0]
#      else:
#        return res
      return False
    else:
      return dsinfo

  def get_cut_pts(self, ds):
    l=ds.lambda_center
    res=numpy.where((ds[0].lamda>=(l-1.45))&(ds[0].lamda<=(l+1.25)))[0]
    if len(res)<3:
      return 0, 0
    P0=len(ds[0].lamda)-res[-1]
    PN=res[0]
    return P0, PN

  def combine_reflectivity(self, live_add=[], sep_last=False):
    '''
    Create plottable arrays from the extracted reflectivities.
    '''
    xitems=[[] for ignore in range(self.reflectivity_states)]
    yitems=[[] for ignore in range(self.reflectivity_states)]
    for idx, items in enumerate(self.reflectivity_items+live_add):
      P0=items[0].options['P0']
      PN=items[0].options['PN']
      Pfrom, Pto=PN, len(items[0].R)-P0
      if sep_last and idx==(len(self.reflectivity_items)-1):
        sep_xy=[(ref.Q[Pfrom:Pto], ref.R[Pfrom:Pto])  for ref in items]
      else:
        for i, ref in enumerate(items):
          xitems[i].append(ref.Q[Pfrom:Pto])
          yitems[i].append(ref.R[Pfrom:Pto])
    out=[]
    for i in range(self.reflectivity_states):
      x=numpy.hstack(xitems[i])
      y=numpy.hstack(yitems[i])
      ids=x.argsort()
      x=x[ids]
      y=y[ids]
      out.append((x, y, self.state_names[i]))
    if sep_last:
      for i, (xi, yi) in enumerate(sep_xy):
        out.append((xi, yi, self.state_names[i]+'  this run'))
    return out

  def plot_reflectivity(self, data, fname, title='', highres=False, this_run=None):
    '''
    Generate a graph with a combined reflectivity plot for all spin-states.
    If this_run is given it's raw data is shown on the right side of the same graph, too.
    '''
    logging.info('Saving plot to "%s".'%fname)
    if highres:
      fig=Figure(figsize=(10.667, 8.), dpi=150, facecolor='#FFFFFF')
      fig.subplots_adjust(left=0.1, bottom=0.1, top=0.95, right=0.98)
    elif this_run:
      fig=Figure(figsize=(11., 8.), dpi=150, facecolor='#FFFFFF')
      fig.subplots_adjust(left=0.1, bottom=0.1, top=0.95, right=0.98)
      gs=GridSpec(2, 2, width_ratios=[3, 1])
    else:
      fig=Figure(figsize=(6., 4.), dpi=72, facecolor='#FFFFFF')
      fig.subplots_adjust(left=0.12, bottom=0.13, top=0.94, right=0.98)
    canvas=FigureCanvasAgg(fig)
    if this_run:
      ax=fig.add_subplot(gs[:, 0])
      xy_ax=fig.add_subplot(gs[0,1])
      tof_ax=fig.add_subplot(gs[1, 1])
      p1, p2=self.plot_raw(xy_ax, tof_ax, this_run)
      fig.colorbar(p1, ax=xy_ax, orientation='horizontal')
      fig.colorbar(p2, ax=tof_ax, orientation='horizontal')
    else:
      ax=fig.add_subplot(111)

    ymin=1e10
    ymax=1e-10
    xmin=0.1
    xmax=0.01
    for x, y, label in data:
      try:
        ymin=min(y[y>0].min(), ymin)
      except ValueError:
        # ignore plots with zero intensity
        continue
      else:
        xmin=min(x.min(), xmin)
        xmax=max(x.max(), xmax)
      ymax=max(y.max(), ymax)
      ax.semilogy(x, y, label=label)
    ax.set_xlim(xmin-xmin%0.005, xmax-xmax%0.005+0.005)
    ax.set_ylim(ymin*0.75, ymax*1.25)
    ax.legend()
    ax.set_title(title)
    ax.set_xlabel('Q [$\\AA^{-1}$]')
    ax.set_ylabel('R')
    try:
      canvas.print_png(fname)
    except IOError:
      logging.warn('Could not save plot:', exc_info=True)

  def plot_raw_only(self, fname, this_run):
    '''
    Generate a graph with only the raw data and no reflectivity plot.
    '''
    fig=Figure(figsize=(11., 5.), dpi=150, facecolor='#FFFFFF')
    fig.subplots_adjust(left=0.1, bottom=0.1, top=0.95, right=0.98)
    canvas=FigureCanvasAgg(fig)
    xy_ax=fig.add_subplot(121)
    tof_ax=fig.add_subplot(122)
    p1, p2=self.plot_raw(xy_ax, tof_ax, this_run)
    fig.colorbar(p1, ax=xy_ax, orientation='vertical')
    fig.colorbar(p2, ax=tof_ax, orientation='vertical')
    try:
      canvas.print_png(fname)
    except IOError:
      logging.warn('Could not save raw plot:', exc_info=True)


  def plot_raw(self, xy_ax, tof_ax, this_run):
    '''
    Plot X-Y and ToF-X images into two axis for a given run number.
    '''
    data=qreduce.NXSData(this_run, use_caching=False)[0]
    xyd=data.xydata
    p1=xy_ax.imshow(xyd, aspect='auto', origin='lower', cmap='default',
                    norm=LogNorm(xyd[xyd>0].min(), xyd.max()))
    xy_ax.set_title('%i: X-Y View'%this_run)
    xy_ax.set_xlabel('x [pix]')
    xy_ax.set_ylabel('y [pix]')

    tofdata=data.tofdata
    tofpos=where(tofdata>0)[0]
    tof_from=tofpos[0]
    tof_to=tofpos[-1]+1

    xyd=data.xtofdata[:, tof_from:tof_to]
    tof=data.tof[tof_from:tof_to]
    p2=tof_ax.imshow(xyd, aspect='auto', origin='lower', cmap='default',
                     norm=LogNorm(xyd[xyd>0].min(), xyd.max()),
                     extent=[tof[0]*1e-3, tof[-1]*1e-3, 0, xyd.shape[0]-1])
    tof_ax.set_title('%i: ToF-X View'%this_run)
    tof_ax.set_xlabel('ToF [ms]')
    tof_ax.set_ylabel('x [pix]')
    return p1, p2

  def get_ai(self, ds):
    data=ds[0]
    xpix=float(qcalc.get_xpos(data, refine=self.db.refine_xpos, max_width=self.db.maxw_xpos))

    grad_per_pixel=data.det_size_x/data.dist_sam_det/data.xydata.shape[1]*180./numpy.pi
    tth=(data.dangle-data.dangle0)+(data.dpix-xpix)*grad_per_pixel
    return tth/2.
