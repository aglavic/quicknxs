#-*- coding: utf-8 -*-
'''
  Module for data readout and evaluation.
  Can also be used stand alone for e.g. interactive processing
  or scripts.
'''

from numpy import *
import h5py
from .instrument_constants import *
#from time import time

def read_file(filename):
  '''
    Load data from a Nexus file containing histogrammed information.
    
    :return: Dictionary with data and metadata for all channels
  '''
  #start=time()
  nxs=h5py.File(filename, mode='r')
  # analyze channels
  channels=nxs.keys()
  for channel in list(channels):
    if nxs[channel][u'total_counts'].value[0]==0:
      channels.remove(channel)
  if len(channels)==0:
    return None
  ana=nxs[channels[0]]['instrument/analyzer/AnalyzerLift/value'].value[0]
  pol=nxs[channels[0]]['instrument/polarizer/PolLift/value'].value[0]
  
  if abs(ana-ANALYZER_IN[0])<ANALYZER_IN[1]:
    mapping=MAPPING_FULLPOL
  elif abs(pol-POLARIZER_IN[0])<POLARIZER_IN[1]:
    mapping=MAPPING_HALFPOL
  elif len(channels)==3:
    mapping=MAPPING_EFIELD
  else:
    mapping=MAPPING_UNPOL
  data={'channels': [], 'origins':[],
        'xydata': [], 'xtofdata': []}
  for dest, channel in mapping:
    if channel not in channels:
      continue
    data['origins'].append(channel)
    data['channels'].append(dest)
    raw=nxs[channel]
    norm=raw['proton_charge'].value[0]
    data[dest]={
         'pc': norm,
         'counts': raw['total_counts'].value[0],
         'data': raw['bank1/data'].value.astype(float), # 4D dataset
         'tof': raw['bank1/time_of_flight'].value,
         'dangle': raw['instrument/bank1/DANGLE/value'].value[0],
         'tth': raw['instrument/bank1/DANGLE/value'].value[0]-
                raw['instrument/bank1/DANGLE0/value'].value[0],
         'ai': raw['sample/SANGLE/value'].value[0],
         'dp': raw['instrument/bank1/DIRPIX/value'].value[0],
         'beam_width': raw['instrument/aperture3/S3HWidth/value'].value[0],
         'lambda_center': raw['DASlogs/LambdaRequest/value'].value[0],
                }
    data['xydata'].append(raw['bank1']['data_x_y'].value.transpose().astype(float)/norm)
    data['xtofdata'].append(raw['bank1']['data_x_time_of_flight'].value.astype(float)/norm)
  #print time()-start
  nxs.close()
  return data

