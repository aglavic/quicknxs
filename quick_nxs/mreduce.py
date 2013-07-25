#-*- coding: utf-8 -*-
'''
Module for data readout and evaluation of the SNS Magnetism Reflectometer.
Can also be used stand alone for e.g. interactive processing
or scripts, therefore it is kept as only one file. The only dependencies
are numpy and the h5py module, which is an interface to the HDF5 file format
C-library, on which Nexus files are based.

The NXSData object reads a full .nxs file (histogram and event mode) and analysis
it's content for the channels that have been measured. It can be use as a list
or dictionary to access these channels as MRDataset objects.

The Relflectivity extracts a reflectiviy from a MRDataset object and
storing the result as well as some intermediate data in itself as attributes.
'''

import os
import sys
from copy import deepcopy
from glob import glob
from numpy import *
from logging import debug, info, warn #@Reimport
import h5py
from time import time, strptime, mktime
# ignore zero devision error
#seterr(invalid='ignore')

try:
  from .decorators import log_call, log_input, log_both
  from .config import PATHS, BASE_SEARCH, OLD_BASE_SEARCH
except ImportError:
  # just in case module is used separately
  BASE_SEARCH, OLD_BASE_SEARCH='', ''
  PATHS={}
  def log_call(func): return func
  def log_input(func): return func
  def log_both(func): return func


### Parameters needed for some calculations.
H_OVER_M_NEUTRON=3.956034e-7 # h/m_n [m²/s]
DETECTOR_X_REGION=(8, 295) # the active area of the detector
DETECTOR_Y_REGION=(8, 246)
ANALYZER_IN=(0., 100.) # position and maximum deviation of analyzer in it's working position
POLARIZER_IN=(-348., 50.) # position and maximum deviation of polarizer in it's working position
# measurement type mapping of states
MAPPING_FULLPOL=(
                 (u'++', u'entry-Off_Off'),
                 (u'--', u'entry-On_On'),
                 (u'+-', u'entry-Off_On'),
                 (u'-+', u'entry-On_Off'),
                 )
MAPPING_HALFPOL=(
                 (u'+', u'entry-Off_Off'),
                 (u'-', u'entry-On_Off'),
                 )
MAPPING_UNPOL=(
               (u'x', u'entry-Off_Off'),
               )
MAPPING_EFIELD=(
                (u'0V', u'entry-Off_Off'),
                (u'+V', u'entry-On_Off'),
                (u'-V', u'entry-Off_On'),
                )

# used for * imports
__all__=['NXSData', 'Reflectivity', 'OffSpecular', 'GISANS']

if sys.platform.startswith('win'):
  _caching_available=False
else:
  _caching_available=True

class NXSData(object):
  '''
  Class for readout and evaluation of histogram and event mode .nxs files,
  which also stores the data to be accessed by attributes.
  
  The object can be used as a ordered dictionary or list of channels,
  where each channel is a MRDataset object.
  
  The generator takes several keyword arguments to control the readout:
  
    * use_caching=True: If files should be cached for faster future readouts (last 20 files)
    * bin_type='0: linear in ToF'/'1: linear in Q' - use linear or 1/x spacing for ToF channels in event mode
    * bins=40: Number of ToF bins for event mode
  '''
  DEFAULT_OPTIONS=dict(bin_type=0, bins=40, use_caching=_caching_available, callback=None,
                       event_split_bins=None, event_split_index=0,
                       event_tof_overwrite=None)
  COUNT_THREASHOLD=100
  MAX_CACHE=20
  _cache=[]

  @log_both
  def __new__(cls, filename, **options):
    all_options=dict(cls.DEFAULT_OPTIONS)
    for key, value in options.items():
      if not key in all_options:
        raise ValueError, "%s is not a known option parameter"%key
      all_options[key]=value
    filename=os.path.abspath(filename)
    cached_names=[item.origin for item in cls._cache]
    if all_options['use_caching'] and filename in cached_names:
      cache_index=cached_names.index(filename)
      cached_object=cls._cache[cache_index]
      compare_options=dict(all_options)
      compare_options['callback']=None
      if cached_object._options==compare_options:
        return cached_object
    # else
    self=object.__new__(cls)
    self._options=all_options
    # create empty attributes
    self._channel_names=[]
    self._channel_origin=[]
    self._channel_data=[]
    self.measurement_type=""
    self.origin=filename
    # process the file
    self._read_times=[]

    if not self._read_file(filename):
      return None
    if all_options['use_caching']:
      if filename in cached_names:
        cache_index=cached_names.index(filename)
        cls._cache.pop(cache_index)
      # make sure cache does not get bigger than MAX_CACHE items or 80% of available memory
      while len(cls._cache)>=cls.MAX_CACHE:
        cls._cache.pop(0)
      cls._cache.append(self)
    # remove callback function to make the object Pickleable
    self._options['callback']=None
    return self

  def _read_file(self, filename):
    '''
    Load data from a Nexus file.
    '''
    start=time()
    if self._options['callback']:
      self._options['callback'](0.)
    try:
      nxs=h5py.File(filename, mode='r')
    except IOError:
      return False
    # analyze channels
    channels=nxs.keys()
    if channels==['entry']:
      # ancient file format with polarizations in different files
      nxs=self._get_ancient(filename)
      channels=nxs.keys()
      channels.sort()
      is_ancient=True
    else:
      is_ancient=False
    for channel in list(channels):
      if nxs[channel][u'total_counts'].value[0]<self.COUNT_THREASHOLD:
        channels.remove(channel)
    if len(channels)==0:
      return False
    ana=nxs[channels[0]]['instrument/analyzer/AnalyzerLift/value'].value[0]
    pol=nxs[channels[0]]['instrument/polarizer/PolLift/value'].value[0]

    # select the type of measurement that has been used
    if abs(ana-ANALYZER_IN[0])<ANALYZER_IN[1]: # is analyzer is in position
      self.measurement_type='Polarization Analysis'
      mapping=MAPPING_FULLPOL
    elif abs(pol-POLARIZER_IN[0])<POLARIZER_IN[1]: # is polarizer is in position
      self.measurement_type='Polarized'
      mapping=MAPPING_HALFPOL
    elif 'DASlogs' in nxs[channels[0]] and \
          nxs[channels[0]]['DASlogs'].get('SP_HV_Minus') is not None and \
          channels!=[u'entry-Off_Off']: # is E-field cart connected and not only 0V measured
      self.measurement_type='Electric Field'
      mapping=MAPPING_EFIELD
    elif len(channels)==1:
      self.measurement_type='Unpolarized'
      mapping=MAPPING_UNPOL
    else:
      self.measurement_type='Unknown'
      mapping=[(channel, channel) for channel in channels]

    # get runtime for event mode splitting
    total_duration=time_from_header('', nxs=nxs)

    progress=0.1
    if self._options['callback']:
      self._options['callback'](progress)
    self._read_times.append(time()-start)
    i=1
    empty_channels=[]
    for dest, channel in mapping:
      if channel not in channels:
        continue
      raw_data=nxs[channel]
      if filename.endswith('event.nxs'):
        data=MRDataset.from_event(raw_data, self._options,
                                  callback=self._options['callback'],
                                  callback_offset=progress,
                                  callback_scaling=0.9/len(channels),
                                  tof_overwrite=self._options['event_tof_overwrite'],
                                  total_duration=total_duration)
        if data is None:
          # no data in channel, don't add it
          empty_channels.append(dest)
          continue
      elif filename.endswith('histo.nxs'):
        data=MRDataset.from_histogram(raw_data, self._options)
      else:
        data=MRDataset.from_old_format(raw_data, self._options)
      self._channel_data.append(data)
      self._channel_names.append(dest)
      self._channel_origin.append(channel)
      progress=0.1+0.9*float(i)/len(channels)
      if self._options['callback']:
        self._options['callback'](progress)
      i+=1
      self._read_times.append(time()-self._read_times[-1]-start)
    #print time()-start
    if not is_ancient:
      nxs.close()
    if empty_channels:
      warn('No counts for state %s'%(','.join(empty_channels)))
    return True

  def _get_ancient(self, filename):
    '''
    For the oldest file format, where polarization channels
    are in different .nxs files, this method reads all files
    and builds a dictionary of it.
    '''
    base_name=filename.rsplit("_p", 1)[0]
    files=glob(base_name+"*.nxs")
    nxs={}
    for name in files:
      key=name.split(base_name)[1][1:-4]
      item=h5py.File(name, mode='r')
      nxs[key]=item['entry']
    return nxs

  def __getitem__(self, item):
    if type(item)==int:
      return self._channel_data[item]
    else:
      if item in self._channel_names:
        return self._channel_data[self._channel_names.index(item)]
      elif item in self._channel_origin:
        return self._channel_data[self._channel_origin.index(item)]
      else:
        raise KeyError, "No such channel: %s"%str(item)

  def __setitem__(self, item, data):
    if type(item)==int:
      self._channel_data[item]=data
    else:
      if item in self._channel_names:
        self._channel_data[self._channel_names.index(item)]=data
      elif item in self._channel_origin:
        self._channel_data[self._channel_origin.index(item)]=data
      else:
        raise KeyError, "No such channel: %s"%str(item)

  def __len__(self):
    return len(self._channel_data)

  def __repr__(self):
    output=self.__class__.__name__+'({'
    spacer0=" "*(len(output)-1)
    for key, value in self.items():
      output+="\n%s '%s': %s,"%(spacer0, key, repr(value))
    output=output[:-1]+'\n'+spacer0+'})'
    return output

  def keys(self):
    return self._channel_names

  def values(self):
    return self._channel_data

  def items(self):
    return zip(self.keys(), self.values())

  def numitems(self):
    ''':return: three items tuples of the channel index, name and data'''
    return zip(xrange(len(self.keys())), self.keys(), self.values())

  def __iter__(self):
    for item in self.values():
      yield item

  @classmethod
  def get_cachesize(cls):
    """
    Return the total amount of memory used by the cached datasets.
    """
    return sum([ds.nbytes for ds in cls._cache])

  # easy access properties common to all datasets
  # return the size of the data stored in memory for all states of this file
  @property
  def nbytes(self): return sum([ds.nbytes for ds in self])

  @property
  def lambda_center(self): return self[0].lambda_center
  @property
  def number(self): return self[0].number
  @property
  def experiment(self): return self[0].experiment
  @property
  def merge_warnings(self): return self[0].merge_warnings
  @property
  def dpix(self): return self[0].dpix
  @property
  def dangle(self): return self[0].dangle
  @property
  def dangle0(self): return self[0].dangle0
  @property
  def sangle(self): return self[0].sangle


