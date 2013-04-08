#-*- coding: utf-8 -*-
'''
Module for calculations used in data reduction and automatic algorithms.
'''

from numpy import *
from scipy.stats.mstats import mquantiles
from logging import debug
from .decorators import log_input, log_both
from .mreduce import Reflectivity, MRDataset, DETECTOR_X_REGION
from .mpfit import mpfit
from .peakfinder import PeakFinder

# used for * imports
__all__=['get_total_reflection', 'get_scaling', 'get_xpos', 'get_yregion',
         'smooth_data', 'refine_gauss']

#TODO: create a good framework for collections of reflectivities used by GUI and future scripts
class RefCollection(object):
  '''
  Representation of collection of datasets used to calculate
  a full reflectivity pattern.
  If a list or MRDataset objects is given, the normalization and
  scaling is automatically calculated.
  '''

  def __init__(self, datasets=None):
    self.norm=[]
    self.refl=[]
    if datasets is not None:
      for ds in datasets:
        self.autoadd(ds)
      self.scale()

  def autoadd(self, ds):
    '''
    Add a dataset, automatically selecting normalization or
    reflectivity.
    '''
    norm=self.getNorm(ds)
    if norm:
      region=where(norm.Rraw>=(norm.Rraw.max()*0.1))[0]
      P0=len(norm.Rraw)-region[-1]
      PN=region[0]
    else:
      P0=0
      PN=0
    x_pos=get_xpos(ds)
    y_pos, y_width, ignore=get_yregion(ds)
    refl=Reflectivity(ds, normalization=norm, P0=P0, PN=PN,
                      x_pos=x_pos, y_pos=y_pos, y_width=y_width)
    if (refl.ai*180./pi)<0.05:
      self.norm.append(refl)
    else:
      self.refl.append(refl)

  def getNorm(self, ds):
    for norm in self.norm:
      if len(norm.Rraw)==len(ds.tof) and norm.lambda_center==ds.lambda_center:
        return norm
    return None

  def scale(self):
    '''
    Scale all reflectivities by total reflection or stitching to previous dataset.
    '''
    s1=get_total_reflection(self.refl[0])
    self.refl[0].rescale(s1)
    for i, refl1 in enumerate(self.refl[1:]):
      refl2=self.refl[i]
      scale, ignore, ignore=get_scaling(refl1, refl2)
      refl1.rescale(scale)

@log_both
def get_total_reflection(refl, return_npoints=False):
  """
  Calculate the intensity of the total reflection plateau in one dataset.
  Starting from low Q points it searches for a drop in intensity to 
  locate the andge and than returns the weighted mean.
  
  :param refl: Reflectivity object
  
  :returns: scaling, (number of points used for weighted mean)
  """
  if not type(refl) is Reflectivity:
    raise ValueError, "'refl' needs to be a Reflectiviy object"
  last=refl.options['PN']
  first=len(refl.R)-refl.options['P0']
  R=refl.R[last:first]
  dR=refl.dR[last:first][R>0]
  R=R[R>0]
  wmean=1.
  # Start from low Q and search for the critical edge
  for i in range(len(R)-5, 0,-1):
    wmean=(R[i:]/dR[i:]).sum()/(1./dR[i:]).sum()
    Ri=R[i-1]
    if Ri<wmean*0.9:
      break
  if return_npoints:
    return 1./wmean, i
  else:
    return 1./wmean

@log_both
def get_scaling(refl1, refl2, add_points=0, polynom=3):
  """
  Calculate the scaling factor needed to stich one dataset to another.
  
  :param refl1/2: Reflectivity objects
  
  :returns: scaling, array of fitted x and y
  """
  if not (type(refl1) is Reflectivity and type(refl2) is Reflectivity):
    raise ValueError, "'refl1' and 'refl2' need to be Reflectiviy objects"
  last=refl1.options['PN']
  first=len(refl1.R)-refl1.options['P0']
  R1=refl1.R[last:first]
  dR1=refl1.dR[last:first][R1>0]
  Q1=refl1.Q[last:first][R1>0]
  R1=R1[R1>0]
  last=refl2.options['PN']
  first=len(refl2.R)-refl2.options['P0']
  R2=refl2.R[last:first]
  dR2=refl2.dR[last:first][R2>0]
  Q2=refl2.Q[last:first][R2>0]
  R2=R2[R2>0]
  reg1=max(0, where(Q1<=Q2.max())[0][0]-add_points)
  reg2=where(Q2>=Q1.min())[0][-1]+1+add_points
  # try to match both datasets by fitting a polynomial to the overlapping region
  return _refineOverlap(Q1[reg1:], R1[reg1:], dR1[reg1:],
                        Q2[:reg2], R2[:reg2], dR2[:reg2], polynom)