def read_event_file(filename, bin_type='linear', bins=40, callback=None):
  '''
    Load data from a Nexus file containing event information.
    Creates 3D histogram with ither linear or 1/t spaced 
    time of flight channels. The result has the same format as
    from the read_file function.
    
    :return: Dictionary with data and metadata for all channels
  '''
  #start=time()
  nxs=h5py.File(filename, mode='r')
  # analyze channels
  channels=nxs.keys()
  for channel in list(channels):
    if nxs[channel][u'total_counts'].value[0]==0:
      channels.remove(channel)
  if len(channels)==0:
    return None
  ana=nxs[channels[0]]['instrument/analyzer/AnalyzerLift/value'].value[0]
  pol=nxs[channels[0]]['instrument/polarizer/PolLift/value'].value[0]
  if abs(ana-ANALYZER_IN[0])<ANALYZER_IN[1]:
    mapping=MAPPING_FULLPOL
  elif abs(pol-POLARIZER_IN[0])<POLARIZER_IN[1]:
    mapping=MAPPING_HALFPOL
  elif len(channels)==3:
    mapping=MAPPING_EFIELD
  else:
    mapping=MAPPING_UNPOL
  data={'channels': [], 'origins':[],
        'xydata': [], 'xtofdata': []}
  # create pixal map
  x=arange(304)
  y=arange(256)
  Y, X=meshgrid(y, x)
  X=X.flatten()
  Y=Y.flatten()
  i=0
  for dest, channel in mapping:
    if channel not in channels:
      continue
    i+=1
    data['origins'].append(channel)
    data['channels'].append(dest)
    raw=nxs[channel]
    norm=raw['proton_charge'].value[0]
    tof_ids=array(raw['bank1_events/event_id'].value, dtype=int)
    tof_time=raw['bank1_events/event_time_offset'].value
    tof_x=X[tof_ids]
    tof_y=Y[tof_ids]
    # calculate tof bins
    lcenter=raw['DASlogs/LambdaRequest/value'].value[0]
    tmin=TOF_DISTANCE/H_OVER_M_NEUTRON*(lcenter-1.6)*1e-4
    tmax=TOF_DISTANCE/H_OVER_M_NEUTRON*(lcenter+1.6)*1e-4
    if bin_type.lower()=='linear':
      tof_edges=linspace(tmin, tmax, bins+1)
    elif bin_type.lower()=='1/x':
      tof_edges=1./linspace(1./tmin, 1./tmax, bins+1)
    else:
      raise ValueError, 'Unknown bin type %s'%bin_type

    # create the 3D binning
    Ixyt, D=histogramdd(vstack([tof_x, tof_y, tof_time]).transpose(),
                       bins=(arange(305)-0.5, arange(256)-0.5, tof_edges))
    if callback:
      progress=float(i)/len(channels)
      callback(progress)
    Ixy=Ixyt.sum(axis=2)
    Ixt=Ixyt.sum(axis=1)
    data[dest]={
         'pc': norm,
         'counts': raw['total_counts'].value[0],
         'data': Ixyt, # 4D dataset
         'tof': D[2],
         'dangle': raw['instrument/bank1/DANGLE/value'].value[0],
         'tth': raw['instrument/bank1/DANGLE/value'].value[0]-
                raw['instrument/bank1/DANGLE0/value'].value[0],
         'ai': raw['sample/SANGLE/value'].value[0],
         'dp': raw['instrument/bank1/DIRPIX/value'].value[0],
         'beam_width': raw['instrument/aperture3/S3HWidth/value'].value[0],
         'lambda_center': lcenter,
                }
    data['xydata'].append(Ixy.transpose().astype(float)/norm)
    data['xtofdata'].append(Ixt.astype(float)/norm)
  #print time()-start
  nxs.close()
  return data

def calc_reflectivity(data, tof_channels, settings):
  """
    Extract reflectivity from 4D dataset (x,y,ToF,I).
    Uses a window in x and y to filter the 4D data
    and than sums all I values for each ToF channel.
    Qz is calculated using the x window center position
    together with the tth-bank and direct pixel values.
    Error is also calculated.
    
    Returns: tuple of Qz, R, dR, alpha_i, I, Background
  """
  tof_edges=tof_channels
  x_pos=settings['x_pos']
  x_width=settings['x_width']
  y_pos=settings['y_pos']
  y_width=settings['y_width']
  bg_pos=settings['bg_pos']
  bg_width=settings['bg_width']
  direct_pixel=settings['dp']
  tth_bank=settings['tth']
  scale=settings['scale']/settings['beam_width'] # scale by user factor and beam-size

  # Get regions in pixels as integers
  reg=map(lambda item: int(round(item)),
          [x_pos-x_width/2., x_pos+x_width/2.+1,
           y_pos-y_width/2., y_pos+y_width/2.+1,
           bg_pos-bg_width/2., bg_pos+bg_width/2.+1])

  # restrict the intensity and background data to the given regions
  Idata=data[reg[0]:reg[1], reg[2]:reg[3], :]
  bgdata=data[reg[4]:reg[5], reg[2]:reg[3], :]
  # calculate region size for later use
  size_I=float((reg[3]-reg[2])*(reg[1]-reg[0]))
  size_BG=float((reg[3]-reg[2])*(reg[5]-reg[4]))
  # calculate ROI intensities and normalize by number of points
  Iraw=Idata.sum(axis=0).sum(axis=0)
  dI=sqrt(Iraw)/size_I
  I=Iraw/size_I
  BG=bgdata.sum(axis=0).sum(axis=0)
  dBG=sqrt(BG)/size_BG
  BG/=size_BG
  
  # get incident angle of reflected beam
  pix_offset=direct_pixel-x_pos
  tth=tth_bank+pix_offset*RAD_PER_PIX
  ai=tth/2.
  # set good angular resolution as real resolution not implemented, yet
  dai=0.0001

  v_edges=TOF_DISTANCE/tof_edges*1e6 #m/s
  lamda_edges=H_OVER_M_NEUTRON/v_edges*1e10 #A
  lamda=(lamda_edges[:-1]+lamda_edges[1:])/2.
  # resolution for lambda is digital range with equal probability
  # therefore it is the bin size divided by sqrt(12)
  dlamda=abs(lamda_edges[:-1]-lamda_edges[1:])/sqrt(12)

  if ai>0.001:
    # for reflectivity use Q as x
    x=4.*pi/lamda*sin(ai)
    # error propagation from lambda and angular resolution
    dx=4*pi*sqrt((dlamda/lamda**2*sin(ai))**2+(cos(ai)*dai/lamda)**2)
  else:
    # for direct beam measurements use λ as x
    x=lamda
    dx=dlamda
  # finally scale reflectivity by the given factor and beam width
  R=(I-BG)*scale
  dR=sqrt(dI**2+dBG**2)*scale
  return x, dx, R, dR, ai, I, BG, Iraw