class NXSMultiData(NXSData):
  '''
  Sum up data of several nxs files.
  '''
  _progress=0.
  _progress_items=1
  _callback=None

  def __new__(cls, filenames, **options):
    if not hasattr(filenames, '__iter__') or len(filenames)==0:
      raise ValueError, 'File names needs to be an iterable of length > 0'
    options['use_caching']=False # caching would return NXSData type objects
    filenames.sort()
    if 'callback' in options and options['callback'] is not None:
      cls._callback=options['callback']
      cls._progress_items=len(filenames)
      cls._progress=0.
      options['callback']=cls._callback_sum
    self=NXSData.__new__(cls, filenames[0], **options)
    numbers=[self.number]
    for i, filename in enumerate(filenames[1:]):
      cls._progress=(i+1.)/cls._progress_items
      other=NXSData(filename, **options)
      if len(self._channel_data)!=len(other._channel_data):
        raise ValueError, 'Files can not be combined due to different number of statess'
      self._add_data(other)
      numbers.append(other.number)
    self.origin=filenames
    return self

  def _add_data(self, other):
    '''
    Add the counts of all channels to this dataset channels 
    and increase the proton charge equally.
    '''
    for key, value in self.items():
      value+=other[key]

  @classmethod
  def _callback_sum(cls, progress):
    cls._callback(cls._progress+progress/cls._progress_items)


