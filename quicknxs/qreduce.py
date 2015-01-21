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
import zlib
from copy import deepcopy
from glob import glob
from numpy import *
from numpy.version import version as npversion
from platform import node
from time import time, strptime, mktime
from mantid.simpleapi import *
from distutils.util import strtobool
# ignore zero devision error
#seterr(invalid='ignore')

from logging import debug, info, warn #@Reimport
from .config import instrument
from .decorators import log_call, log_input, log_both
from .ipython_tools import AttributePloter, StringRepr, NiceDict
from utilities import convert_angle, weighted_sum
import utilities
import numpy as np
from random import randint
import constants
import psutil
from peakfinder import PeakFinder
from all_plot_axis import AllPlotAxis

### Parameters needed for some calculations.
#TODO MAGIC NUMBER
H_OVER_M_NEUTRON=3.956034e-7 # h/m_n [m²/s]
DETECTOR_X_REGION=(8, 295) # the active area of the detector
DETECTOR_Y_REGION=(8, 246)
ANALYZER_IN=(0., 100.) # position and maximum deviation of analyzer in it's working position
POLARIZER_IN=(-348., 50.) # position and maximum deviation of polarizer in it's working position
SUPERMIRROR_IN=(19.125, 10.) # position and maximum deviation of the supermirror translation
POLY_CORR_PARAMS=[-4.74152261e-05,-4.62469580e-05, 1.25995446e-02, 2.13654008e-02,
                  1.02334517e+01] # parameters used in polynomial detector sensitivity correction
DETECTOR_SENSITIVITY={}
# measurement type mapping of states
MAPPING_12FULL=(
                 (u'++ (0V)', u'entry-off_off_Ezero'),
                 (u'-- (0V)', u'entry-on_on_Ezero'),
                 (u'+- (0V)', u'entry-off_on_Ezero'),
                 (u'-+ (0V)', u'entry-on_off_Ezero'),
                 (u'++ (+V)', u'entry-off_off_Eplus'),
                 (u'-- (+V)', u'entry-on_on_Eplus'),
                 (u'+- (+V)', u'entry-off_on_Eplus'),
                 (u'-+ (+V)', u'entry-on_off_Eplus'),
                 (u'++ (-V)', u'entry-off_off_Eminus'),
                 (u'-- (-V)', u'entry-on_on_Eminus'),
                 (u'+- (-V)', u'entry-off_on_Eminus'),
                 (u'-+ (-V)', u'entry-on_off_Eminus'),
                 )
MAPPING_12HALF=(
                 (u'+ (0V)', u'entry-off_off_Ezero'),
                 (u'- (0V)', u'entry-on_off_Ezero'),
                 (u'+ (+V)', u'entry-off_off_Eplus'),
                 (u'- (+V)', u'entry-on_off_Eplus'),
                 (u'+ (-V)', u'entry-off_off_Eminus'),
                 (u'- (-V)', u'entry-on_off_Eminus'),
                 )
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

# don't save RAM by compression when on analysis cluster or mrac computer as they have plenty
USE_COMPRESSION=not ('biganalysis' in node() or 'mrac' in node())

# used for * imports
__all__=['NXSData', 'MRDataset', 'Reflectivity', 'OffSpecular', 'GISANS', 'time_from_header',
         'locate_file']

_bincount=bincount
def bincount(x, weights=None, minlength=None):
  if len(x)==0:
    if minlength:
      return zeros(minlength, dtype=int)
    else:
      return array([0], dtype=int)
  if npversion<'1.6.0':
    bins=_bincount(x, weights=weights)
    if minlength and len(bins)<minlength:
      bins.resize(minlength)
    return bins
  else:
    return _bincount(x, weights, minlength)

class OptionsDocMeta(type):
  '''
  Metaclass to update docstring to dynamically include keyword arguments
  '''

  def __new__(cls, name, bases, dct):
    # overwrite the docstring
    docstring=dct['__doc__']
    docstring+='''
  The generator takes several keyword arguments to control the readout:'''
    opt_desc={}
    if 'DEFAULT_OPTIONS' in dct:
      opts=dct['DEFAULT_OPTIONS']
      if '_OPTIONS_DESCRTIPTION' in dct:
        opt_desc=dct['_OPTIONS_DESCRTIPTION']
    else:
      for base in bases:
        if hasattr(base, 'DEFAULT_OPTIONS'):
          opts=base.DEFAULT_OPTIONS
          if hasattr(base, '_OPTIONS_DESCRTIPTION'):
            opt_desc=base._OPTIONS_DESCRTIPTION
          break
    maxlen_key=3
    maxlen_val=7
    for key, value in sorted(opts.items()):
      maxlen_key=max(maxlen_key, len("%s"%key))
      maxlen_val=max(maxlen_val, len("%s"%value))
    maxlen_desc=80-maxlen_key-maxlen_val
    docline='\n      %%-%is  %%-%is  %%-%is'%(maxlen_key, maxlen_val, maxlen_desc)
    docstring+=docline%('='*maxlen_key, '='*maxlen_val, '='*maxlen_desc)
    docstring+=docline%('Key', 'Default', 'Description')
    docstring+=docline%('='*maxlen_key, '='*maxlen_val, '='*maxlen_desc)
    for key, value in sorted(opts.items()):
      desc=['']
      if key in opt_desc:
        desc=OptionsDocMeta.format_description(opt_desc[key], maxlen_desc)
      docstring+=docline%(key, value, desc[0])
      for desci in desc[1:]:
        docstring+=docline%('', '', desci)
    docstring+=docline%('='*maxlen_key, '='*maxlen_val, '='*maxlen_desc)+'\n      '
    dct['__doc__']=docstring

    return super(OptionsDocMeta, cls).__new__(cls, name, bases, dct)
  
  @staticmethod
  def format_description(description, maxlen):
    output=[description]
    while len(output[-1])>maxlen:
      lastitem=output.pop(-1)
      splitidx=lastitem[:maxlen].rfind(' ')
      output.append(lastitem[:splitidx])
      output.append(lastitem[splitidx+1:])
    return output
    

