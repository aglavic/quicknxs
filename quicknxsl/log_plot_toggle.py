class LogPlotToggle(object):
	
	def __init__(cls, self, button_status, plot_type, is_y_log=True):
		
		if button_status == 'log':
			isLog = True
		else:
			isLog = False
		
		if plot_type=='stitching':
			[r,c] = [0,0]
		else:
			[r,c] = self.getCurrentRowColumnSelected()
		
		_data = self.bigTableData[r,c]
		data = _data.active_data
		   
		if plot_type=='stitching':
			if is_y_log:
				data.all_plot_axis.is_reduced_plot_stitching_tab_ylog = isLog
			else:
				data.all_plot_axis.is_reduced_plot_stitching_tab_xlog = isLog
		elif plot_type=='yi':
			if is_y_log:
				data.all_plot_axis.is_yi_ylog = isLog
			else:
				data.all_plot_axis.is_yi_xlog = isLog
		elif plot_type=='yt':
			if is_y_log:
				data.all_plot_axis.is_yt_ylog = isLog
			else:
				data.all_plot_axis.is_yt_xlog = isLog
		elif plot_type=='it':
			if is_y_log:
				data.all_plot_axis.is_it_ylog = isLog
			else:
				data.all_plot_axis.is_it_xlog = isLog
		elif plot_type=='ix':
			if is_y_log:
				data.all_plot_axis.is_ix_ylog = isLog
			else:
				data.all_plot_axis.is_ix_xlog = isLog
				
		_data.active_data = data
		self.bigTableData[r,c] = _data
	