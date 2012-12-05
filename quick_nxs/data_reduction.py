#-*- coding: utf-8 -*-
'''
  Module for data readout and evaluation.
  Can also be used stand alone for e.g. interactive processing
  or scripts.
'''

from numpy import pi, sin, cos, sqrt, arange, newaxis, ones_like, argsort
import h5py
from .instrument_constants import *
#from time import time

def read_file(filename):
  #start=time()
  nxs=h5py.File(filename)
  # analyze channels
  channels=nxs.keys()
  for channel in list(channels):
    if nxs[channel][u'total_counts'].value[0]==0:
      channels.remove(channel)
  ana=nxs[channels[0]]['instrument/analyzer/AnalyzerLift/value'].value[0]
  pol=nxs[channels[0]]['instrument/polarizer/PolLift/value'].value[0]
  if abs(ana-ANALYZER_IN[0])<ANALYZER_IN[1]:
    mapping=MAPPING_FULLPOL
  elif abs(pol-POLARIZER_IN[0])<POLARIZER_IN[1]:
    mapping=MAPPING_HALFPOL
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
                }
    data['xydata'].append(raw['bank1']['data_x_y'].value.transpose().astype(float)/norm)
    data['xtofdata'].append(raw['bank1']['data_x_time_of_flight'].value.astype(float)/norm)
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

  reg=map(lambda item: int(round(item)),
          [x_pos-x_width/2., x_pos+x_width/2.,
           y_pos-y_width/2., y_pos+y_width/2.,
           bg_pos-bg_width/2., bg_pos+bg_width/2.])

  Idata=data[reg[0]:reg[1], reg[2]:reg[3], :]
  bgdata=data[reg[4]:reg[5], reg[2]:reg[3], :]
  pix_offset=direct_pixel-x_pos
  tth=tth_bank+pix_offset*RAD_PER_PIX
  ai=tth/2.

  v_edges=TOF_DISTANCE/tof_edges*1e6 #m/s
  lamda_edges=H_OVER_M_NEUTRON/v_edges*1e10 #A
  # calculate ROI intensities and normalize by number of points
  Iraw=Idata.sum(axis=0).sum(axis=0)
  dI=sqrt(Iraw)/(reg[3]-reg[2])/(reg[1]-reg[0])
  I=Iraw/(reg[3]-reg[2])/(reg[1]-reg[0])
  BG=bgdata.sum(axis=0).sum(axis=0)
  dBG=sqrt(BG)/(reg[3]-reg[2])/(reg[5]-reg[4])
  BG/=(reg[3]-reg[2])*(reg[5]-reg[4])

  if ai>0.001:
    Qz_edges=4.*pi/lamda_edges*sin(ai)
  else:
    # for direct beam measurements
    Qz_edges=1./lamda_edges
  R=(I-BG)*scale
  dR=sqrt(dI**2+dBG**2)*scale
  Qz=(Qz_edges[:-1]+Qz_edges[1:])/2.
  return Qz, R, dR, ai, I, BG, Iraw

def calc_fan_reflectivity(data, tof_channels, settings, Inorm):
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
          [x_pos-x_width/2., x_pos+x_width/2.,
           y_pos-y_width/2., y_pos+y_width/2.,
           bg_pos-bg_width/2., bg_pos+bg_width/2.])

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
  R=(I-BG[newaxis, :])*scale/Inorm[newaxis, :]
  dR=sqrt(dI**2+(dBG**2)[newaxis, :])*scale/Inorm[newaxis, :]

  Qz_edges=4.*pi/lamda_edges*sin(ai[:, newaxis])
  Qz=(Qz_edges[:, :-1]+Qz_edges[:, 1:])/2.
  R=R.flatten()
  dR=dR.flatten()
  Qz=Qz.flatten()
  order=argsort(Qz)
  R=R[order].reshape(-1, reg[1]-reg[0]).mean(axis=1)
  dR=sqrt(((dR[order].reshape(-1, reg[1]-reg[0]))**2).mean(axis=1))
  Qz=Qz[order].reshape(-1, reg[1]-reg[0]).mean(axis=1)
  return Qz, R*Inorm, dR*Inorm, 0.2, R, R, R

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
  pix_offset_sped=direct_pixel-x_pos
  tth_spec=tth_bank+pix_offset_sped*RAD_PER_PIX
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
  I=Idata.sum(axis=1)/(reg[3]-reg[2])*scale
  return Qx, Qz, ki_z, kf_z, I
