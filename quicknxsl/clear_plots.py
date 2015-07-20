class ClearPlots(object):
	
	self = None
	
	plot_yt = False
	plot_yi = False
	plot_it = False
	plot_ix = False
	reduced = False
	stitched = False
	
	def __init__(cls, self, is_data=True, 
	             is_norm=False, 
	             plot_yt=False, 
	             plot_yi=False, 
	             plot_it=False, 
	             plot_ix=False, 
	             reduced=False, 
	             stitched=False,
	             all_plots=False):
		cls.self = self
		
		cls.plot_yt = plot_yt
		cls.plot_yi = plot_yi
		cls.plot_it = plot_it
		cls.plot_ix = plot_ix
		cls.reduced = reduced
		cls.stitched = stitched
		
		if all_plots:
			cls.plot_yt = True
			cls.plot_yi = True
			cls.plot_it = True
			cls.plot_ix = True
			cls.reduced = True
			cls.stitched = True
		
		if is_data:
			cls.clear_data_plots()
			self.ui.dataNameOfFile.setText('')
		
		if is_norm:
			cls.clear_norm_plots()
			self.ui.normNameOfFile.setText('')
			
		if cls.reduced:
			cls.clear_reduced()
		
		if cls.stitched:
			cls.clear_stitched()
			
	def clear_data_plots(cls):
		self = cls.self
		if cls.plot_yt:
			self.ui.data_yt_plot.clear()
			self.ui.data_yt_plot.draw()
	  
		if cls.plot_yi:
			self.ui.data_yi_plot.clear()
			self.ui.data_yi_plot.draw()
	  
		if cls.plot_it:
			self.ui.data_it_plot.clear()
			self.ui.data_it_plot.draw()
	  
		if cls.plot_ix:
			self.ui.data_ix_plot.clear()
			self.ui.data_ix_plot.draw()

	def clear_norm_plots(cls):
		self = cls.self
		if cls.plot_yt:
			self.ui.norm_yt_plot.clear()
			self.ui.norm_yt_plot.draw()
	  
		if cls.plot_yi:
			self.ui.norm_yi_plot.clear()
			self.ui.norm_yi_plot.draw()
	  
		if cls.plot_it:
			self.ui.norm_it_plot.clear()
			self.ui.norm_it_plot.draw()
	  
		if cls.plot_ix:
			self.ui.norm_ix_plot.clear()
			self.ui.norm_ix_plot.draw()
	
	def clear_reduced(cls):
		cls.self.ui.reflectivity_plot.clear()
		cls.self.ui.reflectivity_plot.draw()
		
	def clear_stitched(cls):
		cls.self.ui.data_stitching_plot.clear()
		cls.self.ui.data_stitching_plot.draw()
	