def calc_fan_reflectivity(data, tof_channels, settings, Inorm, P0, PN):
  """
    Extract reflectivity from 4D dataset (x,y,ToF,I).
    Uses a window in x and y to filter the 4D data
    and than sums all I values for each ToF channel.
    
    In contrast to calc_reflectivity this function assumes
    that a brought region reflected from a bend sample is
    analyzed, so each x line corresponds to different alpha i
    values.
    
    Returns: tuple of Qz, R, dR
  """
  tof_edges=tof_channels
  x_pos=settings['x_pos']
  x_width=settings['x_width']
  y_pos=settings['y_pos']
  y_width=settings['y_width']
  bg_pos=settings['bg_pos']
  bg_width=settings['bg_width']
  direct_pixel=settings['dp']
  tth_bank=settings['tth']
  scale=settings['scale']/settings['beam_width'] # scale by user factor and beam-size

  reg=map(lambda item: int(round(item)),
          [x_pos-x_width/2., x_pos+x_width/2.+1,
           y_pos-y_width/2., y_pos+y_width/2.+1,
           bg_pos-bg_width/2., bg_pos+bg_width/2.+1])

  Idata=data[reg[0]:reg[1], reg[2]:reg[3], :]
  bgdata=data[reg[4]:reg[5], reg[2]:reg[3], :]
  x_region=arange(reg[0], reg[1])
  pix_offset=direct_pixel-x_region
  tth=tth_bank+pix_offset*RAD_PER_PIX
  ai=tth/2.

  v_edges=TOF_DISTANCE/tof_edges*1e6 #m/s
  lamda_edges=H_OVER_M_NEUTRON/v_edges*1e10 #A
  # calculate ROI intensities and normalize by number of points
  Iraw=Idata.sum(axis=1)
  dI=sqrt(Iraw)/(reg[3]-reg[2])
  I=Iraw/(reg[3]-reg[2])
  BG=bgdata.sum(axis=0).sum(axis=0)
  dBG=sqrt(BG)/(reg[3]-reg[2])/(reg[5]-reg[4])
  BG/=(reg[3]-reg[2])*(reg[5]-reg[4])
  R=((I-BG[newaxis, :])*scale/Inorm[newaxis, :])[:, PN:P0]
  dR=(sqrt(dI**2+(dBG**2)[newaxis, :])*scale/Inorm[newaxis, :])[:, PN:P0]

  Qz_edges=4.*pi/lamda_edges*sin(ai[:, newaxis])
  Qz=(Qz_edges[:, :-1]+Qz_edges[:, 1:])/2.
  dQz=abs(Qz_edges[:, :-1]-Qz_edges[:, 1:])/2. #sqrt(12) error due to binning
  R=R.flatten()
  dR=dR.flatten()
  Qzf=Qz[:, PN:P0].flatten()
  order=argsort(Qzf)
  R=R[order].reshape(-1, reg[1]-reg[0]).mean(axis=1)
  dR=sqrt(((dR[order].reshape(-1, reg[1]-reg[0]))**2).mean(axis=1))
  Qzf=Qzf[order].reshape(-1, reg[1]-reg[0]).mean(axis=1)
  Rout=zeros_like(Inorm)
  dRout=zeros_like(Inorm)
  Qz=zeros_like(Inorm)
  Rout[PN:P0]=R
  dRout[PN:P0]=dR
  Qz[PN:P0]=Qzf
  return Qz[::-1], dQz[::-1], Rout[::-1]*Inorm, dRout[::-1]*Inorm, ai.mean(), Rout[::-1], Rout[::-1], Rout[::-1]