class NXSData(object):
  '''
  Class for readout and evaluation of histogram and event mode .nxs files,
  which also stores the data to be accessed by attributes.
  
  The object can be used as a ordered dictionary or list of channels,
  where each channel is a MRDataset object.
  '''
  __metaclass__=OptionsDocMeta

  nexus = None
  list_run_numbers = []
  nxs = None

  # raw axis (where q axis has 1 more element that y and e)
  reduce_q_axis = []
  reduce_y_axis = []
  reduce_e_axis = []
  sf_auto = 1  # automatic scaling factor calculated by program
  sf_auto_found_match = False
  sf_manual = 1 # manual scaling factor defined by user
  sf = 1 # scaling factor apply to data (will be either the auto, manual or 1)

  # histogram q axis (same number of element as y and e)
  q_axis_for_display = []
  y_axis_for_display = []
  e_axis_for_display = []

  # use in the auto SF class
  tmp_y_axis = []
  tmp_e_axis = []

  DEFAULT_OPTIONS=dict(bin_type=0, bins=40, use_caching=True, callback=None,
                       event_split_bins=None, event_split_index=0, low_res_range=[0,303], #TODO MAGIC NUMBER
                       event_tof_overwrite=None, 
                       metadata_config_object=None,
                       angle_offset = 0,
                       is_data = True,
                       is_auto_peak_finder = False,
                       back_offset_from_peak = 4,
                       is_auto_tof_finder = True)
  _OPTIONS_DESCRTIPTION=dict(
    bin_type="linear in ToF'/'1: linear in Q' - use linear or 1/x spacing for ToF channels in event mode",
    bins='Number of ToF bins for event mode',
    use_caching='If files should be cached for faster future readouts (last 20 files)',
    event_split_bins='Number of items, to split the events in time or None for no splitting',
    event_split_index='Index of the splitted item to be returned, when event_split_bin is not None',
    low_res_range='Pixel range of the low resolution axis (0->304 for the REF_L)', #TODO MAGIC NUMBER
    event_tof_overwrite='Optional array of ToF edges to be used instead of the ones created from bins and bin_type',
    metadata_config_object='LConfigDataset that is only present when the data comes from a config file',
    angle_offset='angle offset value defined in GUI',
    callback='Function called to update e.g. a progress bar',
    is_data='True or False (if file is a direct beam data set)',
    is_auto_peak_finder='True or False',
    back_offset_from_peak = 'pixel distance of background from peak',
    is_auto_tof_finder = 'True or False'
    )
  COUNT_THREASHOLD=100 #: Number of counts needed for a state to be interpreted as actual data
  MAX_CACHE=20 #: Number of datasets that are kept in the cache
  MAX_MEMORY_USED=80 #: percentage max of memory used
  _cache=[]

  @log_both
  def __new__(cls, filename, **options):

    if type(filename) is int:
      fn=locate_file(filename)
      if fn is None:
        raise RuntimeError, 'No file found for index %i'%filename
      filename=fn
    
    all_options=cls._get_all_options(options)
    
    if type(filename) == type([]):
      for i in range(len(filename)):
        filename[i] = os.path.abspath(filename[i])
        cached_names=[] #fixme (add cached names when loading more than 1 file)
    else:
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
    self.origin=filename  # full file name of the file
    # process the file
    self._read_times=[]

    if not self._read_file(filename):
      return None

    # memory debug code here
    # psutil.disk_usage('/').percent
    #print '***** Memory usage so far !!! *****'
    #print psutil.virtual_memory()

    if all_options['use_caching']:
      if filename in cached_names:
        cache_index=cached_names.index(filename)
        cls._cache.pop(cache_index)
        
      # make sure we stay below the 80% of memory used
      #while psutil.virtual_memory().percent >= cls.MAX_MEMORY_USED:
        #print 'cls._cache:'
        #print cls._cache
        #cls._cache.pop(0)

      # make sure cache does not get bigger than MAX_CACHE items or 80% of available memory
      while len(cls._cache)>=cls.MAX_CACHE:
        cls._cache.pop(0)
      cls._cache.append(self)
    # remove callback function to make the object Pickleable
    self._options['callback']=None

    return self

  @classmethod
  def _get_all_options(cls, options):
    all_options=dict(cls.DEFAULT_OPTIONS)
    for key, value in options.items():
      if not key in all_options:
        raise ValueError, "%s is not a known option parameter"%key
      all_options[key]=value
    return all_options

  def _read_file(self, filename):
    '''
    Load data from a NeXus file
    
    :param str filename: Path to file to read
    '''
    if instrument.NAME == 'REF_M': #TODO HARDCODED INSTRUMENT
      return self._read_REFM_file(filename)
    else:
      return self._read_REFL_file(filename)

  #def generate_random_workspace_name(self):
    #'''
    #This will generate a random workspace name to avoid conflict names
    #'''
    #string = 'abcdefghijklmnopqrstuvwxyz1234567890'
    #stringList = list(string)
    #nbrPara = len(stringList)
    
    #listRand = []
    #for i in range(5):
      #_tmp = stringList[randint(0,nbrPara-1)]
      #listRand.append(_tmp)
    
    #randomString = ''.join(listRand)
    #return randomString

  def _read_REFL_file(self, filename):
      '''
      Load data from a REF_L Nexus file.
      
      :param str filename: Path to file to read
      '''
      start=time()
      if self._options['callback']:
        self._options['callback'](0.)

      randomString = utilities.generate_random_workspace_name()

      if (type(filename) == type([])) and (len(filename) == 1):
        filename = filename[0]

      if (type(filename) == type(u"")) or (type(filename) == type("")):

        try:
          print '------> filename is: ' + str(filename)
          nxs = LoadEventNexus(Filename=str(filename),OutputWorkspace=randomString)
          self.list_run_numbers.append(nxs.getRun().getProperty('run_number').value) #TODO HARDCODED STRING
        except IOError:
          debug('Could not read nxs file %s'%filename, exc_info=True)
          return False

      else: # list of runs

        _index = 0
        _lambda_requested_1 = ''
        _lambda_requested_2 = ''
        nxs = 'ws_event'
        for _filename in filename:

          try:
            
            if _index == 0:
              nxs=LoadEventNexus(Filename=str(_filename),OutputWorkspace=randomString)
              
              # retrieve lambda requested value
              mt_run = nxs.getRun()
              self.list_run_numbers.append(nxs.getRun().getProperty('run_number').value) #TODO HARDCODED STRING
              _lambda_requested_1 = mt_run.getProperty('LambdaRequest').value #TODO HARDCODED STRING
              _index += 1
            else:
              tmp=LoadEventNexus(Filename=str(_filename))
              
              # make sure that the files have the same lambda requested
              mt_run = tmp.getRun()
              _lambda_requested_2 = mt_run.getProperty('LambdaRequest').value #TODO HARDCODED STRING
              if _lambda_requested_1 != _lambda_requested_2:
                debug('Lambda Requested of files do not match!')
                info('Lambda Requested do not match!')
                return False

              nxs=Plus(LHSWorkspace=randomString,
                   RHSWorkspace='tmp',OutputWorkspace=randomString)
              DeleteWorkspace(tmp)
            
          except IOError:
            strFilename = ",".join(filename)
            debug('Could not read nxs files %s' % strFilename, exc_info=True)
            return False


#      print self._options['low_res_range']
      data=LRDataset.from_event(nxs, self._options,
                                callback=self._options['callback'])


#      self.nexus = nxs

