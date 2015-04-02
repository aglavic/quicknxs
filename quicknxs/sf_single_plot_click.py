from plot_sf_dialog_refl import PlotSFDialogREFL
from plot2d_sf_dialog_refl import Plot2dSFDialogREFL
import constants
import time

class SFSinglePlotClick(object):
	
	self = None
	nxsdata = None
	
	def __init__(cls, self, plot_type, is_pan_or_zoom_activated=False):
		cls.self = self
		
		row = self.current_table_row_selected
		list_nxsdata_sorted = self.list_nxsdata_sorted
		cls.nxsdata = list_nxsdata_sorted[row]
		
		if plot_type == 'yi':
			cls.single_yi_plot_click()
		
		if plot_type == 'yt':
			cls.single_yt_plot_click()
		
	def single_yi_plot_click(cls):
		self = cls.self

		if self.time_click1 == -1:
			self.time_click1 = time.time()
			return
		elif abs(self.time_click1 - time.time()) >0.5:
			self.time_click1 = time.time()
			return
		else:
			_time_click2 = time.time()
	    
		if (_time_click2 - self.time_click1) <= constants.double_click_if_within_time:			
			data = cls.nxsdata
			dialog_refl = PlotSFDialogREFL(self, data.active_data)
			dialog_refl.show()
			
		self.time_click1 = -1
	
	def single_yt_plot_click(cls):
		self = cls.self

		if self.time_click1 == -1:
			self.time_click1 = time.time()
			return
		elif abs(self.time_click1 - time.time()) > 0.5:
			self.time_click1 = time.time()
			return
		else:
			_time_click2 = time.time()
	      
		if (_time_click2 - self.time_click1) <= constants.double_click_if_within_time:
			data = cls.nxsdata
			dialog_refl2d = Plot2dSFDialogREFL(self, data.active_data)
			dialog_refl2d.show()
			
		self.time_click1 = -1