@log_both
def get_xpos(data, dangle0_overwrite=None, direct_pixel_overwrite=-1,
             snr=5, min_width=2, max_width=20, ridge_length=15, return_pf=False, refine=True):
  """
  Calculate the specular or direct beam peak position from data x-projection.
  
  :param data: MRDataset object
  
  :returns: x_center, (Peakfinder)
  """
  if type(data) is not MRDataset:
    raise ValueError, "'data' needs to be a MRDataset object"
  xproj=data.xdata
  # calculate approximate peak position
  if dangle0_overwrite is not None:
    tth_bank=(data.dangle-dangle0_overwrite)*pi/180.
  else:
    tth_bank=(data.dangle-data.dangle0)*pi/180.
  ai=data.sangle*pi/180.
  if direct_pixel_overwrite>=0:
    dp=direct_pixel_overwrite
  else:
    dp=data.dpix
  rad_per_pixel=data.det_size_x/data.dist_sam_det/data.xydata.shape[1]
  pix_position=dp-(ai*2-tth_bank)/rad_per_pixel

  # locate peaks using CWT peak finder algorithm
  pf=PeakFinder(arange(DETECTOR_X_REGION[1]-DETECTOR_X_REGION[0]),
                xproj[DETECTOR_X_REGION[0]:DETECTOR_X_REGION[1]])
  # Signal to noise ratio, minimum width, maximum width, algorithm ridge parameter
  peaks=pf.get_peaks(snr=snr, min_width=min_width, max_width=max_width,
                     ridge_length=ridge_length)
  try:
    x_peaks=array([p[0] for p in peaks])+DETECTOR_X_REGION[0]
    delta_pix=abs(pix_position-x_peaks)
    x_peak=x_peaks[delta_pix==delta_pix.min()][0]
  except:
    x_peak=pix_position
  if refine:
    # refine position with gaussian
    x_peak=refine_gauss(xproj, x_peak, 6.)
  if return_pf:
    return float(x_peak), pf
  else:
    return float(x_peak)

@log_both
def get_yregion(data):
  """
  Calculate the beam y region from data y-projection.
  
  :param data: MRDataset object
  
  :returns: y_center, y_width, y_bg
  """
  yproj=data.ydata
  if type(data) is not MRDataset:
    raise ValueError, "'data' needs to be a MRDataset object"
  # find the central peak reagion with intensities larger than 10% of maximum
  y_bg=mquantiles(yproj, 0.5)[0]
  y_peak_region=where((yproj-y_bg)>yproj.max()/10.)[0]
  yregion=(y_peak_region[0], y_peak_region[-1])
  return (yregion[0]+yregion[1]+1.)/2., yregion[1]+1.-yregion[0], y_bg

@log_input
def refine_gauss(data, pos, width, return_params=False):
  '''
    Fit a gaussian function to a given dataset and return the x0 position.
  '''
  p0=[data[int(pos)], pos, width]
  parinfo=[{'value': p0[i], 'fixed':0, 'limited':[0, 0],
            'limits':[0., 0.]} for i in range(3)]
  parinfo[0]['limited']=[True, False]
  parinfo[0]['limits']=[0., None] # limit to positive intensities
  parinfo[2]['fixed']=True
  res=mpfit(_gauss_residuals, p0, functkw={'data':data}, nprint=0, parinfo=parinfo)
  debug('Result: I=%g  x0=%g niter=%i msg="%s"'%(res.params[0], res.params[1], res.niter,
                                                res.errmsg))
  parinfo[2]['fixed']=False
  parinfo[2]['limited']=[True, True]
  parinfo[2]['limits']=[1., 4.*width]
  p0=[data[int(res.params[1])], res.params[1], width]
  res=mpfit(_gauss_residuals, p0, functkw={'data':data}, nprint=0, parinfo=parinfo)
  debug('Result 2: I=%g  x0=%g w=%g niter=%i msg="%s"'%(res.params[0], res.params[1],
                                                res.params[2], res.niter,
                                                res.errmsg))
  if return_params:
    return res.params
  else:
    return res.params[1]