#      self._channel_data.append(data)
      data.filename = filename
      self.active_data = data

          #if data is None:
            ## no data in channel, don't add it
            #empty_channels.append(dest)
            #continue
        #elif filename.endswith('histo.nxs'):
          #data=MRDataset.from_histogram(raw_data, self._options)
        #else:
          #data=MRDataset.from_old_format(raw_data, self._options)
        #self._channel_data.append(data)
        #self._channel_names.append(dest)
        #self._channel_origin.append(channel)
        #progress=0.1+0.9*float(i)/len(channels)
        #if self._options['callback']:
          #self._options['callback'](progress)
        #i+=1
        #self._read_times.append(time()-self._read_times[-1]-start)
      ##print time()-start
      #if not is_ancient:
        #nxs.close()
      #if empty_channels:
        #warn('No counts for state %s'%(','.join(empty_channels)))
      return True

  def _read_REFM_file(self, filename):
    '''
    Load data from a REF_M Nexus file.
    
    :param str filename: Path to file to read
    '''
    start=time()
    if self._options['callback']:
      self._options['callback'](0.)
    try:
      nxs=h5py.File(filename, mode='r')
    except IOError:
      debug('Could not read nxs file %s'%filename, exc_info=True)
      return False
    # analyze channels
    channels=nxs.keys()
    debug('Channels in file: '+repr(channels))
    if channels==['entry']:
      # ancient file format with polarizations in different files
      nxs=self._get_ancient(filename)
      channels=nxs.keys()
      channels.sort()
      is_ancient=True
    else:
      is_ancient=False
    for channel in list(channels):
      debug(str(nxs[channel][u'total_counts'].value[0]))
      if nxs[channel][u'total_counts'].value[0]<self.COUNT_THREASHOLD:
        channels.remove(channel)
    if len(channels)==0:
      debug('No valid channels in file')
      return False
    ana=nxs[channels[0]]['instrument/analyzer/AnalyzerLift/value'].value[0] #TODO HARDCODED STRING
    pol=nxs[channels[0]]['instrument/polarizer/PolLift/value'].value[0] #TODO HARDCODED STRING
    try:
      smpt=nxs[channels[0]]['DASlogs/SMPolTrans/value'].value[0]
    except KeyError:
      smpt=0.

    # select the type of measurement that has been used
    if abs(ana-ANALYZER_IN[0])<ANALYZER_IN[1]: # is analyzer is in position
      if channels[0] in [m[1] for m in MAPPING_12FULL]:
        self.measurement_type='Polarization Analysis w/E-Field'
        mapping=list(MAPPING_12FULL)
      else:
        self.measurement_type='Polarization Analysis'
        mapping=list(MAPPING_FULLPOL)
    elif abs(pol-POLARIZER_IN[0])<POLARIZER_IN[1] or \
         abs(smpt-SUPERMIRROR_IN[0])<SUPERMIRROR_IN[1]: # is bender or supermirror polarizer is in position
      if channels[0] in [m[1] for m in MAPPING_12HALF]:
        self.measurement_type='Polarized w/E-Field'
        mapping=list(MAPPING_12HALF)
      else:
        self.measurement_type='Polarized'
        mapping=list(MAPPING_HALFPOL)
    #TODO HARDCODED STRING
    elif 'DASlogs' in nxs[channels[0]] and \
          nxs[channels[0]]['DASlogs'].get('SP_HV_Minus') is not None and \
          channels!=[u'entry-Off_Off']: # is E-field cart connected and not only 0V measured
      self.measurement_type='Electric Field'
      mapping=list(MAPPING_EFIELD)
    elif len(channels)==1:
      self.measurement_type='Unpolarized'
      mapping=list(MAPPING_UNPOL)
    else:
      self.measurement_type='Unknown'
      mapping=[]
    # check that all channels have a mapping entry
    for channel in channels:
      if not channel in [m[1] for m in mapping]:
        mapping.append((channel.lstrip('entry-'), channel))

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
      if filename.endswith('event.nxs'): #TODO HARDCODED STRING
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
      elif filename.endswith('histo.nxs'): #TODO HARDCODED STRING
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
    
    :param str filename: Path to file to read
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
    if type(item) in [int, slice]:
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

  def _repr_html_(self):
    '''Object representation for IPython'''
    output='<h2>%s object:</h2>\n'%self.__class__.__name__
    output+='<table>\n'
    output+='\t<tr><td colspan="2" align="center">Object Data:</td></td>\n'
    output+='\t<tr><th>State</th><th>Data Object</th></td>\n'
    for key, value in self.items():
      output+='\t<tr>\n\t\t<td>\n\t\t\t<b>%s</b>\n\t\t</td>\n\t\t<td>\n\t\t\t'%key
      output+='%s\n'%value._repr_html_()
      output+='\t\t</td>\n\t</tr>\n'
    output+='</table>'
    return output

  def keys(self):
    return self._channel_names

  def values(self):
    return self._channel_data

  def items(self):
    return zip(self.keys(), self.values())

  def numitems(self):
    ''':returns: three items tuples of the channel index, name and data'''
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

  def __nbytes(self): return sum([ds.nbytes for ds in self])
  nbytes=property(__nbytes, doc='size of the data stored in memory for all states of this file')


  # easy access properties common to all datasets
  def __lambda_center(self): return self[0].lambda_center
  def __number(self): return self[0].number
  def __experiment(self): return self[0].experiment
  def __merge_warnings(self): return self[0].merge_warnings
  def __dpix(self): return self[0].dpix
  def __dangle(self): return self[0].dangle
  def __dangle0(self): return self[0].dangle0
  def __sangle(self): return self[0].sangle
  lambda_center=property(__lambda_center, doc='first state lambda_center attribute')
  number=property(__number, doc='first state number attribute')
  experiment=property(__experiment, doc='first state experiment attribute')
  merge_warnings=property(__merge_warnings, doc='first state merge_warnings attribute')
  dpix=property(__dpix, doc='first state dpix attribute')
  dangle=property(__dangle, doc='first state dangle attribute')
  dangle0=property(__dangle0, doc='first state dangle0 attribute')
  sangle=property(__sangle, doc='first state sangle attribute')
  

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
    all_options=cls._get_all_options(options)
    all_options['callback']=None
    cached_names=[item.origin for item in cls._cache]
    if all_options['use_caching'] and filenames in cached_names:
      cache_index=cached_names.index(filenames)
      cached_object=cls._cache[cache_index]
      if cached_object._options==all_options:
        return cached_object

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
        raise ValueError, 'Files can not be combined due to different number of states'
      self._add_data(other)
      numbers.append(other.number)
    self.origin=filenames
    self._options=all_options
    for item in self:
      item.read_options=all_options
    if all_options['use_caching']:
      if filenames in cached_names:
        cache_index=cached_names.index(filenames)
        cls._cache.pop(cache_index)
      # make sure cache does not get bigger than MAX_CACHE items or 80% of available memory
      while len(cls._cache)>=cls.MAX_CACHE:
        cls._cache.pop(0)
      cls._cache.append(self)
    return self

  def _add_data(self, other):
    '''
    Add the counts of all channels to this dataset channels 
    and increase the proton charge equally.
    
    :type other: NXSData
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
  proton_charge=0. #: total proton charge on target [pC]
  total_counts=0 #: total counts on detector
  total_time=0 #: time counted in this channal
  tof_edges=None #: array of time of flight edges for the bins [µs]
  dangle=0. #: detector arm angle value in [°]
  dangle0=4. #: detector arm angle value of direct pixel measurement in [°]
  sangle=0. #: sample angle [°]
  mon_data=None #: array of monitor counts per ToF bin

  # for resolution calculation
  #TODO MAGIC NUMBER
  slit1_width=3. #: first slit width [mm]
  slit1_dist=2600. #: first slit to sample distance [mm]
  slit2_width=2. #: second slit width [mm]
  slit2_dist=2019. #: second slit to sample distance [mm]
  slit3_width=0.05 #: last slit width [mm]
  slit3_dist=714. #: last slit to sample distance [mm]

  ai=None #: incident angle
  dpix=0 #: pixel of direct beam position at dangle0
  lambda_center=3.37 #: central wavelength of measurement band [Å]
  xydata=None #: 2D array of intensity projected on X-Y
  xtofdata=None #: 2D array of intensity projected on X-ToF
  data=None #: 3D array of intensity in X, Y and ToF
  logs={} #: Log information of instrument parameters
  log_units={} #: Units of the parameters given in logs
  experiment='' #: Name of the experiment
  number=0 #: Index of the run
  merge_warnings=''
  dist_mod_det=21.2535 #: moderator to detector distance [m]
  dist_sam_det=2.55505 #: sample to detector distance [m]
  det_size_x=0.2128 #: horizontal size of detector [m]
  det_size_y=0.1792 #: vertical size of detector [m]
  from_event_mode=False #: was this dataset created from event mode nexus file

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

    output.tof_edges=data['bank1/time_of_flight'].value #TODO HARDCODED STRING
    # the data arrays
    output.data=data['bank1/data'].value.astype(float) # 3D dataset #TODO HARDCODED STRING
    output.xydata=data['bank1']['data_x_y'].value.transpose().astype(float) # 2D dataset #TODO HARDCODED STRING
    output.xtofdata=data['bank1']['data_x_time_of_flight'].value.astype(float) # 2D dataset #TODO HARDCODED STRING

    try:
      #TODO HARDCODED STRING
      mon_tof_from=data['monitor1']['time_of_flight'].value.astype(float)*\
                                            output.dist_mod_det/output.dist_mod_mon
      mon_I_from=data['monitor1']['data'].value.astype(float) #TODO HARDCODED STRING
      mod_data=histogram((mon_tof_from[:-1]+mon_tof_from[1:])/2., output.tof_edges,
                         weights=mon_I_from)[0]
      output.mon_data=mod_data
    except KeyError:
      output.mon_data=None
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
    output.tof_edges=data['bank1/time_of_flight'].value[1:] #TODO HARDCODED STRING
    # the data arrays
    output.data=data['bank1/data'].value.astype(float)[:, :, 1:] # 3D dataset #TODO HARDCODED STRING
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
      lcenter=data['DASlogs/LambdaRequest/value'].value[0] #TODO HARDCODED STRING
      # ToF region for this specific central wavelength
      tmin=output.dist_mod_det/H_OVER_M_NEUTRON*(lcenter-1.6)*1e-4
      tmax=output.dist_mod_det/H_OVER_M_NEUTRON*(lcenter+1.6)*1e-4
      if bin_type==0: # constant Δλ
        tof_edges=linspace(tmin, tmax, bins+1)
      elif bin_type==1: # constant ΔQ
        tof_edges=1./linspace(1./tmin, 1./tmax, bins+1)
      elif bin_type==2: # constant Δλ/λ
        tof_edges=tmin*(((tmax/tmin)**(1./bins))**arange(bins+1))
      else:
        raise ValueError, 'Unknown bin type %i'%bin_type
    else:
      tof_edges=tof_overwrite

    # Histogram the data
    # create ToF edges for the binning and correlate pixel indices with pixel position
    tof_ids=array(data['bank1_events/event_id'].value, dtype=int) #TODO HARDCODED STRING
    tof_time=data['bank1_events/event_time_offset'].value #TODO HARDCODED STRING
    # read the corresponding proton charge of each pulse
    tof_pc=data['DASlogs/proton_charge/value'].value #TODO HARDCODED STRING
    if read_options['event_split_bins']:
      split_bins=read_options['event_split_bins']
      split_index=read_options['event_split_index']
      # read the relative time in seconds from measurement start to event
      tof_real_time=data['bank1_events/event_time_zero'].value #TODO HARDCODED STRING
      tof_idx_to_id=data['bank1_events/event_index'].value #TODO HARDCODED STRING
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
    # calculate total proton charge in the selected area
    output.proton_charge=tof_pc.sum()
    Ixyt=MRDataset.bin_events(tof_ids, tof_time, tof_edges,
                              callback, callback_offset, callback_scaling)

    # create projections for the 2D datasets
    Ixy=Ixyt.sum(axis=2)
    Ixt=Ixyt.sum(axis=1)
    # store the data
    output.tof_edges=tof_edges
    output.data=Ixyt.astype(float) # 3D dataset
    output.xydata=Ixy.transpose().astype(float) # 2D dataset
    output.xtofdata=Ixt.astype(float) # 2D dataset
    return output

  @staticmethod
  def bin_events(tof_ids, tof_time, tof_edges,
                 callback=None, callback_offset=0., callback_scaling=1.):
    '''
    Filter events outside the tof_edges region and calculate the binning with devide_bin.
    
    @return: 3D array of dimensions (x, y, tof)
    '''
    region=(tof_time>=tof_edges[0])&(tof_time<=tof_edges[-1])
    result=array(MRDataset.devide_bin(tof_ids[region], tof_time[region], tof_edges,
                                callback, callback_offset, callback_scaling/len(tof_edges)))
    return result.transpose((1, 2, 0))

  @staticmethod
  def devide_bin(tof_ids, tof_time, tof_edges, 
                 callback=None, callback_offset=0., callback_scaling=1., cbidx=0):
    '''
    Use a divide and conquer strategy to bin the data. For the actual binning the
    numpy bincount function is used, as it is much faster then histogram for
    counting of integer values.
    
    @param tof_ids: Array of positional indices for each event
    @param tof_time: Array of time of flight for each event
    @param tof_edges: The edges of bins to be used for the histogram
    @keyword callback: Optional callback function for the progress
    @keyword callback_offset: Offset for calling the function
    @keyword callback_scaling: Factor to multiply the counting index when calling the function
    @keyword cbidx: Current counting index for this recursive call
    
    @return: 3D list of dimensions (tof, x, y)
    '''
    if len(tof_edges)==2:
      # deepest recursion reached, all items should be within the two ToF edges
      if callback is not None:
        callback(callback_offset+callback_scaling*cbidx)
      return [bincount(tof_ids, minlength=304*256).reshape(304, 256).tolist()] #TODO MAGIC NUMBER
    # split all events into two time of flight regions
    split_idx=len(tof_edges)/2
    left_region=tof_time<tof_edges[split_idx]
    left_list=MRDataset.devide_bin(tof_ids[left_region], tof_time[left_region],
                              tof_edges[:split_idx+1],
                              callback, callback_offset, callback_scaling, cbidx)
    right_region=logical_not(left_region)
    right_list=MRDataset.devide_bin(tof_ids[right_region], tof_time[right_region],
                              tof_edges[split_idx:],
                              callback, callback_offset, callback_scaling, split_idx+cbidx)
    return left_list+right_list

  def _collect_info(self, data):
    '''
    Extract header information from the HDF5 file.
    
    :param h5py._hl.group.Group data:
    '''
    self.origin=(os.path.abspath(data.file.filename), data.name.lstrip('/'))
    self.logs=NiceDict()
    self.log_minmax=NiceDict()
    self.log_units=NiceDict()
    if 'DASlogs' in data:  # the old format does not include the DAS logs
      # get an array of all pulses to make it possible to correlate values with states
      stimes=data['DASlogs/proton_charge/time'].value #TODO HARDCODED STRING
      stimes=stimes[::10] # reduce the number of items to speed up the correlation
      # use only values that are not directly before or after a state change
      stimesl, stimesc, stimesr=stimes[:-2], stimes[1:-1], stimes[2:]
      stimes=stimesc[((stimesr-stimesc)<1.)&((stimesc-stimesl)<1.)]
      for motor, item in data['DASlogs'].items(): #TODO HARDCODED STRING
        if motor in ['proton_charge', 'frequency', 'Veto_pulse']:
          continue
        try:
          if 'units' in item['value'].attrs:
            self.log_units[motor]=unicode(item['value'].attrs['units'], encoding='utf8')
          else:
            self.log_units[motor]=u''
          val=item['value'].value
          if val.shape[0]==1:
            self.logs[motor]=val[0]
            self.log_minmax[motor]=(val[0], val[0])
          else:
            vtime=item['time'].value
            sidx=searchsorted(vtime, stimes, side='right')
            sidx=maximum(sidx-1, 0)
            val=val[sidx]
            if len(val)==0:
              self.logs[motor]=NaN
              self.log_minmax[motor]=(NaN, NaN)
            else:
              self.logs[motor]=val.mean()
              self.log_minmax[motor]=(val.min(), val.max())
        except:
          continue
      self.lambda_center=data['DASlogs/LambdaRequest/value'].value[0] #TODO HARDCODED STRING
    self.dangle=data['instrument/bank1/DANGLE/value'].value[0] #TODO HARDCODED STRING
    #TODO HARDCODED STRING
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
    self.total_time=data['duration'].value[0]

    self.dist_sam_det=data['instrument/bank1/SampleDetDis/value'].value[0]*1e-3
    self.dist_mod_det=data['instrument/moderator/ModeratorSamDis/value'].value[0]*1e-3+self.dist_sam_det
    self.dist_mod_mon=data['instrument/moderator/ModeratorSamDis/value'].value[0]*1e-3-2.75 #TODO MAGIC NUMBER
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

  def _repr_html_(self):
    '''Object representation for IPython'''
    output='<b>%s</b> Object:\n<table border="1">\n'%self.__class__.__name__
    output+='<tr><th>Attribute</th><th>Value</th></tr>\n'
    for attr in ['experiment', 'number', 'total_counts', 'proton_charge',
                 'sangle', 'dangle', 'dangle0', 'dpix']:
      output+='<tr><td>%s</td><td>%s</td></tr>\n'%(attr, str(getattr(self, attr)))
    if type(self.number) is list:
      for i, item in enumerate(self.origin):
        output+='<tr><td>origin[%i][0]</td><td>%s</td></tr>\n'%(i, item[0])
        output+='<tr><td>origin[%i][1]</td><td>%s</td></tr>\n'%(i, item[1])
    else:
      output+='<tr><td>origin[0]</td><td>%s</td></tr>\n'%self.origin[0]
      output+='<tr><td>origin[1]</td><td>%s</td></tr>\n'%self.origin[1]
    output+='</table>'
    return output

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

  if USE_COMPRESSION:
    # data compressed in memory properties, last dataset data is cached for better GUI response
    _data_zipped=None
    _data_dtype=float
    _data_shape=(0,)
    _cached_object=None
    _cached_data=None
    @property
    def data(self):
      if MRDataset._cached_object is self:
        return MRDataset._cached_data
      data=fromstring(zlib.decompress(self._data_zipped), dtype=self._data_dtype)
      data=data.reshape(self._data_shape)
      MRDataset._cached_data=data
      MRDataset._cached_object=self
      return data
    @data.setter
    def data(self, data):
      self._data_zipped=zlib.compress(data.tostring(), 1)
      self._data_dtype=data.dtype
      self._data_shape=data.shape
      MRDataset._cached_data=data
      MRDataset._cached_object=self

  ################## Properties for easy data access ##########################
  # return the size of the data stored in memory for this dataset
  @property
  def nbytes(self): return (len(self._data_zipped)+
                            self.xydata.nbytes+self.xtofdata.nbytes)
  @property
  def rawbytes(self): return (self.data.nbytes+self.xydata.nbytes+self.xtofdata.nbytes)

  if USE_COMPRESSION:
    @property
    def nbytes(self): return (len(self._data_zipped)+
                              self.xydata.nbytes+self.xtofdata.nbytes)
  else:
    nbytes=rawbytes

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

  def get_tth(self, dangle0=None, dpix=None):
    '''
    Return the tth values corresponding to each x-pixel.
    '''
    if dangle0 is None:
      dangle0=self.dangle0
    if dpix is None:
      dpix=self.dpix
    x=self.x
    grad_per_pixel=self.det_size_x/self.dist_sam_det/len(x)*180./pi
    tth0=(self.dangle-dangle0)-(304-dpix)*grad_per_pixel #TODO MAGIC NUMBER
    tth_range=x[::-1]*grad_per_pixel
    return tth0+tth_range

  def get_tthlamda(self, dangle0=None, dpix=None):
    '''
    Return tth and lamda values corresponding to x and tof.
    '''
    return meshgrid(self.lamda, self.get_tth(dangle0, dpix))

  tth=property(get_tth)
  tthlamda=property(get_tthlamda)

  @property
  def p(self):
    '''A attribute to quickly plot data in the qt console'''
    return AttributePloter(self, ['xdata', 'xydata', 'ydata', 'xtofdata', 'tofdata', 'data'])


class LConfigDataset(object):
  '''
  This class will be used when loading an XML configuration file and will
  keep record of all the information loaded, such as peak, back, TOF range...
  until the data/norm file has been loaded
  '''
  data_full_file_name = ''
  data_peak = ['0','0']
  data_back = ['0','0']
  data_low_res = ['0','0']
  data_back_flag = True
  data_low_res_flag = True
  tof = ['0','0'] 
  tof_units = 'ms'
  tof_auto_flag = True
  
  norm_full_file_name = ''
  norm_flag = True
  norm_peak = ['0','0']
  norm_back = ['0','0']
  norm_back_flag = True
  norm_low_res = ['0','0']
  norm_low_res_flag = True
 
  q_range =['0','0']
  lambda_range = ['0','0']
  
  norm_sets = ''
  data_sets = ''
 
class LRDataset(object):
  '''
  Representation of one measurement channel of the reflectometer
  including meta data.
  '''
  total_counts=0 #: total counts on detector
  total_time=0 #: time counted in this channal

  tof_axis_auto = None # full auto tof axis (estimated by program)
  tof_range_auto = ['0','0'] # [tof_min_auto, tof_max_auto]
  tof_axis_auto_with_margin = None # full auto tof axis with margin (for display)
  tof_range_auto_with_margin = None # [tof_min_auto_margin, tof_max_auto_margin]
  tof_range = ['0','0'] # [tof_min, tof_max] manual tof defined
  tof_axis = None # manual tof axis

  #tof_edges=None #: array of time of flight edges for the bins [µs]
  #tof_edges_full = None

  dangle=0. #: detector arm angle value in [°]
  dangle0=4. #: detector arm angle value of direct pixel measurement in [°]
  sangle=0. #: sample angle [°]
  mon_data=None #: array of monitor counts per ToF bin
  run_number = '' #: NeXus run number

  # for resolution calculation
  #TODO MAGIC NUMBER
  slit1_width=3. #: first slit width [mm]
  slit1_dist=2600. #: first slit to sample distance [mm]
  slit2_width=2. #: second slit width [mm]
  slit2_dist=2019. #: second slit to sample distance [mm]
  slit3_width=0.05 #: last slit width [mm]
  slit3_dist=714. #: last slit to sample distance [mm]

  # metadata
  proton_charge=0. #: total proton charge on target [pC] 
  proton_charge_units='' 
  lambda_requested=0
  lambda_requested_units=''
  thi=0 
  thi_units=''
  tthd=0
  tthd_units = ''
  S1W=0 # slit 1 width
  S2W=0 # slit 2 width
  S1H=0 # slit 1 height
  S2H=0 # slit 2 height
  isSiThere = False
  SiH = 0 # slit i height
  SiW = 0 # slit i width
  dMS=0 # distance Moderator-Sample
  dMS_units = ''
  dSD=0 # distance Sample-Detector
  dSD_units = ''
  dMD=0 # distance Moderator-Detector
  dMD_units = ''
  filename= ''
  
  low_resolution_range = [0,303] #TODO MAGIC NUMBER
  
  # will be used to keep the GUI in the same state
  full_file_name = ''
  use_it_flag = True
  peak = ['0','0']
  back = ['0','0']
  low_res = ['0','0']
  back_flag = True
  low_res_flag = True
  #tof_range = ['0','0'] 
  tof_units = 'ms'
  tof_auto_flag = True
  q_range = ['0','0']
  lambda_range = ['0','0']
  theta = 0
  incident_angle = 0
  
  nxs=None # Mantid NeXus workspace
  nxs_histo=None # Mantid NeXus workspace, rebinned

  ai=None #: incident angle
  dpix=0 #: pixel of direct beam position at dangle0
  #TODO MAGIC NUMBER
  lambda_center=3.37 #: central wavelength of measurement band [Å]

  xydata=None #: 2D array of intensity projected on X-Y
  ytofdata=None #: 2D array of intensity projected on X-TOF
  data=None #: 3D array of intensity in X, Y and TOF
  countstofdata = None
  countsxdata = None
  ycountsdata = None

#  tof_axis = None
  Ixyt = None
  Exyt = None

  Ixyt_reduction = None
  Exyt_reduction = None

  xyerror=None #: 2D array of the error projected on X-Y
  xtoferror=None #: 2D array of error projected on X-TOF
  error=None #: 3D array of error in X, Y and TOF

  logs={} #: Log information of instrument parameters
  log_units={} #: Units of the parameters given in logs
  experiment='' #: Name of the experiment
  number=0 #: Index of the run
  merge_warnings=''
  #TODO MAGIC NUMBER
  dist_mod_det=21.2535 #: moderator to detector distance [m]
  dist_sam_det=2.55505 #: sample to detector distance [m]
  det_size_x=0.2128 #: horizontal size of detector [m]
  det_size_y=0.1792 #: vertical size of detector [m]
  from_event_mode=False #: was this dataset created from event mode nexus file

  new_detector_geometry_flag = False #: True if run taken after constants.new_geometry_detector_date

  _Q=None
  _I=None
  _dI=None
  
  # will define the axis of all the plot used by this data set
  all_plot_axis = None
  

  def __init__(self):
    '''
    Initialize an empty dataset. To actually load a Nexus file channel
    use the class methods from_histogram or from_event.
    '''
    self.origin=('none', 'none')
    self.all_plot_axis = AllPlotAxis()
    
  @classmethod
  @log_call
  def from_histogram(cls, data, read_options):
    '''
    Create object from a histogram Nexus file.
    '''
    output=cls()
    output.read_options=read_options
    output._collect_info(data)

    output.tof_edges=data['bank1/time_of_flight'].value #TODO HARDCODED STRING
    # the data arrays
    output.data=data['bank1/data'].value.astype(float) # 3D dataset #TODO HARDCODED STRING
    output.xydata=data['bank1']['data_x_y'].value.transpose().astype(float) # 2D dataset #TODO HARDCODED STRING
    output.xtofdata=data['bank1']['data_x_time_of_flight'].value.astype(float) # 2D dataset #TODO HARDCODED STRING

    try:
      #TODO HARDCODED STRING
      mon_tof_from=data['monitor1']['time_of_flight'].value.astype(float)*\
                                            output.dist_mod_det/output.dist_mod_mon
      mon_I_from=data['monitor1']['data'].value.astype(float) #TODO HARDCODED STRING
      mod_data=histogram((mon_tof_from[:-1]+mon_tof_from[1:])/2., output.tof_edges,
                         weights=mon_I_from)[0]
      output.mon_data=mod_data
    except KeyError:
      output.mon_data=None
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
    #TODO HARDCODED STRING
    output.tof_edges=data['bank1/time_of_flight'].value[1:]
    # the data arrays
    output.data=data['bank1/data'].value.astype(float)[:, :, 1:] # 3D dataset
    output.xydata=output.data.sum(axis=2).transpose()
    output.xtofdata=output.data.sum(axis=1)
    return output

  @staticmethod
  def populateOutputWithMetadata(_output):
    '''
    Will retrieve the metadata from LConfigDataset and will place them into
    the output object
    '''
    output = _output
    _isData = output.read_options['is_data']

    _iDataset = output.read_options['metadata_config_object']
    
    if _isData:
     
      _data_full_file_name = _iDataset.data_full_file_name
      output.full_file_name = _data_full_file_name
    
      _data_peak = _iDataset.data_peak
      output.peak = _data_peak
   
      _data_back = _iDataset.data_back
      output.back = _data_back

      _data_low_res = _iDataset.data_low_res
      output.low_res = _data_low_res

      _data_back_flag = _iDataset.data_back_flag
      output.back_flag = strtobool(_data_back_flag)

      _data_low_res_flag = _iDataset.data_low_res_flag
      output.low_res_flag = strtobool(_data_low_res_flag)
      
      _data_q_range = _iDataset.q_range
      output.q_range = _data_q_range
      
      _data_lambda_range = _iDataset.lambda_range
      output.lambda_range = _data_lambda_range

    else:    

      _norm_full_file_name = _iDataset.norm_full_file_name
      output.full_file_name = _norm_full_file_name
      
      _norm_flag = _iDataset.norm_flag
      output.use_it_flag = strtobool(_norm_flag)

      _norm_peak = _iDataset.norm_peak
      output.peak = _norm_peak

      _norm_back = _iDataset.norm_back
      output.back = _norm_back

      _norm_back_flag = _iDataset.norm_back_flag
      output.back_flag = strtobool(_norm_back_flag)

      _norm_low_res = _iDataset.norm_low_res
      output.low_res = _norm_low_res

      _norm_low_res_flag = _iDataset.norm_low_res_flag
      output.low_res_flag = strtobool(_norm_low_res_flag)

    _tof = _iDataset.tof_range
    output.tof_range = _tof

    _tof_units = _iDataset.tof_units
    output.tof_units = _tof_units

    _tof_auto_flag = _iDataset.tof_auto_flag
    output.tof_auto_flag = strtobool(_tof_auto_flag)

    return output

  def calculate_q_range(output):
    '''
    calculate q range
    '''

    theta_rad = output.theta
    dMD = output.dMD
    
    _const = float(4) * math.pi * constants.mn * dMD / constants.h
    
    # retrieve tof from GUI
    [tof_min, tof_max] = output.tof_range
      
    q_min = _const * math.sin(theta_rad) / (float(tof_max) * 1e-6) * float(1e-10)
    q_max = _const * math.sin(theta_rad) / (float(tof_min) * 1e-6) * float(1e-10)

    q_min = "%.5f" % q_min
    q_max = "%.5f" % q_max

    return [q_min, q_max]
   
  def calculate_lambda_range(output):
    '''
    calculate lambda range
    '''
    
    dMD = output.dMD
    _const = constants.h / (constants.mn * dMD)
    
    # retrieve tof from GUI
    [tof_min, tof_max] = output.tof_range

    lambda_min = _const * (tof_min * 1e-6) / float(1e-10)
    lambda_max = _const * (tof_max * 1e-6) / float(1e-10)
  
    lambda_min = "%.2f" % lambda_min
    lambda_max = "%2.f" % lambda_max
    
    return [lambda_min, lambda_max]

  def calculate_incident_angle(output):
    '''
    calculate the incident angle
    '''
    _tthd = output.tthd
    _tthd_units = output.tthd_units
      
    _ths = output.thi
    _ths_units = output.thi_units
      
    if _tthd_units != 'degree':
      _tthd = radians(_tthd)
      
    if _ths_units != 'degree':
      _ths = radians(_ths)
        
    angle = fabs(_tthd - _ths)
    _value = "%.2f" % angle
    return _value

  def calculate_theta(output):
    '''
    calculate theta
    '''
    tthd = output.tthd
    tthd_units = output.tthd_units
    thi = output.thi
    thi_units = output.thi_units
    
    tthd_rad = convert_angle(angle=tthd, from_units=tthd_units, to_units='rad')
    thi_rad = convert_angle(angle=thi, from_units=thi_units, to_units='rad')
    
    theta_rad = fabs(tthd_rad - thi_rad) / float(2)
    
    angle_offset = float(output.read_options['angle_offset'])
    angle_offset_rad = convert_angle(angle=angle_offset, from_units='degree', to_units='rad')
    
    theta_rad += angle_offset_rad
    
    return theta_rad

  def isNexusTakeAfterRefDate(output, ref_date):
    '''
    This function parses the output.date and returns true if this date is after the ref date
    '''
    nexus_date = output.date
    nexus_date_acquistion = nexus_date.split('T')[0]
    
    if nexus_date_acquistion > ref_date:
      return True
    else:
      return False

  @classmethod
  @log_call
  def from_event(cls, nxs, read_options,
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
    bin_type=0

    if output.read_options['metadata_config_object'] is not None:
      output = LRDataset.populateOutputWithMetadata(output)

    # we will need to access nxs if the user decides to manually select the TOF range
    output.nxs = nxs;

    # retrieve the metadata from the nexus file
    output._collect_info(nxs)

    # check if file is part of new rotated detector (date > 2014-10-05)
    ref_date = constants.new_geometry_detector_date
    output.new_detector_geometry_flag = LRDataset.isNexusTakeAfterRefDate(output, ref_date)
    
    # calculate theta
    output.theta = LRDataset.calculate_theta(output)

    if (output.read_options['is_auto_tof_finder']) or (output.tof_range == ['0','0']):
      #TODO MAGIC NUMBER
      # auto t range
      autotmin = output.dMD/H_OVER_M_NEUTRON*(output.lambda_requested + 0.5  - 1.7) * 1e-4
      autotmax = output.dMD/H_OVER_M_NEUTRON*(output.lambda_requested + 0.5  + 1.7) * 1e-4
    
      # wider t range for display only
      tmin = output.dMD/H_OVER_M_NEUTRON*(output.lambda_requested + 0.5  - 2.5) * 1e-4
      tmax = output.dMD/H_OVER_M_NEUTRON*(output.lambda_requested + 0.5  + 2.5) * 1e-4
    
    else:
        
      autotmin = np.float(output.tof_range[0])
      autotmax = np.float(output.tof_range[1])
      
      tmin = np.float(autotmin - 0.4e4)
      tmax = np.float(autotmax + 0.4e4)
  
    output.tof_range_auto = [autotmin, autotmax]
    output.tof_range_auto_with_margin = [tmin, tmax]
    output.tof_range = [autotmin, autotmax] # for the first time, initialize tof_range like auto (microS)
    
    output.q_range = LRDataset.calculate_q_range(output)
    output.lambda_range = LRDataset.calculate_lambda_range(output)
    output.incident_angle = LRDataset.calculate_incident_angle(output)
    
    tbin = int(read_options["bins"])
    
    # rebin event nexus to get histogram
    params = [float(tmin), float(tbin), float(tmax)]
    nxs_histo = Rebin(InputWorkspace=nxs,Params=params, PreserveEvents=True)
    # normalize by proton charge

    _proton_charge = float(nxs.getRun().getProperty('gd_prtn_chrg').value) #TODO HARDCODED STRING
    _proton_charge_units = nxs.getRun().getProperty('gd_prtn_chrg').units #TODO HARDCODED STRING
    new_proton_charge_units = 'mC'
    
    output.proton_charge = _proton_charge * 3.6   # to go from microA/h to mC
    output.proton_charge_units = new_proton_charge_units

    output.tof_axis_auto_with_margin = nxs_histo.readX(0)

    ## keep only the low resolution range requested
    low_res_range = [int(read_options['low_res_range'][0]), int(read_options['low_res_range'][1])]
    from_pixel = min(low_res_range)
    to_pixel = max(low_res_range)

    # create projections for the 2D datasets
    x_size = to_pixel - from_pixel
    y_size = output.ixyIndex(1,0)
    num_bins = nxs_histo.blocksize()

    Iyt = np.zeros((y_size, num_bins))
    for x in range(x_size):
      for y in range(y_size):
        Iyt[y] += nxs_histo.readY(output.ixyIndex(from_pixel + x,y))
    Iit = Iyt.sum(axis=0)
    Iyi = Iyt.sum(axis=1)

    Ixy = np.zeros((x_size,y_size))
    for x in range(x_size):
      for y in range(y_size):
        Ixy[x,y] = np.sum(nxs_histo.readY(output.ixyIndex(from_pixel + x, y)))
    Iix = Ixy.sum(axis=1)

    # store the data
    output.xydata = Ixy.transpose().astype(float)
    output.ytofdata = Iyt.astype(float)
    output.countstofdata = Iit.astype(float)
    output.countsxdata = Iix.astype(float)
    output.ycountsdata = Iyi.astype(float)

    if read_options['is_auto_peak_finder']:
      pf = PeakFinder(range(len(output.ycountsdata)), output.ycountsdata)
      peaks=pf.get_peaks()
      main_peak = peaks[0]
      peak1 = int(main_peak[0] - main_peak[1])
      peak2 = int(main_peak[0] + main_peak[1])
      output.peak = [str(peak1), str(peak2)]

      backOffsetFromPeak = read_options['back_offset_from_peak']
      back1 = int(peak1 - backOffsetFromPeak)
      back2 = int(peak2 + backOffsetFromPeak)
      output.back = [str(back1), str(back2)]
    
    return output

  def ixyIndex(self, x, y):
    #TODO MAGIC NUMBER
    if self.new_detector_geometry_flag:
      return 304 * x + y
    else:
      return 256 * x + y

  @staticmethod
  def bin_events(tof_ids, tof_time, tof_edges,
                 callback=None, callback_offset=0., callback_scaling=1.):
    '''
    Filter events outside the tof_edges region and calculate the binning with devide_bin.
    
    @return: 3D array of dimensions (x, y, tof)
    '''
    region=(tof_time>=tof_edges[0])&(tof_time<=tof_edges[-1])
    result=array(MRDataset.devide_bin(tof_ids[region], tof_time[region], tof_edges,
                                callback, callback_offset, callback_scaling/len(tof_edges)))
    return result.transpose((1, 2, 0))

  @staticmethod
  def devide_bin(tof_ids, tof_time, tof_edges, 
                 callback=None, callback_offset=0., callback_scaling=1., cbidx=0):
    '''
    Use a divide and conquer strategy to bin the data. For the actual binning the
    numpy bincount function is used, as it is much faster then histogram for
    counting of integer values.
    
    @param tof_ids: Array of positional indices for each event
    @param tof_time: Array of time of flight for each event
    @param tof_edges: The edges of bins to be used for the histogram
    @keyword callback: Optional callback function for the progress
    @keyword callback_offset: Offset for calling the function
    @keyword callback_scaling: Factor to multiply the counting index when calling the function
    @keyword cbidx: Current counting index for this recursive call
    
    @return: 3D list of dimensions (tof, x, y)
    '''
    if len(tof_edges)==2:
      # deepest recursion reached, all items should be within the two ToF edges
      if callback is not None:
        callback(callback_offset+callback_scaling*cbidx)
      return [bincount(tof_ids, minlength=304*256).reshape(304, 256).tolist()] #TODO MAGIC NUMBER
    # split all events into two time of flight regions
    split_idx=len(tof_edges)/2
    left_region=tof_time<tof_edges[split_idx]
    left_list=MRDataset.devide_bin(tof_ids[left_region], tof_time[left_region],
                              tof_edges[:split_idx+1],
                              callback, callback_offset, callback_scaling, cbidx)
    right_region=logical_not(left_region)
    right_list=MRDataset.devide_bin(tof_ids[right_region], tof_time[right_region],
                              tof_edges[split_idx:],
                              callback, callback_offset, callback_scaling, split_idx+cbidx)
    return left_list+right_list

  def _collect_info(self, nxs):
    '''
    Extract header information from the HDF5 file.
    
    :param h5py._hl.group.Group data:
    '''
    mt_run = nxs.getRun()
    #TODO HARDCODED STRING
    lr = mt_run.getProperty('LambdaRequest').value
    self.run_number = mt_run.getProperty('run_number').value
#    if len(lr) > 1:
 #     self.run_number = 
    self.lambda_requested = mt_run.getProperty('LambdaRequest').value[0]
    self.lambda_requested_units = mt_run.getProperty('LambdaRequest').units
    self.thi = mt_run.getProperty('thi').value[0]
    self.thi_units = mt_run.getProperty('thi').units
    self.tthd = mt_run.getProperty('tthd').value[0]
    self.tthd_units = mt_run.getProperty('tthd').units
    self.S1W = mt_run.getProperty('S1HWidth').value[0]
    self.S1H = mt_run.getProperty('S1VHeight').value[0]

    try:
      self.SiW = mt_run.getProperty('SiHWidth').value[0]
      self.SiH = mt_run.getProperty('SiVHeight').value[0]
      self.isSiThere = True
    except:
      self.S2W = mt_run.getProperty('S2HWidth').value[0]
      self.S2H = mt_run.getProperty('S2VHeight').value[0]

    self.date = mt_run.getProperty('run_start').value

    sample = nxs.getInstrument().getSample()
    source = nxs.getInstrument().getSource()
    self.dMS = sample.getDistance(source) 
    
    #create array of distances pixel->sample
    dPS_array = zeros((256,304)) #TODO MAGIC NUMBER
    for x in range(304):
      for y in range(256):
        _index = 256 * x + y
        detector = nxs.getDetector(_index)
        dPS_array[y,x] = sample.getDistance(detector)
        
    # array of distances pixel->source
    dMP_array = dPS_array + self.dMS
    # distance sample->center of detector
    self.dSD = dPS_array[256/2, 304/2] #TODO MAGIC NUMBER
    # distance source->center of detector
    self.dMD = self.dSD + self.dMS

  def __repr__(self):
    if type(self.origin) is tuple:
      return "<%s '%s' counts: %i>"%(self.__class__.__name__,
                                     "%s/%s"%(os.path.basename(self.origin[0]), self.origin[1]),
                                     self.total_counts)
    else:
      return "<%s '%s' counts: %i>"%(self.__class__.__name__,
                                     "SUM"+repr(self.number),
                                     self.total_counts)

  def _repr_html_(self):
    '''Object representation for IPython'''
    output='<b>%s</b> Object:\n<table border="1">\n'%self.__class__.__name__
    output+='<tr><th>Attribute</th><th>Value</th></tr>\n'
    for attr in ['experiment', 'number', 'total_counts', 'proton_charge',
                 'sangle', 'dangle', 'dangle0', 'dpix']:
      output+='<tr><td>%s</td><td>%s</td></tr>\n'%(attr, str(getattr(self, attr)))
    if type(self.number) is list:
      for i, item in enumerate(self.origin):
        output+='<tr><td>origin[%i][0]</td><td>%s</td></tr>\n'%(i, item[0])
        output+='<tr><td>origin[%i][1]</td><td>%s</td></tr>\n'%(i, item[1])
    else:
      output+='<tr><td>origin[0]</td><td>%s</td></tr>\n'%self.origin[0]
      output+='<tr><td>origin[1]</td><td>%s</td></tr>\n'%self.origin[1]
    output+='</table>'
    return output

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

  if USE_COMPRESSION:
    # data compressed in memory properties, last dataset data is cached for better GUI response
    _data_zipped=None
    _data_dtype=float
    _data_shape=(0,)
    _cached_object=None
    _cached_data=None
    @property
    def data(self):
      if MRDataset._cached_object is self:
        return MRDataset._cached_data
      data=fromstring(zlib.decompress(self._data_zipped), dtype=self._data_dtype)
      data=data.reshape(self._data_shape)
      MRDataset._cached_data=data
      MRDataset._cached_object=self
      return data
    @data.setter
    def data(self, data):
      self._data_zipped=zlib.compress(data.tostring(), 1)
      self._data_dtype=data.dtype
      self._data_shape=data.shape
      MRDataset._cached_data=data
      MRDataset._cached_object=self

  ################## Properties for easy data access ##########################
  # return the size of the data stored in memory for this dataset
  @property
  def nbytes(self): return (len(self._data_zipped)+
                            self.xydata.nbytes+self.xtofdata.nbytes)
  @property
  def rawbytes(self): return (self.data.nbytes+self.xydata.nbytes+self.xtofdata.nbytes)

  if USE_COMPRESSION:
    @property
    def nbytes(self): return (len(self._data_zipped)+
                              self.xydata.nbytes+self.xtofdata.nbytes)
  else:
    nbytes=rawbytes

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

  def get_tth(self, dangle0=None, dpix=None):
    '''
    Return the tth values corresponding to each x-pixel.
    '''
    if dangle0 is None:
      dangle0=self.dangle0
    if dpix is None:
      dpix=self.dpix
    x=self.x
    grad_per_pixel=self.det_size_x/self.dist_sam_det/len(x)*180./pi
    tth0=(self.dangle-dangle0)-(304-dpix)*grad_per_pixel #TODO MAGIC NUMBER
    tth_range=x[::-1]*grad_per_pixel
    return tth0+tth_range

  def get_tthlamda(self, dangle0=None, dpix=None):
    '''
    Return tth and lamda values corresponding to x and tof.
    '''
    return meshgrid(self.lamda, self.get_tth(dangle0, dpix))

  tth=property(get_tth)
  tthlamda=property(get_tthlamda)

  @property
  def p(self):
    '''A attribute to quickly plot data in the qt console'''
    return AttributePloter(self, ['xdata', 'xydata', 'ydata', 'xtofdata', 'tofdata'
                                  , 'data'])

def time_from_header(filename, nxs=None):
  '''
  Read just an nxs header to get the time of a measurement in seconds.
  
  :param str filename: Path to nxs file
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
    sstr=item['start_time'].value[0].decode()
    estr=item['end_time'].value[0].decode()
    if '.' in sstr:
      start_str, start_sub=sstr.split('.', 1)
      start_sub=start_sub.split('-')[0]
      start_time=mktime(strptime(start_str, '%Y-%m-%dT%H:%M:%S'))+float('.'+start_sub)
      end_str, end_sub=estr.split('.', 1)
      end_sub=start_sub.split('-')[0]
      end_time=mktime(strptime(end_str, '%Y-%m-%dT%H:%M:%S'))+float('.'+end_sub)
    else:
      start_str, start_sub=sstr.rsplit('-', 1)
      start_time=mktime(strptime(start_str, '%Y-%m-%dT%H:%M:%S'))
      end_str, end_sub=estr.rsplit('-', 1)
      end_time=mktime(strptime(end_str, '%Y-%m-%dT%H:%M:%S'))
    stime=min(stime, start_time)
    etime=max(etime, end_time)
  if close:
    nxs.close()
  return etime-stime

