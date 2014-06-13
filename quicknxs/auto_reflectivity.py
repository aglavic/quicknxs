#-*- coding: utf-8 -*-
'''
Use the sample database to try to automatically generate reflectivity plots
from the most current mesurements.
'''

import os
import logging
import numpy
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from time import sleep
from . import database, qreduce, qcalc
from .config import instrument

class ReflectivityBuilder(object):
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
  reflectivity_last_ai=None
  reflectivity_last_lamda=None
  reflectivity_active=False
  state_names=None

  MAX_RETRIES=10

  live_data_tof_overwrite=None
  live_data_last_mtime=0

  def __init__(self, start_idx=None):
    self.db=database.DatabaseHandler()
    self.live_data_idx=start_idx

  def run(self):
    while True:
      try:
        self._run()
      except KeyboardInterrupt:
        return
      except:
        logging.warning('Error in ReflectivityBuilder:', exc_info=True)
        sleep(30.)

  def _run(self):
    '''
    Main loop that monitors the live data and follows the files corresponding to
    one reflectivity set.
    '''
    if self.current_index is None:
      # when started the first time, set the current_index variable
      self.set_start_index(self.live_data_idx)

    while True:
      retries=0
      #+++++++++++++ Adding data to the plot that has already been translated ++++++++++++++++#
      while self.live_data_idx>self.current_index:
        if not self.reflectivity_active:
          self.start_new_reflectivity()
        if self.get_dsinfo(self.current_index) is None:
          # if for some reason the run never existed, continue directly
          if len(self.db('file_id>fid', fid=self.current_index))>0:
            retries=0
            self.finish_reflectivity()
            self.current_index+=1
            continue

          # if dataset not yet available, wait for translation service to create the file
          retries+=1
          sleep(60.)
          continue
        if retries>self.MAX_RETRIES:
          # give up when adding reflectivity was not successful after a few tries
          retries=0
          self.finish_reflectivity()
          self.current_index+=1
        self.add_dataset()
      #------------- Adding data to the plot that has already been translated ----------------#

      if os.path.getmtime(instrument.LIVE_DATA)==self.live_data_last_mtime:
        # the live data file has not changed, wait and try again
        sleep(10.)
        continue

      #+++++++++++++ Plotting the current reflectivity including the live data +++++++++++++++#
      # When all files up to the live data index have been added
      # we reread the live data to add it to the plot
      live_ds=qreduce.NXSData(instrument.LIVE_DATA, use_caching=False,
                              event_tof_overwrite=self.live_data_tof_overwrite)
      if live_ds is None:
        continue
      else:
        self.live_data_last_mtime=os.path.getmtime(instrument.LIVE_DATA)
      if live_ds.number>self.current_index:
        # if the current run has finished we increment the live data index and add
        # the dataset after translation, which is done in the first step of the main loop
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

    results=self.db('file_id>=start_id and file_id<end_id',
                    start_id=self.current_index-20,
                    end_id=self.current_index)
    results=results.sort_by('-file_id')
    for result in results:
      if abs(result.ai)<0.1:
        break
      if result.ai>(last_ai*1.05) and (abs(result.ai-last_ai)>0.01
                                      or result.lambda_center<=last_lambda):
        break
      if result.no_states!=last_channels:
        break
      last_ai=result.ai
      last_lambda=result.lambda_center
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
      self.reflectivity_last_ai=self.get_ai(live_ds)
      self.reflectivity_last_lamda=live_ds.lambda_center
      self.reflectivity_states=len(live_ds.keys())
      self.reflectivity_active=True
      self.state_names=None
      return True
    else:
      # the first dataset is already translated, use database information to begin reflecitvity
      dsinfo=self.get_dsinfo(self.current_index)
      if dsinfo is None:
        return False
      elif dsinfo.ai<0.1:
        self.current_index+=1
        return False
      logging.info('Creating new reflectivity starting at index %i.'%self.current_index)
      self.reflectivity_items=[]
      self.reflectivity_last_ai=dsinfo.ai
      self.reflectivity_last_lamda=dsinfo.lambda_center
      self.reflectivity_states=dsinfo.no_states
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
    if dsinfo is None:
      # dataset is not yet in database, go back to the main loop, which will wait for it
      return False
    if dsinfo.ai<(self.reflectivity_last_ai*0.95) or dsinfo.no_states!=self.reflectivity_states:
      # The currenct reflectivity is finished, as this dataset does not correspond to
      # it. Return to the main loop, which will try to add the dataset again.
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
    self.reflectivity_last_ai=dsinfo.ai
    self.reflectivity_last_lamda=dsinfo.lambda_center
    self.live_data_tof_overwrite=data[0].tof_edges
    return True

  def create_live_refl(self, live_ds):
    '''
    Read the file for the current index and create the reflecitvity for each state.
    '''
    if not self.reflectivity_active:
      return None
    xpix=float(qcalc.get_xpos(live_ds[0]))
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
        # don't export empty reflectivityies
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
      res=self.db.add_record(index)
      if res:
        return self.db(file_id=index)[0]
      else:
        return None
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

  def combine_reflectivity(self, live_add=[]):
    '''
    Create plottable arrays from the extracted reflectivities.
    '''
    xitems=[[] for ignore in range(self.reflectivity_states)]
    yitems=[[] for ignore in range(self.reflectivity_states)]
    for items in self.reflectivity_items+live_add:
      P0=items[0].options['P0']
      PN=items[0].options['PN']
      Pfrom, Pto=PN, len(items[0].R)-P0
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
    return out

  def plot_reflectivity(self, data, fname, title='', highres=False):
    logging.info('Saving plot to "%s".'%fname)
    if highres:
      fig=Figure(figsize=(10.667, 8.), dpi=150, facecolor='#FFFFFF')
    else:
      fig=Figure(figsize=(6., 4.), dpi=72, facecolor='#FFFFFF')
    fig.subplots_adjust(left=0.12, bottom=0.13, top=0.94, right=0.98)
    canvas=FigureCanvasAgg(fig)
    ax=fig.add_subplot(111)

    ymin=1e10
    ymax=1e-10
    for x, y, label in data:
      try:
        ymin=min(y[y>0].min(), ymin)
      except ValueError:
        # ignore plots with zero intensity
        continue
      ymax=max(y.max(), ymax)
      ax.semilogy(x, y, label=label)
    ax.set_xlim(x.min()-x.min()%0.005, x.max()-x.max()%0.005+0.005)
    ax.set_ylim(ymin*0.75, ymax*1.25)
    ax.legend()
    ax.set_title(title)
    ax.set_xlabel('Q [$\\AA^{-1}$]')
    ax.set_ylabel('R')
    canvas.print_png(fname)

  def get_ai(self, ds):
    data=ds[0]
    xpix=float(qcalc.get_xpos(data))

    grad_per_pixel=data.det_size_x/data.dist_sam_det/data.xydata.shape[1]*180./numpy.pi
    tth=(data.dangle-data.dangle0)+(data.dpix-xpix)*grad_per_pixel
    return tth/2.
