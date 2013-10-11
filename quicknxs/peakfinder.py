#-*- coding: utf8 -*-
'''
Peak finder algorithm based on the continuous wavelet transform (CWT) method
discribed in [PDu2006]_.


Implemented by Artur Glavic (artur.glavic@gmail.com) 2012-2013
'''

import numpy
try:
  from scipy.stats.mstats import mquantiles
except ImportError:
  # use the slightly slower quantiles function that does not rely on scipy
  def mquantiles(data, prob, *ignore): return quantile(data, prob)
from .decorators import time_call

class PeakFinder(object):
  '''
  Peak finder which can be reevaluated with different thresholds 
  without recalculation all steps.
  The steps performed are:
  
    - CWT of the dataset (which also removes the baseline)
    - Finding ridged lines by walking through different CWT scales
    - Calculate signal to noise ratio (SNR)
    - Identify the peaks from the ridged lines 
      (this is where the user parameters enter and can be recalculated fast) 
  '''

  def __init__(self, xdata, ydata, resolution=5):
    xdata=numpy.array(xdata)
    ydata=numpy.array(ydata)
    idx=numpy.argsort(xdata)
    self.xdata=xdata[idx]
    self.ydata=ydata[idx]
    self.resolution=resolution
    self.positions=[]

    self._CWT()
    self._find_ridges()
    self._SNR()

  def _CWT(self):
    '''
    Create the continous wavelet transform for the dataset.
    '''
    self.CWT=MexicanHat(self.ydata,
                        largestscale=1,
                        notes=self.resolution,
                        order=1,
                        scaling='log',
                        )

  def _find_ridges(self, maxgap=4):
    '''
    Ridges are lines connecting local maxima at different
    scales of the CWT. Starting from the highest scale
    (most smooth) the lines are flowed down to the lowest
    scale. Strong peaks will produce longer ridge lines than
    weaker or noise, as they start at higher scales.
    '''
    cwt=self.CWT.getdata()
    scales=self.CWT.getscales()
    # initialize ridges starting at smoothest scaling
    ridges=[]
    gaps=[]
    cwt_len=len(cwt)
    for j, cwti in enumerate(reversed(cwt)):
      local_maxi=self._find_local_max(cwti)
      local_max_positions=numpy.where(local_maxi)[0]
      if len(local_max_positions)==0:
        # if there is no local maximum, continue with next step
        continue
      for i, ridge in enumerate(ridges):
        if gaps[i]<=maxgap:
          ridge_pos=ridge[-1][1]
          min_dist=numpy.abs(local_max_positions-ridge_pos).min()
          if min_dist<=scales[cwt_len-j]:
            idx=numpy.where(numpy.abs(local_max_positions-ridge_pos)==min_dist)[0][0]
            ridge.append([cwt_len-j-1, int(local_max_positions[idx])])
            gaps[i]=0
            local_max_positions[idx]=-1000
          else:
            gaps[i]+=1
      for ridge_pos in local_max_positions[local_max_positions>=0]: #@NoEffect
        gaps.append(0)
        ridges.append([[cwt_len-j-1, ridge_pos]])
    # collect some information on the ridge lines
    evaluated_ridges=[]
    ridge_info=[]
    ridge_intensities=[]
    for ridge in ridges:
      ridge=numpy.array(ridge)
      # len of ridge line and position of last point
      info=[ridge.shape[0], ridge[-1][1]]
      ridge_intensity=[]
      for rs, rx in ridge:
        ridge_intensity.append(cwt[rs, rx])
      ridge_intensity=numpy.array(ridge_intensity)
      max_idx=numpy.argmax(ridge_intensity)
      # scale of maximum coefficient on the ridge line
      #info.append(ridge[max_idx][0])
      info.append(scales[ridge[max_idx][0]])
      info.append(ridge_intensity[max_idx])
      # peak center estimate from ridge maximum
      info.append(ridge[max_idx][1])
      ridge_info.append(info)
      ridge_intensities.append(ridge_intensity)
      evaluated_ridges.append(numpy.vstack([ridge[:, 0], ridge[:, 1], ridge_intensity]))
    self.ridges=evaluated_ridges
    self.ridge_info=ridge_info
    self.ridge_intensities=ridge_intensities

  def _SNR(self, minimum_noise_level=0.001):
    '''
    Calculate signal to noise ratio. Signal is the highest
    CWT intensity of all scales, noise is the 95% quantile
    of the lowest scale WT, which is dominated by noise.
    '''
    ridge_info=self.ridge_info
    cwt=self.CWT.getdata()
    noise_cwt=cwt[0]
    # minimum noise is the noise value for the whole dataset times minimum_noise_level
    minimum_noise=float(minimum_noise_level*mquantiles(
                        noise_cwt,
                        0.95,
                        3./8., 3./8.))
    for info in ridge_info:
      scale=max(3, info[2]) # get a minimal width of 30 items for noise calculation
      signal=info[3]
      base_left=max(0, int(info[1]-scale*5))
      base_right=int(info[1]+scale*5)
      noise=mquantiles(noise_cwt[base_left:base_right+1],
                       0.95,
                       3./8., 3./8.)
      noise=numpy.nan_to_num(noise)
      noise=float(max([minimum_noise, noise]))
      info.append(signal/noise)

  def _find_local_max(self, data, steps=3):
    '''
    Find the positions of local maxima in a set of data.
    A window of size steps is used to check if the central
    point is the largest in the window region.
    '''
    if steps%2==0:
      steps+=1
    windows=[]
    for i in range(steps):
      windows.append(data[i:(-(steps-i-1) or None)])
    windows=numpy.vstack(windows)
    lmax=windows[(steps+1)/2-1]==windows.max(axis=0)
    return numpy.hstack([numpy.zeros(steps//2),
                         lmax,
                         numpy.zeros(steps//2)])

  def get_peaks(self, snr=2.5,
                min_width=None, max_width=None,
                ridge_length=15, analyze=False,
                double_peak_detection=False,
                double_peak_reduced_ridge_length=3,
                estimate_center=False):
    '''
    Return a list of peaks fulfilling the defined conditions.
    
    :param snr: Minimal signal to noise ratio
    :param min_width: Minimal peak width
    :param max_width: Maximal peak width
    :param ridge_length: Minimal ridge line length
    :param analyze: Store information to analyze the filtering
    :param double_peak_detection: Perform a second run, where the ridge_length is reduced near found peaks
    :param estimate_center: Use the x position of the ridge maximum to estimate peak position
    
    :return: List of found peaks as (x0, width, I0, ridge length, SNR)
    '''
    xdata=self.xdata
    if min_width is None:
      min_width=1.5*abs(xdata[1]-xdata[0])
    if max_width is None:
      max_width=0.3*(xdata.max()-xdata.min())
    ridge_info=self.ridge_info

    if analyze:
      self.length_filtered=filter(lambda item: item[0]<ridge_length,
                     ridge_info)
      self.snr_filtered=filter(lambda item: item[5]<snr, ridge_info)
    # filter for signal to noise ratio
    ridge_info=filter(lambda item: item[5]>=snr, ridge_info)
    if double_peak_detection:
      # store peaks filtered by ridge length
      ridge_filtered=filter(lambda item: (item[0]<ridge_length)&
                            (item[0]>=double_peak_reduced_ridge_length),
                            ridge_info)
    # filter for minimum ridge line length
    ridge_info=filter(lambda item: item[0]>=ridge_length,
                     ridge_info)
    # calculate peak info from ridge info
    # peak info items are [center_position, width, intensity]
    peak_info=[]
    for item in ridge_info:
      info=[]
      # x corresponding to index
      if estimate_center:
        info.append(xdata[item[4]])
      else:
        info.append(xdata[item[1]])
      # width corresponding to index width
      i_low=int(item[1]-item[2]/2.)
      i_high=int(item[1]+item[2]/2.)
      if i_low<0:
        i_low=0
      elif i_low==item[1]:
        i_low-=1
      if i_high>=len(xdata):
        i_high=len(xdata)-1
      elif i_high==item[1]:
        i_high+=1
      w_low=xdata[i_low]
      w_high=xdata[i_high]
      w=w_high-w_low
      info.append(float(abs(w)/numpy.sqrt(2.))) # estimated peak FWHM
      # intensity from ridge value (empirical from application to Gauss peak)
      info.append(item[3]*3.)
      # ridge length
      info.append(item[0])
      # SNR
      info.append(item[5])
      peak_info.append(info)
    # filter for peak width
    peak_info=filter(lambda item: (item[1]>=min_width)&(item[1]<=max_width),
                     peak_info)
    if double_peak_detection:
      # detect double-peaks by reducing the ridge-length filtering in adjacency of
      # strong peaks

      # collect peak information of all ridge filtered peaks
      double_peak_info=[]
      for item in ridge_filtered:
        info=[]
        # x corresponding to index
        if estimate_center:
          info.append(xdata[item[4]])
        else:
          info.append(xdata[item[1]])
        # width corresponding to index width
        i_low=int(round(item[1]-item[2]/2.))
        i_high=int(round(item[1]+item[2]/2.))
        if i_low<0:
          i_low=0
        elif i_low==item[1]:
          i_low-=1
        if i_high>=len(xdata):
          i_high=len(xdata)-1
        elif i_high==item[1]:
          i_high+=1
        w_low=xdata[i_low]
        w_high=xdata[i_high]
        w=w_high-w_low
        info.append(float(abs(w))/1.6) # estimated peak width
        # intensity
        info.append(item[3]*3.)
        # ridge length
        info.append(item[0])
        # SNR
        info.append(item[5])
        if (w>=min_width)&(w<=max_width):
          double_peak_info.append(info)
      adjecent_peaks=[]
      for peaki in peak_info:
        # all peaks in SNR/2-sigmas range are used
        # this way peaks close to stronger peaks are found
        adjecent_peaks+=[item for item in double_peak_info if
                        (item[0]>=(peaki[0]-peaki[3]/2.*peaki[1]))
                        and (item[0]<=(peaki[0]+peaki[3]/2.*peaki[1]))
                        and not item in adjecent_peaks
                        ]
      peak_info+=adjecent_peaks
    if analyze:
      width_filtered=zip(ridge_info, peak_info)
      self.width_filtered=filter(lambda item: \
              (item[1][1]<min_width)|(item[1][1]>max_width), width_filtered)
    peak_info.sort()
    return peak_info

  def visualize(self, snr=2.5,
                min_width=None, max_width=None,
                ridge_length=15, double_peak_detection=False,
                double_peak_reduced_ridge_length=3,
                estimate_center=False):
    '''
      Use matplotlib to visualize the peak finding routine.
    '''
    from pylab import figure, plot, semilogy, errorbar, pcolormesh, show, draw, \
                      legend, title, xlabel, ylabel, ylim
    fig=figure(101)
    fig.clear()
    peaks=self.get_peaks(snr, min_width, max_width, ridge_length, True,
                         double_peak_detection, double_peak_reduced_ridge_length,
                         estimate_center)
    mcount=self.ydata[self.ydata>0].min()
    semilogy(self.xdata, numpy.maximum(self.ydata, 0.1*mcount), 'r-', label='Data')
    if len(peaks)>0:
      errorbar([p[0] for p in peaks], [p[2] for p in peaks],
             xerr=[p[1]/2. for p in peaks], fmt='go',
             elinewidth=2, barsabove=True, capsize=6,
             label='Detected Peaks', markersize=10)
    legend()
    xlabel('x')
    ylabel('I')
    ylim((0.5*mcount, None))
    draw()
    fig=figure(102)
    fig.clear()
    pcolormesh(self.CWT.getdata())
    peak_pos=[p[0] for p in peaks]
    snr_filtered=self.snr_filtered
    length_filtered=self.length_filtered
    #width_filtered=[item[0] for item in self.width_filtered]
    if estimate_center:
      xidx=4
    else:
      xidx=1
    for ridge, ridge_info in reversed(zip(self.ridges, self.ridge_info)):
      if self.xdata[ridge_info[xidx]] in peak_pos:
        plot(ridge[1], ridge[0], 'r-', linewidth=3)
      elif ridge_info in length_filtered:
        plot(ridge[1], ridge[0], 'g-', linewidth=2)
      elif ridge_info in snr_filtered:
        plot(ridge[1], ridge[0], 'b-', linewidth=2)
      else:
        plot(ridge[1], ridge[0], "y-")
    title('Detected Peaks (Red) and Filtered by Ridge Length (Green), SNR (Blue), Width (Yellow)')
    xlabel('x')
    ylabel('CWT scale index')
    draw()
    show()


############## Code below here is adapted from an python CWT example ###########
class Cwt:
    """
    Base class for continuous wavelet transforms
    Implements cwt via the Fourier transform
    Used by subclass which provides the method wf(self,s_omega)
    wf is the Fourier transform of the wavelet function.
    Returns an instance.
    
    Naming convention roughly follows [CTorrance1998]_.
    """

    fourierwl=1.00

    def _log2(self, x):
        # utility function to return (integer) log2
        return int(numpy.log2(float(x)))

    def __init__(self, data, largestscale=1, notes=0, order=2, scaling='log'):
        """
        Continuous wavelet transform of data

        :param data:    data in array to transform, length must be power of 2
        :param notes:   number of scale intervals per octave
        :param largestscale: largest scale as inverse fraction of length
                             of data array
                             scale = len(data)/largestscale
                             smallest scale should be >= 2 for meaningful data
        :param order:   Order of wavelet basis function for some families
        :param scaling: Linear or log
        """
        ndata=len(data)
        self.order=order
        self.scale=largestscale
        self._setscales(ndata, largestscale, notes, scaling)
        self.cwt=numpy.zeros((self.nscale, ndata), numpy.float64)
        omega=numpy.array(range(0, ndata+1))*(2.0*numpy.pi/ndata)
        # create a grid twice the size of the original grid to remove boundary
        # effects in the convolution
        scaled_data=numpy.zeros(ndata*2)
        scaled_data[ndata/2:ndata/2+ndata]=data
        scaled_data[ndata/2+ndata:]=data[-10:].mean()
        scaled_data[:ndata/2]=data[:10].mean()
        datahat=numpy.fft.rfft(scaled_data)
        self.fftdata=datahat
        #self.psihat0=self.wf(omega*self.scales[3*self.nscale/4])
        # loop over scales and compute wvelet coeffiecients at each scale
        # using the fft to do the convolution
        for scaleindex in range(self.nscale):
            currentscale=self.scales[scaleindex]
            self.currentscale=currentscale  # for internal use
            s_omega=omega*currentscale
            psihat=self.wf(s_omega)
            # TODO: need to check the math behind it, seems to work better without factor
            #psihat*=numpy.sqrt(2.0*numpy.pi*currentscale)
            convhat=psihat*datahat
            W=numpy.fft.irfft(convhat)
            self.cwt[scaleindex, :]=W[ndata/2:ndata/2+ndata]
        return

    def _setscales(self, ndata, largestscale, notes, scaling):
        """
        if notes non-zero, returns a log scale based on notes per ocave
        else a linear scale
        """
        if scaling=="log":
            if notes<=0: notes=1
            # adjust nscale so smallest scale is 1
            noctave=self._log2(2.*ndata/largestscale)
            self.nscale=notes*noctave
            self.scales=numpy.zeros(self.nscale, float)
            for j in range(self.nscale):
                self.scales[j]=2.0**(float(j)/notes)
        elif scaling=="linear":
            nmax=ndata/largestscale/2
            self.scales=numpy.arange(float(2), float(nmax))
            self.nscale=len(self.scales)
        else: raise ValueError, "scaling must be linear or log"
        return

    def getdata(self):
        """
        returns wavelet coefficient array
        """
        return self.cwt
    def getcoefficients(self):
        return self.cwt
    def getpower(self):
        """
        returns square of wavelet coefficient array
        """
        return (self.cwt*numpy.conjugate(self.cwt)).real
    def getscales(self):
        """
        returns array containing scales used in transform
        """
        return self.scales
    def getnscale(self):
        """
        return number of scales
        """
        return self.nscale

class MexicanHat(Cwt):
    """
    2nd Derivative Gaussian (mexican hat) wavelet
    """
    fourierwl=2.0*numpy.pi/numpy.sqrt(2.5)
    def wf(self, s_omega):
        ss_omega_scaled=(s_omega/2./numpy.pi*numpy.sqrt(2))**2
        # should this number be 1/sqrt(3/4) (no pi)?
        #s_omega = s_omega/self.fourierwl
        #print max(s_omega)
#        a=(s_omega*)**2
#        b=s_omega**2/2.
        return ss_omega_scaled*numpy.exp(-0.5*ss_omega_scaled)/1.1529702
        #return s_omega**2*numpy.exp(-s_omega**2/2.0)/1.1529702

def quantile(a, prob):
    """
    Estimates the prob'th quantile of the values in a data array.

    Uses the algorithm of matlab's quantile(), namely:
        - Remove any nan values
        - Take the sorted data as the (.5/n), (1.5/n), ..., (1-.5/n) quantiles.
        - Use linear interpolation for values between (.5/n) and (1 - .5/n).
        - Use the minimum or maximum for quantiles outside that range.

    See also: scipy.stats.mstats.mquantiles
    """
    a=numpy.asanyarray(a)
    a=a[numpy.logical_not(numpy.isnan(a))].ravel()
    n=a.size

    if prob>=1-.5/n:
        return a.max()
    elif prob<=.5/n:
        return a.min()

    # find the two bounds we're interpreting between:
    # that is, find i such that (i+.5) / n <= prob <= (i+1.5)/n
    t=n*prob-.5
    i=numpy.floor(t)

    # partial sort so that the ith element is at position i, with bigger ones
    # to the right and smaller to the left
    a.sort()

    if i==t: # did we luck out and get an integer index?
        return a[i]
    else:
        # we'll linearly interpolate between this and the next index
        smaller=a[i]
        larger=a[i+1:].min()
        if numpy.isinf(smaller):
            return smaller # avoid inf - inf
        return smaller+(larger-smaller)*(t-i)