def locate_file(number, histogram=True, old_format=False):
    '''
    Search the data folders for a specific file number and open it.
    
    :param int number: Run number
    '''
    info('Trying to locate file number %s...'%number)
    if histogram:
      search=glob(os.path.join(instrument.data_base, (instrument.BASE_SEARCH%number)+u'histo.nxs'))
    elif old_format:
      search=glob(os.path.join(instrument.data_base, (instrument.OLD_BASE_SEARCH%(number, number))+u'.nxs'))
    else:
      search=glob(os.path.join(instrument.data_base, (instrument.BASE_SEARCH%number)+u'event.nxs'))
    if search:
      return search[0]
    else:
      return None

class Reflectivity(object):
  """
  Extraction of reflectivity from MRDatatset object storing all data
  and options used for the extraction process.
  """
  __metaclass__=OptionsDocMeta

  #TODO MAGIC NUMBER
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
       sample_length=10.,
       extract_fan=False,
       normalization=None,
       bg_tof_constant=False,
       bg_poly_regions=None,
       bg_scale_xfit=False,
       bg_scale_factor=1.,
       sensitivity_correction=None,
       P0=0,
       PN=0,
       number='0',
       gisans_gridy=50,
       gisans_gridz=50,
       gisans_no_DP=True,
       )
  _OPTIONS_DESCRTIPTION=dict(
       x_pos='X-pixel position of the reflected beam on the detector',
       x_width='Pixel width of the area used to extract the intensity',
       y_pos='Y-pixel position of the are used to extract the intensity',
       y_width='Pixel width in Y-direction to be used to extract the intensity',
       bg_pos='X-pixel position of the background subtraction area (center)',
       bg_width='X-pixel width of the background subtraction area',
       tth='Two Theta of the detector arm',
       dpix='X-pixel position of the direct beam at tth=0',
       scale='Scaling factor for the reflectivity',
       sample_length='Length of the sample in mm, used to calculate the Q-resolution',
       extract_fan='Treat every x-pixel separately and join the data afterwards',
       normalization='another Reflectivity object used for normalization',
       bg_tof_constant='treat background to be independent of wavelength for better statistics',
       bg_poly_regions='use polygon regions in x/λ to determine which points to use for the background',
       bg_scale_xfit='use a linear fit on x-axes projection to scale the background',
       bg_scale_factor='scale the background by this constant before subtraction',
       sensitivity_correction='Detector sensitivity correction to be used',
       P0='Number of points to remove from the low-Q side of the reflectivity',
       PN='Number of points to remove from the high-Q side of the reflectivity',
       number='Index of the origin dataset used for naming etc. when exported',
       gisans_gridy='When extracting GISANS data, this is the number of pixels in Qz',
       gisans_gridz='When extracting GISANS data, this is the number of pixels in Qy',
       gisans_no_DP='Remove the ToF bin which contains the direct pulse background',
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

  def _repr_html_(self):
    '''Object representation for IPython'''
    output='<b>%s</b> Object:\n<table border="1">\n'%self.__class__.__name__
    try:
      output+='<tr><td>#points</td><td>%i</td></tr>\n'%(len(self.Q))
    except AttributeError:
      output+='<tr><td>#points</td><td>%s</td></tr>\n'%(repr(self.Qz.shape))
    if type(self.origin) is list:
      output+='<tr><td>State</td><td>%s</td></tr>\n'%(self.origin[0][1])
      for i, item in enumerate(self.origin):
          output+='<tr><td>origin[%i]</td><td>%s</td></tr>\n'%(i, item[0])
    else:
      output+='<tr><td>State</td><td>%s</td></tr>\n'%(self.origin[1])
      output+='<tr><td>origin</td><td>%s</td></tr>\n'%(self.origin[0])
    output+='</table>See .info attribute for detailed description.\n'
    return output

  @property
  def info(self):
    output='<table border="1">\n'
    try:
      output+='<tr><td>#points</td><td>%i</td></tr>\n'%(len(self.Q))
    except AttributeError:
      output+='<tr><td>#points</td><td>%s</td></tr>\n'%(repr(self.Qz.shape))
    if type(self.origin) is list:
      output+='<tr><td>State</td><td>%s</td></tr>\n'%(self.origin[0][1])
      for i, item in enumerate(self.origin):
          output+='<tr><td>origin[%i]</td><td>%s</td></tr>\n'%(i, item[0])
    else:
      output+='<tr><td>State</td><td>%s</td></tr>\n'%(self.origin[1])
      output+='<tr><td>origin</td><td>%s</td></tr>\n'%(self.origin[0])
    output+='</table><table border="1">\n'
    output+='<tr><th>Option</th><th>Value</th></tr>\n'
    for key, value in sorted(self.options.items()):
      if key=='normalization' and value is not None:
        output+='<tr><td>%s</td><td>%s</td></tr>\n'%(key,
                                    value.origin[0])
      else:
        output+='<tr><td>%s</td><td>%s</td></tr>\n'%(key,
                                    repr(value).replace('<', '[').replace('>', ']'))
    output+='</table>'
    return StringRepr('self.options='+repr(self.options), output)


  @log_call
  def _correct_sensitivity(self, data):
    if self.options['sensitivity_correction'] in DETECTOR_SENSITIVITY:
      return data/DETECTOR_SENSITIVITY[self.options['sensitivity_correction']][:, :, newaxis]
    elif self.options['sensitivity_correction']=='polynomial':
      # use polynomial form to generate sensitivity map
      X, Y=meshgrid(arange(data.shape[0]), arange(data.shape[1]))
      X, Y=X.T.astype(float), Y.T.astype(float)
      ax, ay, bx, by, c=POLY_CORR_PARAMS
      Isens=ax*X**2+ay*Y**2+bx*X+by*Y+c
      Isens/=Isens.mean()
      DETECTOR_SENSITIVITY[self.options['sensitivity_correction']]=Isens
      return data/Isens[:, :, newaxis]
    else:
      raise NotImplementedError, 'sensitivity correction %s not known'%self.options['sensitivity_correction']

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
    
    :param quicknxs.qreduce.MRDataset dataset: The dataset to use for extraction
    """
    tof_edges=dataset.tof_edges
    data=dataset.data
    if self.options['sensitivity_correction'] is not None:
      data=self._correct_sensitivity(data)
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
    
    :param quicknxs.qreduce.MRDataset dataset: The dataset to use for extraction
    """
    tof_edges=dataset.tof_edges
    data=dataset.data
    if self.options['sensitivity_correction'] is not None:
      data=self._correct_sensitivity(data)
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
    
    :param quicknxs.qreduce.MRDataset dataset: The dataset to use for extraction
    '''
    data=dataset.data
    if self.options['sensitivity_correction'] is not None:
      data=self._correct_sensitivity(data)
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
      import matplotlib
      x=dataset.x
      lamda=dataset.lamda
      X, Lamda=meshgrid(x, lamda)
      points=vstack([Lamda.flatten(), X.flatten()]).transpose()
      points_in_region=zeros(X.shape, dtype=bool).flatten()
      # matplotlib 1.2 deprecates nxutils and 1.3 removes it
      if matplotlib.__version__>='1.2':
        debug('Using matplotlib.path for polygon checking')
        from matplotlib.path import Path
        for poly in bg_poly:
          poly_path=Path(poly)
          points_in_region|=poly_path.contains_points(points)
      else:
        debug('Using matplotlib.nxutils for polygon checking')
        from matplotlib.nxutils import points_inside_poly
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

  @log_call
  def get_resolution(self):
    '''
    Calculate the angular resolution given by all slits together with the sample size
    and return the smallest one.
    '''
    res=[]
    s_width=self.options['sample_length']*sin(self.ai)
    for width, dist in self.slits:
      # calculate the maximum opening angle dTheta
      if s_width>0.:
        dTheta=arctan((s_width/2.*(1.+width/s_width))/dist)*2.
      else:
        dTheta=arctan(width/2./dist)*2.
      # standard deviation for a uniform angle distribution is Δθ/√12
      res.append(dTheta*0.28867513)
    debug('Sample Size %.2f\tSample FP: %.5f\tResolutions for slits: %s'%(
                            self.options['sample_length'], s_width, res))
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
    
    :param quicknxs.qreduce.MRDataset dataset: The dataset to use for extraction
    """
    tof_edges=dataset.tof_edges
    data=dataset.data
    if self.options['sensitivity_correction'] is not None:
      data=self._correct_sensitivity(data)
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
    :param quicknxs.qreduce.MRDataset dataset: The dataset to use for extraction
    """
    tof_edges=dataset.tof_edges
    data=dataset.data
    if self.options['sensitivity_correction'] is not None:
      data=self._correct_sensitivity(data)
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

    if self.options['gisans_no_DP']:
      fast_n_tof=[i*1.0e6/60. for i in range(4)]
      tof_edges=dataset.tof_edges[PN:P0]
      fresult=(tof_edges[1:]<fast_n_tof[0])|(tof_edges[:-1]>fast_n_tof[0])
      for fnt in fast_n_tof[1:]:
        fresult&=(tof_edges[1:]<fnt)|(tof_edges[:-1]>fnt)
      fidx=where(fresult)[0]
      # apply filtering to all arrays
      self.Iraw=self.Iraw[:, :, fidx]
      self.dIraw=self.dIraw[:, :, fidx]
      self.I=self.I[:, :, fidx]
      self.dI=self.dI[:, :, fidx]
      self.S=self.S[:, :, fidx]
      self.dS=self.dS[:, :, fidx]
      self.Qx=self.Qx[:, :, fidx]
      self.Qy=self.Qy[:, :, fidx]
      self.Qz=self.Qz[:, :, fidx]

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
