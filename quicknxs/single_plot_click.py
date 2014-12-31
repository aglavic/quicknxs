from plotdialogrefl import PlotDialogREFL
from plot2ddialogrefl import Plot2dDialogREFL
import constants
import time

class SinglePlotClick(object):
	
	self = None
	
	def __init__(cls, self, data_type, plot_type, is_pan_or_zoom_activated=False):
		cls.self = self
		
		if plot_type == 'ix':
			return
		
		if plot_type == 'it':
			return
		
		if plot_type == 'stitching':
			return
		
		if plot_type == 'yi':
			cls.single_yi_plot_click(data_type)
		
		if plot_type == 'yt':
			cls.single_yt_plot_click(data_type)
		
	def single_yi_plot_click(cls, data_type):
		self = cls.self
		
		if self.timeClick1 == -1:
			self.timeClick1 = time.time()
			return
		elif abs(self.timeClick1 - time.time()) > 0.5:
			self.timeClick1 = time.time()
			return
		else:
			_timeClick2 = time.time()
	    
		if (_timeClick2 - self.timeClick1) <= constants.double_click_if_within_time:
			data = self.active_data
			dialog_refl = PlotDialogREFL(self, data_type, data)
			dialog_refl.show()
			
		self.timeClick1 = -1
	
	def single_yt_plot_click(cls, data_type):
		self = cls.self

		if self.timeClick1 == -1:
			self.timeClick1 = time.time()
			return
		elif abs(self.timeClick1 - time.time()) > 0.5:
			self.timeClick1 = time.time()
			return
		else:
			_timeClick2 = time.time()
	      
		if (_timeClick2 - self.timeClick1) <= constants.double_click_if_within_time:
			data = self.active_data
			dialog_refl2d = Plot2dDialogREFL(self, data_type, data)
			dialog_refl2d.show()
			