class MRDataset(object):
  '''
  Representation of one measurement channel of the reflectometer
  including meta data.
  '''
  proton_charge=0.
  total_counts=0
  tof_edges=None
  dangle=0. #°
  dangle0=4. #°
  sangle=0. #°
  mon_data=None

  # for resolution calculation
  slit1_width=3. # mm
  slit1_dist=2600. # mm
  slit2_width=2. # mm
  slit2_dist=2019. #mm
  slit3_width=0.05 # mm
  slit3_dist=714. # mm

  ai=None
  dpix=0
  lambda_center=3.37 #Å
  xydata=None
  xtofdata=None
  data=None
  logs={}
  log_units={}
  experiment=''
  number=0
  merge_warnings=''
  dist_mod_det=21.2535 #m
  dist_sam_det=2.55505 #m
  det_size_x=0.2128 #m
  det_size_y=0.1792 #m
  from_event_mode=False

  _Q=None
  _I=None
  _dI=None

  def __init__(self):
    '''
    Initialize an empty dataset. To actually load a Nexus file channel
    use the class methods from_histogram or from_event.
    '''
    self.origin=('none', 'none')

  @classmethod
  @log_call
  def from_histogram(cls, data, read_options):
    '''
    Create object from a histogram Nexus file.
    '''
    output=cls()
    output.read_options=read_options
    output._collect_info(data)

    output.tof_edges=data['bank1/time_of_flight'].value
    # the data arrays
    output.data=data['bank1/data'].value.astype(float) # 3D dataset
    output.xydata=data['bank1']['data_x_y'].value.transpose().astype(float) # 2D dataset
    output.xtofdata=data['bank1']['data_x_time_of_flight'].value.astype(float) # 2D dataset

    mon_tof_from=data['monitor1']['time_of_flight'].value.astype(float)*\
                                          output.dist_mod_det/output.dist_mod_mon
    mon_I_from=data['monitor1']['data'].value.astype(float)
    mod_data=histogram((mon_tof_from[:-1]+mon_tof_from[1:])/2., output.tof_edges,
                       weights=mon_I_from)[0]
    output.mon_data=mod_data
    return output

  @classmethod
  @log_call
  def from_old_format(cls, data, read_options):
    '''
    Create object from a histogram Nexus file.
    '''
    output=cls()
    output.read_options=read_options
    output._collect_info(data)

    # first ToF edge is 0, prevent that
    output.tof_edges=data['bank1/time_of_flight'].value[1:]
    # the data arrays
    output.data=data['bank1/data'].value.astype(float)[:, :, 1:] # 3D dataset
    output.xydata=output.data.sum(axis=2).transpose()
    output.xtofdata=output.data.sum(axis=1)
    return output

  @classmethod
  @log_call
  def from_event(cls, data, read_options,
                 callback=None, callback_offset=0., callback_scaling=1.,
                 total_duration=None,
                 tof_overwrite=None):
    '''
    Load data from a Nexus file containing event information.
    Creates 3D histogram with ither linear or 1/t spaced 
    time of flight channels. The result has the same format as
    from the read_file function.
    '''
    output=cls()
    output.read_options=read_options
    output.from_event_mode=True
    bin_type=read_options['bin_type']
    bins=read_options['bins']
    output._collect_info(data)

    if tof_overwrite is None:
      lcenter=data['DASlogs/LambdaRequest/value'].value[0]
      # ToF region for this specific central wavelength
      tmin=output.dist_mod_det/H_OVER_M_NEUTRON*(lcenter-1.6)*1e-4
      tmax=output.dist_mod_det/H_OVER_M_NEUTRON*(lcenter+1.6)*1e-4
      if bin_type==0:
        tof_edges=linspace(tmin, tmax, bins+1)
      elif bin_type==1:
        tof_edges=1./linspace(1./tmin, 1./tmax, bins+1)
      else:
        raise ValueError, 'Unknown bin type %i'%bin_type
    else:
      tof_edges=tof_overwrite

    # Histogram the data
    # create pixel map
    x=arange(304)
    y=arange(256)
    Y, X=meshgrid(y, x)
    X=X.flatten()
    Y=Y.flatten()
    # create ToF edges for the binning and correlate pixel indices with pixel position
    tof_ids=array(data['bank1_events/event_id'].value, dtype=int)
    tof_time=data['bank1_events/event_time_offset'].value
    # read the corresponding proton charge of each pulse
    tof_pc=data['DASlogs/proton_charge/value'].value
    if read_options['event_split_bins']:
      split_bins=read_options['event_split_bins']
      split_index=read_options['event_split_index']
      # read the relative time in seconds from measurement start to event
      tof_real_time=data['bank1_events/event_time_zero'].value
      tof_idx_to_id=data['bank1_events/event_index'].value
      if total_duration is None:
        split_step=float(tof_real_time[-1]+0.01)/split_bins
      else:
        split_step=float(total_duration+0.01)/split_bins
      try:
        start_id, stop_id=where(((tof_real_time>=(split_index*split_step))&
                                 (tof_real_time<((split_index+1)*split_step))))[0][[0,-1]]
      except IndexError:
        debug('No pulses in selected range')
        return None

      if start_id==0:
        start_idx=0
      else:
        start_idx=tof_idx_to_id[start_id-1]
      stop_idx=tof_idx_to_id[stop_id]
      debug('Event split with %.1f<=t<%.1f yielding pulse/tof indices: [%i:%i]/[%i:%i]'
            %((split_index*split_step), ((split_index+1)*split_step),
              start_id, stop_id+1, start_idx, stop_idx)
            )
      tof_pc=tof_pc[start_id:stop_id+1]

      tof_ids=tof_ids[start_idx:stop_idx]
      tof_time=tof_time[start_idx:stop_idx]
      # correct the total count value for the number of neutrons in the selected range
      output.total_counts=tof_time.shape[0]
      if output.total_counts==0:
        debug('No counts in selected range')
        return None
    tof_x=X[tof_ids]
    tof_y=Y[tof_ids]
    # calculate total proton charge in the selected area
    output.proton_charge=tof_pc.sum()

    if callback is not None:
      # create the 3D binning
      ssize=1e5
      Ixyt, D=histogramdd(vstack([tof_x[:ssize], tof_y[:ssize], tof_time[:ssize]]).transpose(),
                         bins=(arange(305)-0.5, arange(257)-0.5, tof_edges))
      steps=int(tof_x.shape[0]/ssize)
      callback(callback_offset+callback_scaling*1/(steps+1))
      for i in range(1, steps+1):
        Ixyti, D=histogramdd(vstack([tof_x[ssize*i:ssize*(i+1)], tof_y[ssize*i:ssize*(i+1)],
                                     tof_time[ssize*i:ssize*(i+1)]]).transpose(),
                           bins=(arange(305)-0.5, arange(257)-0.5, tof_edges))
        Ixyt+=Ixyti
        callback(callback_offset+callback_scaling*(i+1)/(steps+1))
    else:
      # create the 3D binning
      Ixyt, D=histogramdd(vstack([tof_x, tof_y, tof_time]).transpose(),
                         bins=(arange(305)-0.5, arange(257)-0.5, tof_edges))
    # create projections for the 2D datasets
    Ixy=Ixyt.sum(axis=2)
    Ixt=Ixyt.sum(axis=1)
    # store the data
    output.tof_edges=D[2]
    output.data=Ixyt.astype(float) # 3D dataset
    output.xydata=Ixy.transpose().astype(float) # 2D dataset
    output.xtofdata=Ixt.astype(float) # 2D dataset
    return output

  def _collect_info(self, data):
    self.origin=(os.path.abspath(data.file.filename), data.name.lstrip('/'))
    self.logs={}
    self.log_minmax={}
    self.log_units={}
    if 'DASlogs' in data:
      # the old format does not include the DAS logs
      for motor, item in data['DASlogs'].items():
        try:
          self.logs[motor]=item['average_value'].value[0]
          if 'units' in item['average_value'].attrs:
            self.log_units[motor]=item['average_value'].attrs['units']
          else:
            self.log_units[motor]=u''
          self.log_minmax[motor]=(item['minimum_value'].value[0],
                                  item['maximum_value'].value[0])
        except:
          continue
      self.lambda_center=data['DASlogs/LambdaRequest/value'].value[0]
    self.dangle=data['instrument/bank1/DANGLE/value'].value[0]
    if 'instrument/bank1/DANGLE0' in data: # compatibility for ancient file format
      self.dangle0=data['instrument/bank1/DANGLE0/value'].value[0]
      self.dpix=data['instrument/bank1/DIRPIX/value'].value[0]
      self.slit1_width=data['instrument/aperture1/S1HWidth/value'].value[0]
      self.slit2_width=data['instrument/aperture2/S2HWidth/value'].value[0]
      self.slit3_width=data['instrument/aperture3/S3HWidth/value'].value[0]
    else:
      self.slit1_width=data['instrument/aperture1/RSlit1/value'].value[0]-\
                      data['instrument/aperture1/LSlit1/value'].value[0]
      self.slit2_width=data['instrument/aperture2/RSlit2/value'].value[0]-\
                      data['instrument/aperture2/LSlit2/value'].value[0]
      self.slit3_width=data['instrument/aperture3/RSlit3/value'].value[0]-\
                      data['instrument/aperture3/LSlit3/value'].value[0]
    self.slit1_dist=-data['instrument/aperture1/distance'].value[0]*1000.
    self.slit2_dist=-data['instrument/aperture2/distance'].value[0]*1000.
    self.slit3_dist=-data['instrument/aperture3/distance'].value[0]*1000.

    self.sangle=data['sample/SANGLE/value'].value[0]

    self.proton_charge=data['proton_charge'].value[0]
    self.total_counts=data['total_counts'].value[0]

    self.dist_sam_det=data['instrument/bank1/SampleDetDis/value'].value[0]*1e-3
    self.dist_mod_det=data['instrument/moderator/ModeratorSamDis/value'].value[0]*1e-3+self.dist_sam_det
    self.dist_mod_mon=data['instrument/moderator/ModeratorSamDis/value'].value[0]*1e-3-2.75
    self.det_size_x=data['instrument/bank1/origin/shape/size'].value[0]
    self.det_size_y=data['instrument/bank1/origin/shape/size'].value[1]

    self.experiment=str(data['experiment_identifier'].value[0])
    self.number=int(data['run_number'].value[0])
    self.merge_warnings=str(data['SNSproblem_log_geom/data'].value[0])

  def __repr__(self):
    if type(self.origin) is tuple:
      return "<%s '%s' counts: %i>"%(self.__class__.__name__,
                                     "%s/%s"%(os.path.basename(self.origin[0]), self.origin[1]),
                                     self.total_counts)
    else:
      return "<%s '%s' counts: %i>"%(self.__class__.__name__,
                                     "SUM"+repr(self.number),
                                     self.total_counts)

  def __iadd__(self, other):
    '''
    Add the data of one dataset to this dataset.
    '''
    self.data+=other.data
    self.xydata+=other.xydata
    self.xtofdata+=other.xtofdata
    self.total_counts+=other.total_counts
    self.proton_charge+=other.proton_charge
    if type(self.number) is list:
      self.number.append(other.number)
      self.origin.append(other.origin)
    else:
      self.number=[self.number, other.number]
      self.origin=[self.origin, other.origin]
    return self
    #self.origin.append(other.origin)

  def __add__(self, other):
    '''
    Add two datasets.
    '''
    output=deepcopy(self)
    output+=other
    return output

  ################## Properties for easy data access ##########################
  # return the size of the data stored in memory for this dataset
  @property
  def nbytes(self): return (self.data.nbytes+self.xydata.nbytes+self.xtofdata.nbytes)

  @property
  def xdata(self): return self.xydata.mean(axis=0)

  @property
  def ydata(self): return self.xydata.mean(axis=1)

  @property
  def tofdata(self): return self.xtofdata.mean(axis=0)

  # coordinates corresponding to the data items
  @property
  def x(self): return arange(self.xydata.shape[1])

  @property
  def y(self): return arange(self.xydata.shape[0])

  @property
  def xy(self): return meshgrid(self.x, self.y)

  @property
  def tof(self): return (self.tof_edges[:-1]+self.tof_edges[1:])/2.

  @property
  def xtof(self): return meshgrid(self.tof, self.x)

  @property
  def lamda(self):
    v_n=self.dist_mod_det/self.tof*1e6 #m/s
    lamda_n=H_OVER_M_NEUTRON/v_n*1e10 #A
    return lamda_n

