class AllPlotAxis(object):
	
	plot_axis_data = None
	plot_axis_norm = None
	
	def __init__(self):
		self.plot_axis_data = PlotAxis()
		self.plot_axis_norm = PlotAxis()


class PlotAxis(object):
	
	yt_axis = [-1,-1,-1,-1]
	is_yt_ylog = False
	is_yt_xlog = False

	yi_axis = [-1,-1,-1,-1]
	is_yi_ylog = False
	is_yi_xlog = True
	
	it_axis = [-1,-1,-1,-1]
	is_it_ylog = False
	is_it_xlog = False
	
	ix_axis = [-1,-1,-1,-1]
	is_ix_ylog = False
	is_it_xlog = False
	
	def __init__(self):
		pass
	
	def set_yt_axis(self, xmin, xmax, ymin, ymax):
		self.yt_axis = [xmin, xmax, ymin, ymax]

	def set_yi_axis(self, xmin, xmax, ymin, ymax):
		self.yi_axis = [xmin, xmax, ymin, ymax]

	def set_it_axis(self, xmin, xmax, ymin, ymax):
		self.it_axis = [xmin, xmax, ymin, ymax]

	def set_ix_axis(self, xmin, xmax, ymin, ymax):
		self.ix_axis = [xmin, xmax, ymin, ymax]
		