@log_input
def smooth_data(settings, x, y, I, sigmas=3., axis_sigma_scaling=None, xysigma0=0.06, callback=None):
  '''
    Smooth a irregular spaced dataset onto a regular grid.
    Takes each intensities with a distance < 3*sigma
    to a given grid point and averages their intensities
    weighted by the gaussian of the distance.
  '''
  gridx, gridy=settings['grid']
  sigmax, sigmay=settings['sigma']
  x1, x2, y1, y2=settings['region']
  xout=linspace(x1, x2, gridx)
  yout=linspace(y1, y2, gridy)
  Xout, Yout=meshgrid(xout, yout)
  Iout=zeros_like(Xout)
  ssigmax, ssigmay=sigmax**2, sigmay**2
  imax=len(Xout)
  for i in range(imax):
    if callback is not None and i%5==0:
      progress=float(i)/imax
      callback(progress)
    for j in range(len(Xout[0])):
      xij=Xout[i, j]
      yij=Yout[i, j]
      if axis_sigma_scaling:
        if axis_sigma_scaling==1: xyij=xij
        elif axis_sigma_scaling==2: xyij=yij
        elif axis_sigma_scaling==3: xyij=xij+yij
        if xyij==0:
          continue
        ssigmaxi=ssigmax/xysigma0*xyij
        ssigmayi=ssigmay/xysigma0*xyij
        rij=(x-xij)**2/ssigmaxi+(y-yij)**2/ssigmayi # normalized distance^2
      else:
        rij=(x-xij)**2/ssigmax+(y-yij)**2/ssigmay # normalized distance^2
      take=where(rij<sigmas**2) # take points up to 3 sigma distance
      if len(take[0])==0:
        continue
      Pij=exp(-0.5*rij[take])
      Pij/=Pij.sum()
      Iout[i, j]=(Pij*I[take]).sum()
  return Xout, Yout, Iout

######## helper functions ###############
def _gauss_residuals(p, fjac=None, data=None, width=1):
  '''
    Gaussian of I0, x0 and sigma parameters minus the data.
  '''
  xdata=arange(data.shape[0])
  I0=p[0]
  x0=p[1]
  sigma=p[2]/5.
  G=exp(-0.5*((xdata-x0)/sigma)**2)
  return 0, data-I0*G

class OverlapFunction(object):
  def __init__(self, p0, func):
    self.func=func
    self.p0=list(p0)

  def __call__(self, p, fjac=None,
               x1=None, y1=None, dy1=None,
               x2=None, y2=None, dy2=None):
    part1=(log10(p[0]*y1)-self.func(p[1:], x1))/(dy1/y1)
    part2=(log10(y2)-self.func(p[1:], x2))/(dy2/y2)
    return 0, hstack([part1, part2])

  def plotfunc(self, p, x1, x2):
    xfit=hstack([x1, x2])
    xfit.sort()
    return xfit, 10**self.func(p[1:], xfit)

class OverlapPoly(OverlapFunction):
  def __init__(self, order=3):
    self.order=order
    self.p0=[1.]+[0. for ignore in range(order)]

  def func(self, p, x):
    result=zeros_like(x)
    for i in range(self.order):
      result+=p[-i]*x**i
    return result

class OverlapGaussian(OverlapFunction):
  def __init__(self, x0, sigma0, BG0):
    self.p0=[1., 0.1, x0, sigma0, 0., log10(BG0)]

  def func(self, p, x):
    result=p[0]*exp(-0.5*(x-p[1])**2/p[2]**2)+p[3]*x+p[4]
    return result

@log_input
def _refineOverlap(x1, y1, dy1, x2, y2, dy2, polynom):
  '''
    Refine a polynomial to the logarithm of two datasets while
    scaling the first dataset as well. Return the resulting
    scaling parameter and the refined function for plotting.
    
    :returns: scaling, array of fitted x and y
  '''
  x1=x1.astype(float64)
  y1=y1.astype(float64)
  x2=x2.astype(float64)
  y2=y2.astype(float64)
  if polynom>0:
    # make sure the polynom order is not higher than the number of points
    polynom=min(len(x1)+len(x2), polynom)
    func=OverlapPoly(polynom)
  else:
    func=OverlapGaussian((x1.mean()+x2.mean())/2., 0.001, y2.mean())
  result=mpfit(func, func.p0,
               functkw=dict(
                            x1=x1, y1=y1, dy1=dy1,
                            x2=x2, y2=y2, dy2=dy2
                            ),
               nprint=0)
  xfit, yfit=func.plotfunc(result.params, x1, x2)
  yscale=result.params[0]
  return yscale, xfit, yfit

