class MouseLeavePlot(object):
	
	self = None
	
	def __init__(cls, self, type=None):
		if type is None:
			return
		cls.self = self

		if type == 'stitching':
			cls.leave_figure_plot(type, r=0, c=0)
		else:
			cls.leave_figure_plot(type)

	def leave_figure_plot(cls, type, r=-1, c=-1):
		self = cls.self
		if r==-1 and c==-1:
			[r,c] = self.getCurrentRowColumnSelected()
		bigTableData = self.bigTableData
		_data = bigTableData[r,c]

		if _data is None:
			return
		data = _data.active_data

		if type == 'yi':
			view_interval = data.all_plot_axis.yi_view_interval
			if c==0:
				plot_ui = self.ui.data_yi_plot
			else:
				plot_ui = self.ui.norm_yi_plot
		elif type == 'yt':
			view_interval = data.all_plot_axis.yt_view_interval
			if c==0:
				plot_ui = self.ui.data_yt_plot
			else:
				plot_ui = self.ui.norm_yt_plot
		elif type =='it':
			view_interval = data.all_plot_axis.it_view_interval
			if c==0:
				plot_ui = self.ui.data_it_plot
			else:
				plot_ui = self.ui.norm_it_plot
		elif type =='ix':
			view_interval = data.all_plot_axis.ix_view_interval
			if c==0:
				plot_ui = self.ui.data_ix_plot
			else:
				plot_ui = self.ui.norm_ix_plot
		elif type=='stitching':
			view_interval = data.all_plot_axis.reduced_plot_stitching_tab_view_interval
			plot_ui = self.ui.data_stitching_plot
		    
		[xmin, xmax] = plot_ui.canvas.ax.xaxis.get_view_interval()
		[ymin, ymax] = plot_ui.canvas.ax.yaxis.get_view_interval()
		plot_ui.canvas.ax.xaxis.set_data_interval(xmin, xmax)
		plot_ui.canvas.ax.yaxis.set_data_interval(ymin,ymax)
		plot_ui.draw()
		
		if type == 'yi':
			data.all_plot_axis.yi_view_interval = [xmin,xmax,ymin,ymax]
		elif type == 'yt':
			data.all_plot_axis.yt_view_interval = [xmin,xmax,ymin,ymax]
		elif type =='it':
			data.all_plot_axis.it_view_interval = [xmin,xmax,ymin,ymax]
		elif type =='ix':
			data.all_plot_axis.ix_view_interval = [xmin,xmax,ymin,ymax]
		elif type=='stitching':
			data.all_plot_axis.reduced_plot_stitching_tab_view_interval = [xmin,xmax,ymin,ymax]
	    
		_data.active_data = data
		self.bigTableData[r,c] = _data
		