#from plot_dialog_refl import PlotDialogREFL
#from plot2d_dialog_refl import Plot2dDialogREFL
import constants
import time

class SFSinglePlotClick(object):
	
	self = None
	
	def __init__(cls, self, plot_type, is_pan_or_zoom_activated=False):
		cls.self = self
		
		#[row,col] = self.getCurrentRowColumnSelected()
		#_data = self.bigTableData[row, col]
		#self.active_data = _data.active_data
		
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
			pass
			#data = self.active_data
			#dialog_refl = PlotDialogREFL(self, data_type, data)
			#dialog_refl.show()
			
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
			pass
			#data = self.active_data
			#dialog_refl2d = Plot2dDialogREFL(self, data_type, data)
			#dialog_refl2d.show()
			
		self.time_click1 = -1