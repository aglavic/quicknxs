#-*- coding: utf-8 -*-
'''
Helpers to improve interactivity in ipython.
'''
from numpy import ndarray

class PlottableArray(ndarray):
  '''
  A numpy array that displays a plotted representation, when it is shown in the qt console. 
  '''
  _log=False

  def __new__(cls, other):
    # do not copy any data when this object gets created, only return a new view
    return other.view(cls)

  def _repr_html_(self):
    return 'told ya'

  def _repr_png_(self):
    # to prevent problems with other modules import needed stuff on the fly
    from cStringIO import StringIO
    from matplotlib.colors import LogNorm
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    if self.ndim<3:
      fig=Figure(figsize=[4, 4])
      ax=fig.add_axes([.1, .1, .85, .85])
    else:
      fig=Figure(figsize=[9, 3])
      ax=fig.add_axes([.033, .1, .25, .85])
      ax2=fig.add_axes([.363, .1, .25, .85])
      ax3=fig.add_axes([.693, .1, .25, .85])

    if self.ndim==1:
      ax.plot(self)
      if self._log:
        ax.set_yscale('log')
    elif self.ndim==2:
      if self._log:
        ax.imshow(self, aspect='auto', norm=LogNorm(self[self>0].min()))
      else:
        ax.imshow(self, aspect='auto')
    elif self.ndim==3:
      # for 3D datasets show three projections
      ax.set_title('sum(axis=0)')
      ax2.set_title('sum(axis=1)')
      ax3.set_title('sum(axis=2)')
      if self._log:
        ax.imshow(self.sum(axis=0), aspect='auto', norm=LogNorm(self[self>0].min()))
        ax2.imshow(self.sum(axis=1), aspect='auto', norm=LogNorm(self[self>0].min()))
        ax3.imshow(self.sum(axis=2), aspect='auto', norm=LogNorm(self[self>0].min()))
      else:
        ax.imshow(self.sum(axis=0), aspect='auto')
        ax2.imshow(self.sum(axis=1), aspect='auto')
        ax3.imshow(self.sum(axis=2), aspect='auto')
    else:
      return None

    canvas=FigureCanvasAgg(fig)
    buf=StringIO()
    canvas.print_png(buf)
    return buf.getvalue()

  @property
  def log(self):
    # return a view of this array which gets displayed in logarithmic scale
    output=self.__class__(self)
    output._log=True
    return output

class AttributePloter(object):
  '''
  A class that can be used as an objects property to show a plotted representation
  of array attributes in the qt console of ipython.
  '''
  _parent=None
  _attrs=None

  def __init__(self, parent, attrs):
    self._parent=parent
    self._attrs=attrs

  def __getattribute__(self, name):
    if name.startswith('_') or not name in self._attrs:
      return object.__getattribute__(self, name)
    else:
      return PlottableArray(getattr(self._parent, name))

  def __dir__(self):
    return self.__dict__.keys()+self._attrs