def time_from_header(filename, nxs=None):
  '''
  Read just an edf header to get the time of a measurement in seconds.
  '''
  if nxs is None:
    try:
      nxs=h5py.File(filename, mode='r')
    except IOError:
      return None
    close=True
  else:
    close=False
  stime=1.e30
  etime=0.
  for item in nxs.values():
    if '.' in str(item['start_time'].value[0]):
      start_str, start_sub=str(item['start_time'].value[0]).split('.', 1)
      start_sub=start_sub.split('-')[0]
      start_time=mktime(strptime(start_str, '%Y-%m-%dT%H:%M:%S'))+float('.'+start_sub)
      end_str, end_sub=str(item['end_time'].value[0]).split('.', 1)
      end_sub=start_sub.split('-')[0]
      end_time=mktime(strptime(end_str, '%Y-%m-%dT%H:%M:%S'))+float('.'+end_sub)
    else:
      start_str, start_sub=str(item['start_time'].value[0]).rsplit('-', 1)
      start_time=mktime(strptime(start_str, '%Y-%m-%dT%H:%M:%S'))
      end_str, end_sub=str(item['end_time'].value[0]).rsplit('-', 1)
      end_time=mktime(strptime(end_str, '%Y-%m-%dT%H:%M:%S'))
    stime=min(stime, start_time)
    etime=max(etime, end_time)
  if close:
    nxs.close()
  return etime-stime

def locate_file(number, histogram=True, old_format=False):
    '''
    Search the data folders for a specific file number and open it.
    '''
    info('Trying to locate file number %s...'%number)
    if histogram:
      search=glob(os.path.join(PATHS['data_base'], (BASE_SEARCH%number)+u'histo.nxs'))
    elif old_format:
      search=glob(os.path.join(PATHS['data_base'], (OLD_BASE_SEARCH%(number, number))+u'.nxs'))
    else:
      search=glob(os.path.join(PATHS['data_base'], (BASE_SEARCH%number)+u'event.nxs'))
    if search:
      return search[0]
    else:
      return None

