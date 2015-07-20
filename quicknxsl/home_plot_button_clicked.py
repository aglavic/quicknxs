class HomePlotButtonClicked(object):
	
	self = None
	
	def __init__(cls, self, type=None):
		if type is None:
			return
		cls.self = self
		
		[r,c] = self.getCurrentRowColumnSelected()
		_data = self.bigTableData[r,c]
	    
		if _data is None:
			return
		data = _data.active_data
	    
		if data.all_plot_axis.yi_data_interval is None:
			return
		
		if type =='yi':
			[xmin,xmax,ymin,ymax] = data.all_plot_axis.yi_data_interval
			data.all_plot_axis.yi_view_interval = [xmin,xmax,ymin,ymax]
			if c==0:
				_plot_ui = self.ui.data_yi_plot.canvas
			else:
				_plot_ui = self.ui.norm_yi_plot.canvas
				
		elif type == 'yt':
			[xmin,xmax,ymin,ymax] = data.all_plot_axis.yt_data_interval
			data.all_plot_axis.yt_view_interval = [xmin,xmax,ymin,ymax]
			if c==0:
				_plot_ui = self.ui.data_yt_plot.canvas
			else:
				_plot_ui = self.ui.norm_yt_plot.canvas
				
		elif type == 'it':
			[xmin,xmax,ymin,ymax] = data.all_plot_axis.it_data_interval
			data.all_plot_axis.it_view_interval = [xmin,xmax,ymin,ymax]
			if c==0:
				_plot_ui = self.ui.data_it_plot.canvas
			else:
				_plot_ui = self.ui.norm_it_plot.canvas
				
		elif type == 'ix':
			[xmin,xmax,ymin,ymax] = data.all_plot_axis.ix_data_interval
			data.all_plot_axis.ix_view_interval = [xmin,xmax,ymin,ymax]
			if c==0:
				_plot_ui = self.ui.data_ix_plot.canvas
			else:
				_plot_ui = self.ui.norm_ix_plot.canvas

		elif type == 'stitching':
			_data = self.bigTableData[0,0]
			data = _data.active_data
			if data.all_plot_axis.reduced_plot_stitching_tab_data_interval is None:
				return
			[xmin, xmax, ymin, ymax] = data.all_plot_axis.reduced_plot_stitching_tab_data_interval
			_plot_ui = self.ui.data_stitching_plot.canvas
			[r,c] = [0,0]
				

		_data.active_data = data
		self.bigTableData[r,c] = _data
		  
		_plot_ui.ax.set_xlim([xmin, xmax])
		_plot_ui.ax.set_ylim([ymin, ymax])
		_plot_ui.draw()

			
			