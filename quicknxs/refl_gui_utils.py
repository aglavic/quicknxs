from PyQt4.QtGui import QDialog, QPalette
from PyQt4.QtCore import Qt
from plot_dialog_refl import Ui_Dialog as UiPlot
from mplwidget import MPLWidget

class PlotDialogREFL(QDialog):
	
	main_gui = None
	type = 'data'
	
	_open_instances = []
	yaxis = None
	peak = None
	back = None
	
	_prev_peak1 = -1
	_prev_peak2 = -1
	_prev_back1 = -1
	_prev_back2 = -1

	isJimLog = True
	isJohnLog = True
	
	nbr_pixel_y_axis = 304
	
	def __init__(self, main_gui, type, yaxis, peak, back, new_detector_geometry_flag, parent=None):

		self.type = type
		self.main_gui = main_gui

		self.yaxis = yaxis
		self.peak = peak
		self.back = back
		_new_detector_geometry_flag = new_detector_geometry_flag

		QDialog.__init__(self, parent=parent)
		self.setWindowModality(False)
		self._open_instances.append(self)
		self.ui = UiPlot()
		self.ui.setupUi(self)

		self.hide_and_format_invalid_widgets()

		if not _new_detector_geometry_flag:
			self.reset_max_ui_value()
			self.nbr_pixel_y_axis = 256
		self.init_plot()
		
	def hide_and_format_invalid_widgets(self):
		palette = QPalette()
		palette.setColor(QPalette.Foreground, Qt.red)
		self.ui.jim_peak1_label.setVisible(False)
		self.ui.jim_peak1_label.setPalette(palette)
		self.ui.jim_peak2_label.setVisible(False)
		self.ui.jim_peak2_label.setPalette(palette)
		self.ui.jim_back1_label.setVisible(False)
		self.ui.jim_back1_label.setPalette(palette)
		self.ui.jim_back2_label.setVisible(False)
		self.ui.jim_back2_label.setPalette(palette)
		self.ui.john_peak1_label.setVisible(False)
		self.ui.john_peak1_label.setPalette(palette)
		self.ui.john_peak2_label.setVisible(False)
		self.ui.john_peak2_label.setPalette(palette)
		self.ui.john_back1_label.setVisible(False)
		self.ui.john_back1_label.setPalette(palette)
		self.ui.john_back2_label.setVisible(False)
		self.ui.john_back2_label.setPalette(palette)
		self.ui.invalid_selection_label.setVisible(False)
		self.ui.invalid_selection_label.setPalette(palette)
		
	def check_widget_format(self):
		'''
		will inform the user if back is inside the peak for example....
		'''
		self.widgets_to_show('peak1', False)
		self.widgets_to_show('peak2', False)
		self.widgets_to_show('back1', False)
		self.widgets_to_show('back2', False)

		peak1 = self.ui.jim_peak1.value()
		peak2 = self.ui.jim_peak2.value()
		back1 = self.ui.jim_back1.value()
		back2 = self.ui.jim_back2.value()
		
		peak_min = min([peak1, peak2])
		peak_max = max([peak1, peak2])
		
		back_min = min([back1, back2])
		back_max = max([back1, back2])
		
		is_peak1_peak_min = (peak1 == peak_min)
		is_peak2_peak_max = (peak2 == peak_max)
		is_back1_back_min = (back1 == back_min)
		is_back2_back_max = (back2 == back_max)
		
		_at_least_one_error = False
		
		if back_min > peak_min:
			_at_least_one_error = True
			if is_peak1_peak_min:
				self.widgets_to_show('peak1', True)
			else:
				self.widgets_to_show('peak2', True)
			
			if is_back1_back_min:
				self.widgets_to_show('back1', True)
			else:
				self.widgets_to_show('back2', True)
				
		if back_max < peak_max:
			_at_least_one_error = True
			if is_peak2_peak_max:
				self.widgets_to_show('peak2', True)
			else:
				self.widgets_to_show('peak1', True)
			
			if is_back2_back_max:
				self.widgets_to_show('back2', True)
			else:
				self.widgets_to_show('back1', True)
				
		self.ui.invalid_selection_label.setVisible(_at_least_one_error)
				
				
	def widgets_to_show(self, widget, status):
		if widget == 'peak1':
			self.ui.jim_peak1_label.setVisible(status)
			self.ui.john_peak1_label.setVisible(status)
		if widget == 'peak2':
			self.ui.jim_peak2_label.setVisible(status)
			self.ui.john_peak2_label.setVisible(status)
		if widget == 'back1':
			self.ui.jim_back1_label.setVisible(status)
			self.ui.john_back1_label.setVisible(status)
		if widget == 'back2':
			self.ui.jim_back2_label.setVisible(status)
			self.ui.john_back2_label.setVisible(status)
		
		
	def reset_max_ui_value(self):
		self.ui.john_peak1.setMaximum(255)
		self.ui.john_peak2.setMaximum(255)
		self.ui.jim_peak1.setMaximum(255)
		self.ui.jim_peak2.setMaximum(255)
		self.ui.john_back1.setMaximum(255)
		self.ui.john_back2.setMaximum(255)
		self.ui.jim_back1.setMaximum(255)
		self.ui.jim_back2.setMaximum(255)

	def init_plot(self):
		xaxis = range(len(self.yaxis))
		self.xaxis = xaxis
		[peak1, peak2] = self.peak
		[back1, back2] = self.back
		
		peak1 = int(peak1)
		peak2 = int(peak2)
		back1 = int(back1)
		back2 = int(back2)
		
		self._prev_peak1 = peak1
		self._prev_peak2 = peak2
		self._prev_back1 = back1
		self._prev_back2 = back2
		
		# John
		ui_plot1 = self.ui.plot_pixel_vs_counts
		ui_plot1.plot(self.yaxis, xaxis)
		ui_plot1.canvas.ax.set_xlabel(u'counts')
		ui_plot1.canvas.ax.set_ylabel(u'Pixels')
		if self.isJohnLog:
			ui_plot1.canvas.ax.set_xscale('log')
		else:
			ui_plot1.canvas.ax.set_xscale('linear')
		ui_plot1.canvas.ax.set_ylim(0,self.nbr_pixel_y_axis-1)
		ui_plot1.canvas.ax.axhline(peak1, color='#00aa00')
		ui_plot1.canvas.ax.axhline(peak2, color='#00aa00')
		ui_plot1.canvas.ax.axhline(back1, color='#aa0000')
		ui_plot1.canvas.ax.axhline(back2, color='#aa0000')
		ui_plot1.draw()

		# Jim
		ui_plot2 = self.ui.plot_counts_vs_pixel
		ui_plot2.canvas.ax.plot(xaxis, self.yaxis)
		ui_plot2.canvas.ax.set_xlabel(u'Pixels')
		ui_plot2.canvas.ax.set_ylabel(u'Counts')
		if self.isJimLog:
			ui_plot2.canvas.ax.set_yscale('log')
		else:
			ui_plot2.canvas.ax.set_yscale('linear')
		ui_plot2.canvas.ax.set_xlim(0,self.nbr_pixel_y_axis-1)
		ui_plot2.canvas.ax.axvline(peak1, color='#00aa00')
		ui_plot2.canvas.ax.axvline(peak2, color='#00aa00')
		ui_plot2.canvas.ax.axvline(back1, color='#aa0000')
		ui_plot2.canvas.ax.axvline(back2, color='#aa0000')
		ui_plot2.draw()
		
		# John and Jim peak and back
		self.set_peak_value(peak1, peak2)
		self.set_back_value(back1, back2)
		
		ui_plot1.logtogx.connect(self.logtogglexlog)
		ui_plot2.logtogy.connect(self.logtoggleylog)

	def logtogglexlog(self, status):
		if status == 'log':
			self.isJohnLog = True
		else:
			self.isJohnLog = False
	
	def logtoggleylog(self, status):
		if status == 'log':
			self.isJimLog = True
		else:
			self.isJimLog = False
		
	def set_peak_value(self, peak1, peak2):
		self.ui.john_peak1.setValue(peak1)
		self.ui.jim_peak1.setValue(peak1)
		self.ui.john_peak2.setValue(peak2)
		self.ui.jim_peak2.setValue(peak2)
		self.check_widget_format()
	
	def set_back_value(self, back1, back2):
		self.ui.john_back1.setValue(back1)
		self.ui.jim_back1.setValue(back1)
		self.ui.john_back2.setValue(back2)
		self.ui.jim_back2.setValue(back2)
		self.check_widget_format()

	# peak1
	def update_peak1(self, value, updateJimSpinbox=True,
	                 updateJohnSpinbox=True):
		if updateJimSpinbox:
			self.ui.jim_peak1.setValue(value)
		if updateJohnSpinbox:
			self.ui.john_peak1.setValue(value)
		self._prev_peak1 = value
		self.check_widget_format()
				
	def jim_peak1_spinbox_signal(self, value):
		if value == self._prev_peak1:
			return
		self.update_peak1(value, updateJimSpinbox=False)
		self.update_plot()
		
	def john_peak1_spinbox_signal(self, value):
		if value == self._prev_peak1:
			return
		self.update_peak1(value, updateJohnSpinbox=False)
		self.update_plot()		

	# peak2
	def update_peak2(self, value, updateJimSpinbox=True,
	                 updateJohnSpinbox=True):
		if updateJimSpinbox:
			self.ui.jim_peak2.setValue(value)
		if updateJohnSpinbox:
			self.ui.john_peak2.setValue(value)
		self._prev_peak2 = value
		self.check_widget_format()
		
	def jim_peak2_spinbox_signal(self, value):
		if value == self._prev_peak2:
			return
		self.update_peak2(value, updateJimSpinbox=False)
		self.update_plot()
				
	def john_peak2_spinbox_signal(self, value):
		if value == self._prev_peak2:
			return
		self.update_peak2(value, updateJohnSpinbox=False)
		self.update_plot()
		
	# back1
	def update_back1(self, value, updateJimSpinbox=True,
	                 updateJohnSpinbox=True):
		if updateJimSpinbox:
			self.ui.jim_back1.setValue(value)
		if updateJohnSpinbox:
			self.ui.john_back1.setValue(value)
		self._prev_back1 = value
		self.check_widget_format()			
			
	def jim_back1_spinbox_signal(self, value):
		if value == self._prev_back1:
			return
		self.update_back1(value, updateJimSpinbox=False)
		self.update_plot()
				
	def john_back1_spinbox_signal(self, value):
		if value == self._prev_back1:
			return
		self.update_back1(value, updateJohnSpinbox=False)
		self.update_plot()
				
	# back2
	def update_back2(self, value, updateJimSpinbox=True,
	                 updateJohnSpinbox=True):
		if updateJimSpinbox:
			self.ui.jim_back2.setValue(value)
		if updateJohnSpinbox:
			self.ui.john_back2.setValue(value)
		self._prev_back2 = value
		self.check_widget_format()
		
	def jim_back2_spinbox_signal(self, value):
		if value == self._prev_back2:
			return
		self.update_back2(value, updateJimSpinbox=False)
		self.update_plot()
		
	def john_back2_spinbox_signal(self, value):
		if value == self._prev_back2:
			return
		self.update_back2(value, updateJohnSpinbox=False)
		self.update_plot()
						
	# check widgets 	
	def make_sure_peak1_lt_peak2(self):
		peak1 = self.ui.jim_peak1.value()
		peak2 = self.ui.jim_peak2.value()
		if peak1>peak2:
			self.update_peak1(peak2)
			self.update_peak2(peak1)

	def make_sure_peak2_gt_peak1(self):
		peak1 = self.ui.jim_peak1.value()
		peak2 = self.ui.jim_peak2.value()
		if peak2 < peak1:
			self.update_peak1(peak2)
			self.update_peak2(peak1)
		
	def make_sure_back1_lt_back2(self):
		back1 = self.ui.jim_back1.value()
		back2 = self.ui.jim_back2.value()
		if back1>back2:
			self.update_back1(back2)
			self.update_back2(back1)
		
	def make_sure_back2_gt_back1(self):
		back1 = self.ui.jim_back1.value()
		back2 = self.ui.jim_back2.value()
		if back2<back1:
			self.update_back1(back2)
			self.update_back2(back1)
		
	def update_plot(self):
		self.ui.plot_counts_vs_pixel.clear()
		self.ui.plot_pixel_vs_counts.clear()

		peak1 = self.ui.jim_peak1.value()
		peak2 = self.ui.jim_peak2.value()
		back1 = self.ui.jim_back1.value()
		back2 = self.ui.jim_back2.value()
		
		# John
		ui_plot1 = self.ui.plot_pixel_vs_counts
		ui_plot1.canvas.ax.plot(self.yaxis, self.xaxis)
		ui_plot1.canvas.ax.set_xlabel(u'counts')
		ui_plot1.canvas.ax.set_ylabel(u'Pixels')
		if self.isJohnLog:
			ui_plot1.canvas.ax.set_xscale('log')
		else:
			ui_plot1.canvas.ax.set_xscale('linear')
		ui_plot1.canvas.ax.set_ylim(0,self.nbr_pixel_y_axis-1)		
		ui_plot1.canvas.ax.axhline(peak1, color='#00aa00')
		ui_plot1.canvas.ax.axhline(peak2, color='#00aa00')
		ui_plot1.canvas.ax.axhline(back1, color='#aa0000')
		ui_plot1.canvas.ax.axhline(back2, color='#aa0000')
		ui_plot1.canvas.draw()

		# Jim
		ui_plot2 = self.ui.plot_counts_vs_pixel
		ui_plot2.canvas.ax.plot(self.xaxis, self.yaxis)
		ui_plot2.canvas.ax.set_xlabel(u'Pixels')
		ui_plot2.canvas.ax.set_ylabel(u'Counts')
		if self.isJimLog:
			ui_plot2.canvas.ax.set_yscale('log')
		else:
			ui_plot2.canvas.ax.set_yscale('linear')
		ui_plot2.canvas.ax.set_xlim(0,self.nbr_pixel_y_axis-1)
		ui_plot2.canvas.ax.axvline(peak1, color='#00aa00')
		ui_plot2.canvas.ax.axvline(peak2, color='#00aa00')
		ui_plot2.canvas.ax.axvline(back1, color='#aa0000')
		ui_plot2.canvas.ax.axvline(back2, color='#aa0000')
		ui_plot2.canvas.draw()
		
	def closeEvent(self, event=None):
		# collect peak and back values
		peak1 = self.ui.jim_peak1.value()
		peak2 = self.ui.jim_peak2.value()
		back1 = self.ui.jim_back1.value()
		back2 = self.ui.jim_back2.value()
		
		peak_min = min([peak1, peak2])
		peak_max = max([peak1, peak2])
		
		back_min = min([back1, back2])
		back_max = max([back1, back2])
		
		if self.type == 'data':
			self.main_gui.ui.dataPeakFromValue.setValue(peak_min)
			self.main_gui.ui.dataPeakToValue.setValue(peak_max)
			self.main_gui.ui.dataBackFromValue.setValue(back_min)
			self.main_gui.ui.dataBackToValue.setValue(back_max)
			self.main_gui.data_peak_and_back_validation(False)
		else:
			self.main_gui.ui.normPeakFromValue.setValue(peak_min)
			self.main_gui.ui.normPeakToValue.setValue(peak_max)
			self.main_gui.ui.normBackFromValue.setValue(back_min)
			self.main_gui.ui.normBackToValue.setValue(back_max)
			self.main_gui.norm_peak_and_back_validation(False)

		self.main_gui.plot_overview_REFL(plot_it=False, plot_ix=False)
		
	