class Reflectivity(object):
  """
  Extraction of reflectivity from MRDatatset object storing all data
  and options used for the extraction process.
  """
  DEFAULT_OPTIONS=dict(
       x_pos=None,
       x_width=9,
       y_pos=102,
       y_width=204,
       bg_pos=80,
       bg_width=40,
       tth=None,
       dpix=None,
       scale=1.,
       sample_length=10., # mm - used to calculate the angular resolution
       extract_fan=False, # Treat every x-pixel separately and join the data afterwards
       normalization=None, # another Reflectivity object used for normalization
       bg_tof_constant=False, # treat background to be independent of wavelength for better statistics
       bg_poly_regions=None, # use polygon regions in x/λ to determine which points to use for the background
       bg_scale_xfit=False, # use a linear fit on x-axes projection to scale the background
       bg_scale_factor=1.,
       P0=0,
       PN=0,
       number='0',
       gisans_gridy=50,
       gisans_gridz=50,
       )

  @log_input
  def __init__(self, dataset, **options):
    all_options=dict(Reflectivity.DEFAULT_OPTIONS)
    for key, value in options.items():
      if not key in all_options:
        raise ValueError, "%s is not a known option parameter"%key
      all_options[key]=value
    self.options=all_options
    self.origin=dataset.origin
    self.read_options=dataset.read_options
    if self.options['x_pos'] is None:
      # if nor x_pos is given, use the value from the dataset
      rad_per_pixel=dataset.det_size_x/dataset.dist_sam_det/dataset.xydata.shape[1]
      self.options['x_pos']=dataset.dpix-dataset.sangle/180.*pi/rad_per_pixel
    if self.options['tth'] is None:
      self.options['tth']=dataset.dangle-dataset.dangle0
    if self.options['dpix'] is None:
      self.options['dpix']=dataset.dpix
    self.lambda_center=dataset.lambda_center
    self.slits=[(dataset.slit1_width, dataset.slit1_dist),
                (dataset.slit2_width, dataset.slit2_dist),
                (dataset.slit3_width, dataset.slit3_dist)]

    if all_options['extract_fan'] and all_options['normalization'] is not None:
      self._calc_fan(dataset)
    else:
      self._calc_normal(dataset)

  def __repr__(self):
    if type(self.origin) is list:
      fnames='+'.join([os.path.basename(item[0]) for item in self.origin])
      output='<Reflectivity[%i] "%s/%s"'%(len(self.Q), fnames,
                                        self.origin[0][1])
    else:
      output='<Reflectivity[%i] "%s/%s"'%(len(self.Q), os.path.basename(self.origin[0]),
                                        self.origin[1])
    if self.options['normalization'] is None:
      output+=' NOT normalized'
    elif self.options['extract_fan']:
      output+=' FAN'
    output+='>'
    return output

  #############################################################################

  @log_call
  def _calc_normal(self, dataset):
    """
    Extract reflectivity from 3D dataset I(x,y,ToF).
    Uses a window in x and y to filter the 3D data and than sums all I values 
    for each ToF channel. Qz is calculated using the x window center position
    together with the tth-bank and direct pixel values. 
    Error is also calculated and all intermediate steps are stored in the object 
    (scaled and unscaled intensity and background).
    
    :param dataset: MRDataset object
    """
    tof_edges=dataset.tof_edges
    data=dataset.data
    x_pos=self.options['x_pos']
    x_width=self.options['x_width']
    y_pos=self.options['y_pos']
    y_width=self.options['y_width']
    scale=1./dataset.proton_charge # scale by user factor

    # Get regions in pixels as integers
    reg=map(lambda item: int(round(item)),
            [x_pos-x_width/2., x_pos+x_width/2.+1,
             y_pos-y_width/2., y_pos+y_width/2.+1])
    debug('Reflectivity region: %s'%str(reg))

    # get incident angle of reflected beam
    rad_per_pixel=dataset.det_size_x/dataset.dist_sam_det/dataset.xydata.shape[1]
    relpix=self.options['dpix']-x_pos
    tth=(self.options['tth']*pi/180.+relpix*rad_per_pixel)
    self.ai=tth/2.
    # calculate resolution from slits, sample size and incident angle
    dai=self.get_resolution()
    debug('alpha_i=%s+/-%s'%(self.ai, dai))

    self._calc_bg(dataset)

    # restrict the intensity and background data to the given regions
    Idata=data[reg[0]:reg[1], reg[2]:reg[3], :]
    # calculate region size for later use
    size_I=float((reg[3]-reg[2])*(reg[1]-reg[0]))
    # calculate ROI intensities and normalize by number of points
    self.Iraw=Idata.sum(axis=0).sum(axis=0)
    self.I=self.Iraw/(size_I/scale)
    self.dIraw=sqrt(self.Iraw)
    self.dI=self.dIraw/(size_I/scale)
    debug("Intensity scale is %s/%s=%s"%(scale, size_I, scale/size_I))

    v_edges=dataset.dist_mod_det/tof_edges*1e6 #m/s
    lamda_edges=H_OVER_M_NEUTRON/v_edges*1e10 #A
    # store the ToF as well for comparison etc.
    self.tof=(tof_edges[:-1]+tof_edges[1:])/2. # µs
    self.lamda=(lamda_edges[:-1]+lamda_edges[1:])/2.
    # resolution for lambda is digital range with equal probability
    # therefore it is the bin size divided by sqrt(12)
    self.dlamda=abs(lamda_edges[:-1]-lamda_edges[1:])/sqrt(12)

    # for reflectivity use Q as x
    self.Q=4.*pi/self.lamda*sin(self.ai)
    # error propagation from lambda and angular resolution
    self.dQ=4*pi*sqrt((self.dlamda/self.lamda**2*sin(self.ai))**2+
                      (cos(self.ai)*dai/self.lamda)**2)
    debug("Q=%s"%repr(self.Q))
    # finally scale reflectivity by the given factor and beam width
    self.Rraw=(self.I-self.BG) # used for normalization files
    self.dRraw=sqrt(self.dI**2+self.dBG**2)
    if self.ai>0.0002:
      sin_scale=0.005/sin(self.ai) # scale by beam-footprint
    else:
      sin_scale=1.
    self.R=sin_scale*self.options['scale']*self.Rraw
    self.dR=sin_scale*self.options['scale']*self.dRraw

    if self.options['normalization']:
      norm=self.options['normalization']
      debug("Performing normalization from %s"%norm)
      idxs=norm.Rraw>0.
      self.dR[idxs]=sqrt(
                   (self.dR[idxs]/norm.Rraw[idxs])**2+
                   (self.R[idxs]/norm.Rraw[idxs]**2*norm.dRraw[idxs])**2
                   )
      self.R[idxs]/=norm.Rraw[idxs]
      self.R[logical_not(idxs)]=0.
      self.dR[logical_not(idxs)]=0.

  @log_call
  def _calc_fan(self, dataset):
    """
    Extract reflectivity from 4D dataset (x,y,ToF,I).
    Uses a window in x and y to filter the 4D data
    and than sums all I values for each ToF channel.
    
    In contrast to calc_reflectivity this function assumes
    that a brought region reflected from a bend sample is
    analyzed, so each x line corresponds to different alpha i
    values.
    """
    tof_edges=dataset.tof_edges
    data=dataset.data
    x_pos=self.options['x_pos']
    x_width=self.options['x_width']
    y_pos=self.options['y_pos']
    y_width=self.options['y_width']
    scale=1./dataset.proton_charge # scale by user factor

    reg=map(lambda item: int(round(item)),
            [x_pos-x_width/2., x_pos+x_width/2.+1,
             y_pos-y_width/2., y_pos+y_width/2.+1])
    debug('Reflectivity region: %s'%str(reg))

    rad_per_pixel=dataset.det_size_x/dataset.dist_sam_det/dataset.xydata.shape[1]
    Idata=data[reg[0]:reg[1], reg[2]:reg[3], :]
    x_region=arange(reg[0], reg[1])
    relpix=self.options['dpix']-x_region
    tth=(self.options['tth']*pi/180.+relpix*rad_per_pixel)
    ai=tth/2.
    self.ai=ai.mean()
    dai_rel=self.get_resolution()/self.ai
    debug("Intensity scale is %s"%(scale))
    debug('alpha_i=%s'%repr(ai))

    self._calc_bg(dataset)

    v_edges=dataset.dist_mod_det/tof_edges*1e6 #m/s
    lamda_edges=H_OVER_M_NEUTRON/v_edges*1e10 #A
    self.tof=(tof_edges[:-1]+tof_edges[1:])/2. # µs
    self.lamda=(lamda_edges[:-1]+lamda_edges[1:])/2.
    # resolution for lambda is digital range with equal probability
    # therefore it is the bin size divided by sqrt(12)
    self.dlamda=abs(lamda_edges[:-1]-lamda_edges[1:])/sqrt(12)

    # calculate ROI intensities and normalize by number of points
    # still keeping it as 2D dataset
    self.Iraw=Idata.sum(axis=1)
    I=self.Iraw/(reg[3]-reg[2])*scale
    self.dIraw=sqrt(self.Iraw)
    dI=self.dIraw/(reg[3]-reg[2])*scale
    # For comparison store intensity summed over whole area
    self.I=I.sum(axis=0)/(reg[1]-reg[0])
    self.dI=sqrt((dI**2).sum(axis=0))/(reg[1]-reg[0])

    R=(I-self.BG[newaxis, :])*self.options['scale']
    dR=sqrt(dI**2+(self.dBG**2)[newaxis, :])*self.options['scale']
    if self.ai>0.0002:
      sin_scale=0.005/sin(self.ai) # scale by beam-footprint
      R*=sin_scale
      dR*=sin_scale

    norm=self.options['normalization']
    normR=where(norm.Rraw>0, norm.Rraw, 1.)
    # normalize each line by the incident intensity including error propagation
    dR=sqrt((dR/normR[newaxis, :])**2+(R*(norm.dR/normR**2)[newaxis, :])**2)
    R/=normR[newaxis, :]
    # reduce ToF region to points with incident intensity

    # calculate Q for each point of R
    Qz_edges=4.*pi/lamda_edges*sin(ai)[:, newaxis]
    Qz_centers=(Qz_edges[:, :-1]+Qz_edges[:, 1:])/2.
    #dQz=abs(Qz_edges[:, :-1]-Qz_edges[:, 1:])/2. #sqrt(12) error due to binning

    # create the Q bins to combine all R lines to
    # uses the smallest and largest Q all lines have in common with
    # a step size which has one point of every line in it.
    #Qz_start=Qz_edges[0,-1]
    Qz_start=Qz_edges[0, where(norm.Rraw>0)[0][-1]]
    Qz_end=Qz_edges[-1, where(norm.Rraw>0)[0][0]]
    Q=[]
    dQ=[]
    Rsum=[]
    ddRsum=[]
    Qz_edges_first=Qz_edges[0]
    Qz_edges_last=Qz_edges[-1]
    lines=range(Qz_edges.shape[0])
    ddR=dR**2
    for Qz_bin_low in reversed(Qz_edges_first[(Qz_edges_first<=Qz_end)&(Qz_edges_first>=Qz_start)]):
      # create a bin where at least one point from every
      # line is present
      try:
        # at least one point at the end can't be made into a bin this way
        Qz_bin_high=Qz_edges_last[Qz_edges_last>=Qz_bin_low][-2]
      except IndexError:
        break
      Q.append((Qz_bin_high+Qz_bin_low)/2.)
      # error is calculated from the relative binning size and angle resolutions
      dQ_rel=(Qz_bin_high-Qz_bin_low)/sqrt(12.)/Q[-1]
      dQ.append(sqrt(dQ_rel**2+dai_rel**2)*Q[-1])
      Rsumi=[]
      ddRsumi=[]
      for line in lines:
        # each line is treated equally in weight but there can be more than
        # one point per line in the same bin, so these are averaged
        select=(Qz_centers[line]>=Qz_bin_low)&(Qz_centers[line]<=Qz_bin_high)
        Rselect=R[line, select]
        ddRselect=ddR[line, select]
        Rsumi.append(Rselect.sum()/len(Rselect))
        ddRsumi.append(ddRselect.sum()/len(Rselect)**2)
      Rsum.append(array(Rsumi).sum())
      ddRsum.append(array(ddRsumi).sum())

    # sort the lists according to the default order from normal readout
    # and store them as numpy arrays
    Q.reverse()
    dQ.reverse()
    Rsum.reverse()
    ddRsum.reverse()
    self.dQ=array(dQ)
    self.Q=array(Q)
    self.R=array(Rsum)/len(lines)
    self.dR=sqrt(array(ddRsum))/len(lines)

  @log_call
  def _calc_bg(self, dataset):
    '''
    Calculate the background intensity vs. ToF.
    Equal for normal and fan reflectivity extraction.
    
    Methods supported:
        'data': Just take a region in x to extract an average count rate vs. ToF
    '''
    data=dataset.data
    y_pos=self.options['y_pos']
    y_width=self.options['y_width']
    bg_pos=self.options['bg_pos']
    bg_width=self.options['bg_width']
    bg_poly=self.options['bg_poly_regions']
    scale=1./dataset.proton_charge # scale by user factor

    # Get regions in pixels as integers
    reg=map(lambda item: int(round(item)),
            [bg_pos-bg_width/2., bg_pos+bg_width/2.+1,
             y_pos-y_width/2., y_pos+y_width/2.+1 ])
    debug('Background region: %s'%str(reg))


    if bg_poly:
      # create the background region from given polygons
      # for ToF channels without polygon region the normal positions are use
      from matplotlib.nxutils import points_inside_poly
      x=dataset.x
      lamda=dataset.lamda
      X, Lamda=meshgrid(x, lamda)
      points=vstack([Lamda.flatten(), X.flatten()]).transpose()
      points_in_region=zeros(X.shape, dtype=bool).flatten()
      for poly in bg_poly:
        points_in_region|=points_inside_poly(points, poly)
      points_in_region=points_in_region.reshape(X.shape)
      lamda_regions=unique(Lamda[points_in_region].flatten())
      # add missing lambda items from normal bg region
      for lamdai in lamda:
        if not lamdai in lamda_regions:
          points_in_region[:, reg[0]:reg[1]]|=(Lamda[:, reg[0]:reg[1]]==lamdai)
      points_in_region=points_in_region.astype(float)
      # sum over y
      bgydata=data[:, reg[2]:reg[3], :].sum(axis=1).transpose()
      # sum over x in the given region and devide by number of x-points used
      unscaled_bgdata=(bgydata*points_in_region).sum(axis=1)
      scaling_data=points_in_region.sum(axis=1)*float(reg[3]-reg[2])
      self.BGraw=unscaled_bgdata/scaling_data*scale
      self.dBGraw=sqrt(unscaled_bgdata)/scaling_data*scale
      debug("Background scale is %s"%(scale/scaling_data))
    else:
      # restrict the intensity and background data to the given regions
      bgdata=data[reg[0]:reg[1], reg[2]:reg[3], :]
      # calculate region size for later use
      size_BG=float((reg[3]-reg[2])*(reg[1]-reg[0]))
      # calculate ROI intensities and normalize by number of points
      self.BGraw=bgdata.sum(axis=0).sum(axis=0)
      self.dBGraw=sqrt(self.BGraw)/(size_BG/scale)
      self.BGraw/=size_BG/scale
      debug("Background scale is %s"%(scale/size_BG))
    if self.options['bg_tof_constant'] and self.options['normalization']:
      norm=self.options['normalization'].R
      reg=(self.dBGraw>0)&(norm>0)
      norm_BG=self.BGraw[reg]/norm[reg]
      norm_dBG=self.dBGraw[reg]/norm[reg]
      wmeanBG=(norm_BG/norm_dBG).sum()/(1./norm_dBG).sum()
      wmeandBG=sqrt(len(norm_BG))/(1./norm_dBG).sum()
      self.BG=wmeanBG*norm
      self.dBG=wmeandBG*norm
      # for the channels with fast neutron contribution just take the raw background
      fast_n_tof=[i*1.0e6/60. for i in range(3)]
      tof_edges=dataset.tof_edges
      for fnt in fast_n_tof:
        channel=where((tof_edges[1:]>=fnt)&(tof_edges[:-1]<=fnt))[0]
        if not channel:
          continue
        self.BG[channel]=self.BGraw[channel]
        self.dBG[channel]=self.dBGraw[channel]
    else:
      self.BG=self.BGraw.copy()
      self.dBG=self.dBGraw.copy()
    self.BG*=self.options['bg_scale_factor']
    self.dBG*=self.options['bg_scale_factor']

  def rescale(self, scaling):
    old_scale=self.options['scale']
    rescale=scaling/old_scale
    self.R*=rescale
    self.dR*=rescale
    self.options['scale']=scaling

  def get_resolution(self):
    '''
    Calculate the angular resolution given by all slits together with the sample size
    and return the smallest one.
    '''
    res=[]
    s_width=self.options['sample_length']*sin(self.ai)
    for width, dist in self.slits:
      # calculate the maximum opening angle dTheta
      dTheta=arctan((s_width/2.*(1.+width/s_width))/dist)*2.
      # standard deviation for a triangle shaped beam intensity distribution is dTheta / sqrt(6)
      res.append(dTheta*0.408)
    return min(res)