######################## Data correction algorithms ###########################

class DetectorTailCorrector(object):
  '''
    Try to remove tails of strong peaks from detector xy data using a shape
    function deduced from a direct beam measurement and simulating real
    data convoluted with the shape function until the measured data is found.
  '''
  gamma=12.
  peak_scale=150.
  _epsilon=1e-4

  def __init__(self, detector_I, x0=206):
    self.det_I=detector_I
    self.mshape=self.det_I.shape[0]
    self.fshape=2*self.mshape
    self._gauss_params=[detector_I.max(), refine_gauss(detector_I, x0, 1.5), 1.5, 0.]
    self._fit_shape()

  def _create_shape(self):
    self.shape_function=1./(1.+((arange(self.fshape)-self.mshape-0.5)**2/self.gamma**2))
    self.shape_function[self.mshape]=self.peak_scale
    self.shape_function/=self.shape_function.sum()

  def _compare_shape(self):
    # Used to define a shape function with the assumption that
    # the read direct beam has a gaussian shape
    G=self._gauss_params[0]*exp(-0.5*(arange(self.mshape)-
                                      self._gauss_params[1])**2/
                                      self._gauss_params[2]**2)+self._gauss_params[3]
    Gconv=self.convole_data(G)
    return Gconv, self.det_I-Gconv

  def _compare_residuals(self, p, fjac=None):
    # Function used to fit the shape function and Gauss parameters
    self.gamma=p[0]
    self.peak_scale=p[1]
    self._gauss_params=p[2:]
    self._create_shape()
    Gconv, ignore=self._compare_shape()
    return 0, log(self.det_I[self.det_I>0])-log(Gconv[self.det_I>0])

  def _fit_shape(self):
    '''
      Get the shape function parameters by fitting it to a direct beam measurement.
    '''
    debug('correction parameters before fit gamma=%g  peak_scale=%g'%
                                              (self.gamma, self.peak_scale))
    p0=[self.gamma, self.peak_scale]+self._gauss_params
    parinfo=[{'value': p0[i], 'fixed':0, 'limited':[0, 0],
              'limits':[0., 0.]} for i in range(6)]
    parinfo[5]['limited']=[1, 0]
    result=mpfit(self._compare_residuals, p0, nprint=0, parinfo=parinfo)
    # make sure the shape function is using the resulting parameters
    self._compare_residuals(result.params)
    debug('fit exited with message %s after %i iterations'%(repr(result.errmsg), result.niter))
    debug('correction parameters before fit gamma=%g  peak_scale=%g'%
                                              (self.gamma, self.peak_scale))
    return result

  def correct_shape(self, data):
    if (data==0.).all():
      debug('data is zero, nothing to do')
      return data.copy()
    outshape=data.shape[0]
    if data.shape[0]==self.mshape:
      result=data.copy()
      lendiff=0
    else:
      result=zeros(self.mshape)
      lendiff=self.mshape-data.shape[0]
      result[lendiff/2:data.shape[0]+lendiff/2]=data
      data=result.copy()
    rdiff=data-self.convole_data(result)
    last_diff=abs(rdiff).sum()
    debug('difference at start %g'%last_diff)
    result+=rdiff
    result*=data.sum()/result.sum()
    for ignore in range(20):
      rdiff=data-self.convole_data(result)
      abs_diff=abs(rdiff).sum()
      result+=rdiff
      result*=data.sum()/result.sum()
      if (last_diff-abs_diff)<self._epsilon:
        break
      else:
        last_diff=abs_diff
    debug('difference at end %g'%last_diff)
    return result[lendiff/2:outshape+lendiff/2]

  def correct_shape_set(self, data):
    output=[]
    for line in data:
      output.append(self.correct_shape(line))
    return array(output)

  def _mirror_shape(self):
    '''
      Make the shape function mirror symmetric around the center.
    '''
    sf=self.shape_function
    ms=self.mshape
    sfmax=maximum(sf[:ms], sf[::-1][:ms])
    sf[:ms]=sfmax
    sf[-ms:]=sfmax[::-1]

  def convole_data(self, data):
    conv=convolve(data, self.shape_function, mode='same')
    return conv[self.mshape/2+1:-self.mshape/2+1]

  def __call__(self, data):
    return self.correct_shape_set(data.transpose()).transpose()