def calc_offspec(data, tof_channels, settings):
  """
    Extract off-specular scattering from 4D dataset (x,y,ToF,I).
    Uses a window in y to filter the 4D data
    and than sums all I values for each ToF and x channel.
    Qz,Qx,kiz,kfz is calculated using the x and ToF positions
    together with the tth-bank and direct pixel values.
    
    Returns: tuple of Qx, Qz, ki_x, kf_x, I, alpha_i
  """
  tof_edges=tof_channels
  x_pos=settings['x_pos']
  x_width=settings['x_width']
  y_pos=settings['y_pos']
  y_width=settings['y_width']
  bg_pos=settings['bg_pos']
  bg_width=settings['bg_width']
  direct_pixel=settings['dp']
  tth_bank=settings['tth']
  scale=settings['scale']/settings['beam_width'] # scale by user factor and beam-size

  reg=map(lambda item: int(round(item)),
          [x_pos-x_width/2., x_pos+x_width/2.,
           y_pos-y_width/2., y_pos+y_width/2.,
           bg_pos-bg_width/2., bg_pos+bg_width/2.])

  xtth=direct_pixel-arange(data.shape[0])[DETECTOR_X_REGION[0]:DETECTOR_X_REGION[1]]
  pix_offset_spec=direct_pixel-x_pos
  tth_spec=tth_bank+pix_offset_spec*RAD_PER_PIX
  af=tth_bank+xtth*RAD_PER_PIX-tth_spec/2.
  ai=ones_like(af)*tth_spec/2.

  v_edges=TOF_DISTANCE/tof_edges*1e6 #m/s
  lamda_edges=H_OVER_M_NEUTRON/v_edges*1e10 #A
  k_edges=2.*pi/lamda_edges
  k=(k_edges[:-1]+k_edges[1:])/2.

  Qz=k[newaxis, :]*(sin(af)+sin(ai))[:, newaxis]
  Qx=k[newaxis, :]*(cos(af)-cos(ai))[:, newaxis]
  ki_z=k[newaxis, :]*sin(ai)[:, newaxis]
  kf_z=k[newaxis, :]*sin(af)[:, newaxis]

  # calculate ROI intensities and normalize by number of points
  Idata=data[DETECTOR_X_REGION[0]:DETECTOR_X_REGION[1], reg[2]:reg[3], :]
  bgdata=data[reg[4]:reg[5], reg[2]:reg[3], :].sum(axis=0).sum(axis=0)/(reg[3]-reg[2])/(reg[5]-reg[4])
  Iraw=Idata.sum(axis=1)
  dIraw=sqrt(Iraw)
  I=(Iraw/(reg[3]-reg[2])-bgdata[newaxis, :])*scale
  dI=dIraw/(reg[3]-reg[2])*scale
  return Qx, Qz, ki_z, kf_z, I, dI

def smooth_data(settings, x, y, I, sigmas=3., callback=None):
  '''
    Smooth a irregular spaced dataset onto a regular grid.
    Takes each intensities with a distance < 3*sigma
    to a given grid point and averages their intensities
    weighted by the gaussian of the distance.
  '''
  gridx, gridy=settings['grid']
  sigmax, sigmay=settings['sigma']
  ssigmax, ssigmay=sigmax**2, sigmay**2
  x1, x2, y1, y2=settings['region']
  xout=linspace(x1, x2, gridx)
  yout=linspace(y1, y2, gridy)
  Xout, Yout=meshgrid(xout, yout)
  Iout=zeros_like(Xout)
  imax=len(Xout)
  for i in range(imax):
    if callback is not None and i%5==0:
      progress=float(i)/imax
      callback(progress)
    for j in range(len(Xout[0])):
      xij=Xout[i, j]
      yij=Yout[i, j]
      rij=(x-xij)**2/ssigmax+(y-yij)**2/ssigmay # normalized distance^2
      take=where(rij<sigmas**2) # take points up to 3 sigma distance
      Pij=exp(-0.5*rij[take])
      Pij/=Pij.sum()
      Iout[i, j]=(Pij*I[take]).sum()
  return Xout, Yout, Iout