class OffSpecular(Reflectivity):
  '''
  Calculate off-specular scattering similarly as done for reflectivity.
  '''

  @log_input
  def __init__(self, dataset, **options):
    all_options=dict(OffSpecular.DEFAULT_OPTIONS)
    for key, value in options.items():
      if not key in all_options:
        raise ValueError, "%s is not a known option parameter"%key
      all_options[key]=value
    self.options=all_options
    self.origin=dataset.origin
    self.read_options=dataset.read_options
    if self.options['x_pos'] is None:
      # if nor x_pos is given, use the value from the dataset
      rad_per_pixel=dataset.det_size_x/dataset.dist_sam_det/dataset.xydata.shape[1]
      self.options['x_pos']=dataset.dpix-dataset.sangle/180.*pi/rad_per_pixel
    if self.options['tth'] is None:
      self.options['tth']=dataset.dangle-dataset.dangle0
    if self.options['dpix'] is None:
      self.options['dpix']=dataset.dpix
    self.lambda_center=dataset.lambda_center
    self.slits=[(dataset.slit1_width, dataset.slit1_dist),
                (dataset.slit2_width, dataset.slit2_dist),
                (dataset.slit3_width, dataset.slit3_dist)]

    self._calc_offspec(dataset)

  def __repr__(self):
    if type(self.origin) is list:
      fnames='+'.join([os.path.basename(item[0]) for item in self.origin])
      output='<OffSpecular[%i] "%s/%s"'%(len(self.Qz), fnames,
                                        self.origin[0][1])
    else:
      output='<OffSpecular[%i] "%s/%s"'%(len(self.Qz), os.path.basename(self.origin[0]),
                                        self.origin[1])
    if self.options['normalization'] is None:
      output+=' NOT normalized'
    output+='>'
    return output

  @log_call
  def _calc_offspec(self, dataset):
    """
    Extract off-specular scattering from 4D dataset (x,y,ToF,I).
    Uses a window in y to filter the 4D data
    and than sums all I values for each ToF and x channel.
    Qz,Qx,kiz,kfz is calculated using the x and ToF positions
    together with the tth-bank and direct pixel values.
    """
    tof_edges=dataset.tof_edges
    data=dataset.data
    x_pos=self.options['x_pos']
    x_width=self.options['x_width']
    y_pos=self.options['y_pos']
    y_width=self.options['y_width']
    scale=1./dataset.proton_charge # scale by user factor

    # Get regions in pixels as integers
    reg=map(lambda item: int(round(item)),
            [x_pos-x_width/2., x_pos+x_width/2.+1,
             y_pos-y_width/2., y_pos+y_width/2.+1])
    debug('Off-Specular region: %s'%str(reg))

    rad_per_pixel=dataset.det_size_x/dataset.dist_sam_det/dataset.xydata.shape[1]
    xtth=self.options['dpix']-arange(data.shape[0])[DETECTOR_X_REGION[0]:DETECTOR_X_REGION[1]]
    pix_offset_spec=self.options['dpix']-x_pos
    tth_spec=self.options['tth']*pi/180.+pix_offset_spec*rad_per_pixel
    af=self.options['tth']*pi/180.+xtth*rad_per_pixel-tth_spec/2.
    ai=ones_like(af)*tth_spec/2.
    self.ai=tth_spec/2.
    debug('alpha_i=%s'%self.ai)

    self._calc_bg(dataset)

    v_edges=dataset.dist_mod_det/tof_edges*1e6 #m/s
    lamda_edges=H_OVER_M_NEUTRON/v_edges*1e10 #A
    # store the ToF as well for comparison etc.
    self.tof=(tof_edges[:-1]+tof_edges[1:])/2. # µs
    self.lamda=(lamda_edges[:-1]+lamda_edges[1:])/2.
    # resolution for lambda is digital range with equal probability
    # therefore it is the bin size divided by sqrt(12)
    self.dlamda=abs(lamda_edges[:-1]-lamda_edges[1:])/sqrt(12)
    k=2.*pi/self.lamda

    # calculate reciprocal space, incident and outgoing perpendicular wave vectors
    self.Qz=k[newaxis, :]*(sin(af)+sin(ai))[:, newaxis]
    self.Qx=k[newaxis, :]*(cos(af)-cos(ai))[:, newaxis]
    self.ki_z=k[newaxis, :]*sin(ai)[:, newaxis]
    self.kf_z=k[newaxis, :]*sin(af)[:, newaxis]

    # calculate ROI intensities and normalize by number of points
    Idata=data[DETECTOR_X_REGION[0]:DETECTOR_X_REGION[1], reg[2]:reg[3], :]
    self.Iraw=Idata.sum(axis=1)
    self.dIraw=sqrt(self.Iraw)
    # normalize data by width in y and multiply scaling factor
    debug("Intensity scale is %s*%s=%s"%(scale/(reg[3]-reg[2]),
                                        self.options['scale'],
                                        self.options['scale']*scale/(reg[3]-reg[2])))
    self.I=self.Iraw/(reg[3]-reg[2])*scale
    self.dI=self.dIraw/(reg[3]-reg[2])*scale
    self.S=self.I-self.BG[newaxis, :]
    self.dS=sqrt(self.dI**2+(self.dBG**2)[newaxis, :])
    self.S*=self.options['scale']
    self.dS*=self.options['scale']

    if self.options['normalization']:
      norm=self.options['normalization']
      debug("Performing normalization from %s"%norm)
      idxs=norm.Rraw>0.
      self.dS[:, idxs]=sqrt(
                   (self.dS[:, idxs]/norm.Rraw[idxs][newaxis, :])**2+
                   (self.S[:, idxs]/norm.Rraw[idxs][newaxis, :]**2*norm.dRraw[idxs][newaxis, :])**2
                   )
      self.S[:, idxs]/=norm.Rraw[idxs][newaxis, :]
      self.S[:, logical_not(idxs)]=0.
      self.dS[:, logical_not(idxs)]=0.

class GISANS(Reflectivity):
  '''
  Calculate GISANS scattering from dataset.
  '''

  @log_input
  def __init__(self, dataset, **options):
    all_options=dict(OffSpecular.DEFAULT_OPTIONS)
    for key, value in options.items():
      if not key in all_options:
        raise ValueError, "%s is not a known option parameter"%key
      all_options[key]=value
    self.options=all_options
    self.origin=dataset.origin
    self.read_options=dataset.read_options
    if self.options['x_pos'] is None:
      # if nor x_pos is given, use the value from the dataset
      rad_per_pixel=dataset.det_size_x/dataset.dist_sam_det/dataset.xydata.shape[1]
      self.options['x_pos']=dataset.dpix-dataset.sangle/180.*pi/rad_per_pixel
    if self.options['tth'] is None:
      self.options['tth']=dataset.dangle-dataset.dangle0
    if self.options['dpix'] is None:
      self.options['dpix']=dataset.dpix
    self.lambda_center=dataset.lambda_center
    self.slits=[(dataset.slit1_width, dataset.slit1_dist),
                (dataset.slit2_width, dataset.slit2_dist),
                (dataset.slit3_width, dataset.slit3_dist)]

    self._calc_gisans(dataset)

  def __repr__(self):
    if type(self.origin) is list:
      fnames='+'.join([os.path.basename(item[0]) for item in self.origin])
      output='<OffSpecular[%i] "%s/%s"'%(len(self.Qz), fnames,
                                        self.origin[0][1])
    else:
      output='<OffSpecular[%i] "%s/%s"'%(len(self.Qz), os.path.basename(self.origin[0]),
                                        self.origin[1])
    if self.options['normalization'] is None:
      output+=' NOT normalized'
    output+='>'
    return output

  @log_call
  def _calc_gisans(self, dataset):
    """
    """
    tof_edges=dataset.tof_edges
    data=dataset.data
    x_pos=self.options['x_pos']
    y_pos=self.options['y_pos']
    # create a nicer intensity scale by multiplying with the reflectiviy extraction region
    scale=self.options['scale']/dataset.proton_charge # scale by user factor

    rad_per_pixel=dataset.det_size_x/dataset.dist_sam_det/dataset.xydata.shape[1]
    xtth=self.options['dpix']-arange(data.shape[0])[DETECTOR_X_REGION[0]:DETECTOR_X_REGION[1]]
    pix_offset_spec=self.options['dpix']-x_pos
    tth_spec=self.options['tth']*pi/180.+pix_offset_spec*rad_per_pixel
    af=self.options['tth']*pi/180.+xtth*rad_per_pixel-tth_spec/2.
    ai=ones_like(af)*tth_spec/2.
    phi=(arange(data.shape[1])[DETECTOR_Y_REGION[0]:DETECTOR_Y_REGION[1]]-y_pos)*rad_per_pixel
    debug('alpha_i=%s'%(tth_spec/2.))

    v_edges=dataset.dist_mod_det/tof_edges*1e6 #m/s
    lamda_edges=H_OVER_M_NEUTRON/v_edges*1e10 #A
    # store the ToF as well for comparison etc.
    self.tof=(tof_edges[:-1]+tof_edges[1:])/2. # µs
    self.lamda=(lamda_edges[:-1]+lamda_edges[1:])/2.
    # resolution for lambda is digital range with equal probability
    # therefore it is the bin size divided by sqrt(12)
    self.dlamda=abs(lamda_edges[:-1]-lamda_edges[1:])/sqrt(12)
    k=2.*pi/self.lamda

    # calculate ROI intensities and normalize by number of points
    P0=len(self.tof)-self.options['P0']
    PN=self.options['PN']
    Idata=data[DETECTOR_X_REGION[0]:DETECTOR_X_REGION[1],
               DETECTOR_Y_REGION[0]:DETECTOR_Y_REGION[1],
               PN:P0]
    # calculate reciprocal space, incident and outgoing perpendicular wave vectors
    self.Qx=k[newaxis, newaxis, PN:P0]*(cos(phi)*cos(af)[:, newaxis]-cos(ai)[:, newaxis])[:, :, newaxis]
    self.Qy=k[newaxis, newaxis, PN:P0]*(sin(phi)*cos(af)[:, newaxis])[:, :, newaxis]
    self.Qz=k[newaxis, newaxis, PN:P0]*((0*phi)+sin(af)[:, newaxis]+sin(ai)[:, newaxis])[:, :, newaxis]

    self.Iraw=Idata
    self.dIraw=sqrt(self.Iraw)
    # normalize data by width in y and multiply scaling factor
    self.I=self.Iraw*scale
    self.dI=self.dIraw*scale
    debug("Intensity scale is %s"%(scale))

    self.S=array(self.I)
    self.dS=array(self.dI)
    if self.options['normalization']:
      norm=self.options['normalization']
      debug("Performing normalization from %s"%norm)
      normR=norm.Rraw[PN:P0]
      normdR=norm.dRraw[PN:P0]
      idxs=normR>0.
      self.dS[:, :, idxs]=sqrt(
                   (self.dS[:, :, idxs]/normR[idxs][newaxis, newaxis, :])**2+
                   (self.S[:, :, idxs]/normR[idxs][newaxis, newaxis, :]**2*
                    normdR[idxs][newaxis, newaxis, :])**2
                   )
      self.S[:, :, idxs]/=normR[idxs][newaxis, newaxis, :]
      self.S[:, :, logical_not(idxs)]=0.
      self.dS[:, :, logical_not(idxs)]=0.

    # create grid
    self.SGrid, qy, qz=histogram2d(self.Qy.flatten(), self.Qz.flatten(),
                                   bins=(self.options['gisans_gridy'],
                                         self.options['gisans_gridz']),
                                   weights=self.S.flatten())
    npoints, ignore, ignore=histogram2d(self.Qy.flatten(), self.Qz.flatten(),
                                   bins=(self.options['gisans_gridy'],
                                         self.options['gisans_gridz']))
    self.SGrid[npoints>0]/=npoints[npoints>0]
    self.SGrid=self.SGrid.transpose()
    qy=(qy[:-1]+qy[1:])/2.
    qz=(qz[:-1]+qz[1:])/2.
    self.QyGrid, self.QzGrid=meshgrid(qy, qz)

