from PyQt4.QtGui import QDialog, QPalette, QFileDialog, QApplication
from PyQt4.QtCore import Qt
from plot_dialog_refl_interface import Ui_Dialog as UiPlot
from mplwidget import MPLWidget
import colors
import os
import utilities

class PlotSFDialogREFL(QDialog):
	
	main_gui = None
	type = 'data'
	data = None
	
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
	
	def __init__(self, main_gui, active_data, parent=None):

		self.main_gui = main_gui
		self.data = active_data

		QDialog.__init__(self, parent=parent)
		self.setWindowModality(False)
		self._open_instances.append(self)
		self.ui = UiPlot()
		self.ui.setupUi(self)

		self.setWindowTitle('Counts vs Y pixel (Jim and John views)')
		self.hide_and_format_invalid_widgets()
		
		self.ui.plot_counts_vs_pixel.leaveFigure.connect(self.leave_plot_counts_vs_pixel)
		self.ui.plot_counts_vs_pixel.toolbar.homeClicked.connect(self.home_plot_counts_vs_pixel)
		self.ui.plot_counts_vs_pixel.toolbar.exportClicked.connect(self.export_counts_vs_pixel)
		
		self.ui.plot_pixel_vs_counts.leaveFigure.connect(self.leave_plot_pixel_vs_counts)
		self.ui.plot_pixel_vs_counts.toolbar.homeClicked.connect(self.home_plot_pixel_vs_counts)
		self.ui.plot_pixel_vs_counts.toolbar.exportClicked.connect(self.export_counts_vs_pixel)
		
		_new_detector_geometry_flag = self.data.new_detector_geometry_flag
		if not _new_detector_geometry_flag:
			self.reset_max_ui_value()
			self.nbr_pixel_y_axis = 256 #TODO MAGIC NUMBER
		
		self.init_plot()

	def export_counts_vs_pixel(self):

		_active_data = self.data
		run_number = _active_data.run_number
		default_filename = 'REFL_' + str(run_number) + '_rpx.txt'
		_path = self.main_gui.path_ascii
		default_filename = _path + '/' + default_filename
		filename = QFileDialog.getSaveFileName(self, 'Create Counts vs Pixel ASCII File', default_filename)
		
		#user canceled
		if str(filename).strip() == '':
			return
		
		self.main_gui.path_ascii = os.path.dirname(filename)

		ycountsdata = _active_data.ycountsdata
		pixelaxis = range(len(ycountsdata))
		
		text = ['#Couns vs Pixels','#Pixel - Counts']
		sz = len(pixelaxis)
		for i in range(sz):
			_line = str(pixelaxis[i]) + ' ' + str(ycountsdata[i])
			text.append(_line)
			
		utilities.write_ascii_file(filename, text)
	
	def leave_plot_counts_vs_pixel(self):
		[xmin,xmax] = self.ui.plot_counts_vs_pixel.canvas.ax.yaxis.get_view_interval()
		[ymin,ymax] = self.ui.plot_counts_vs_pixel.canvas.ax.xaxis.get_view_interval()
		self.ui.plot_counts_vs_pixel.canvas.ax.xaxis.set_data_interval(xmin,xmax)
		self.ui.plot_counts_vs_pixel.canvas.ax.yaxis.set_data_interval(ymin,ymax)
		self.ui.plot_counts_vs_pixel.draw()
		self.ui.plot_pixel_vs_counts.canvas.ax.xaxis.set_data_interval(ymin,ymax)
		self.ui.plot_pixel_vs_counts.canvas.ax.yaxis.set_data_interval(xmin,xmax)
		self.ui.plot_pixel_vs_counts.draw()
		self.data.all_plot_axis.yi_view_interval = [xmin,xmax,ymin,ymax]
		self.update_pixel_vs_counts_plot()
	
	def home_plot_counts_vs_pixel(self):
		[xmin,xmax,ymin,ymax] = self.data.all_plot_axis.yi_data_interval
		self.ui.plot_counts_vs_pixel.canvas.ax.set_ylim([xmin,xmax])
		self.ui.plot_counts_vs_pixel.canvas.ax.set_xlim([ymin,ymax])
		self.ui.plot_counts_vs_pixel.draw()
		self.ui.plot_pixel_vs_counts.canvas.ax.set_xlim([xmin,xmax])
		self.ui.plot_pixel_vs_counts.canvas.ax.set_ylim([ymin,ymax])
		self.ui.plot_pixel_vs_counts.draw()
	
	def leave_plot_pixel_vs_counts(self):
		[xmin,xmax] = self.ui.plot_pixel_vs_counts.canvas.ax.xaxis.get_view_interval()
		[ymin,ymax] = self.ui.plot_pixel_vs_counts.canvas.ax.yaxis.get_view_interval()
		self.ui.plot_pixel_vs_counts.canvas.ax.xaxis.set_data_interval(xmin,xmax)
		self.ui.plot_pixel_vs_counts.canvas.ax.yaxis.set_data_interval(ymin,ymax)
		self.ui.plot_pixel_vs_counts.draw()
		self.ui.plot_counts_vs_pixel.canvas.ax.xaxis.set_data_interval(ymin,ymax)
		self.ui.plot_counts_vs_pixel.canvas.ax.yaxis.set_data_interval(xmin,xmax)
		self.ui.plot_counts_vs_pixel.draw()
		self.data.all_plot_axis.yi_view_interval = [xmin,xmax,ymin,ymax]
		self.update_counts_vs_pixel_plot()
	
	def home_plot_pixel_vs_counts(self):
		[xmin,xmax,ymin,ymax] = self.data.all_plot_axis.yi_data_interval
		self.ui.plot_pixel_vs_counts.canvas.ax.set_xlim([xmin,xmax])
		self.ui.plot_pixel_vs_counts.canvas.ax.set_ylim([ymin,ymax])
		self.ui.plot_pixel_vs_counts.draw()
		self.ui.plot_counts_vs_pixel.canvas.ax.set_xlim([ymin,ymax])
		self.ui.plot_counts_vs_pixel.canvas.ax.set_ylim([xmin,xmax])
		self.ui.plot_counts_vs_pixel.draw()
		
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

	def sort_peak_back_input(self):
		peak1 = self.ui.jim_peak1.value()
		peak2 = self.ui.jim_peak2.value()
		peak_min = min([peak1,peak2])
		peak_max = max([peak1,peak2])
		if peak_min != peak1:
			self.ui.jim_peak1.setValue(peak2)
			self.ui.john_peak1.setValue(peak2)
			self.ui.jim_peak2.setValue(peak1)
			self.ui.john_peak2.setValue(peak1)
			
		back1 = self.ui.jim_back1.value()
		back2 = self.ui.jim_back2.value()
		back_min = min([back1,back2])
		back_max = max([back1,back2])
		if back_min != back1:
			self.ui.jim_back1.setValue(back2)
			self.ui.john_back1.setValue(back2)
			self.ui.jim_back2.setValue(back1)
			self.ui.john_back2.setValue(back1)
		
	def check_peak_back_input_validity(self):
		peak1 = self.ui.jim_peak1.value()
		peak2 = self.ui.jim_peak2.value()
		back1 = self.ui.jim_back1.value()
		back2 = self.ui.jim_back2.value()

		_show_widgets_1 = False
		_show_widgets_2 = False
		
		if self.ui.jim_back_flag.isChecked():
			if back1 > peak1:
				_show_widgets_1 = True
			if back2 < peak2:
				_show_widgets_2 = True
		
		self.ui.jim_back1_label.setVisible(_show_widgets_1)
		self.ui.jim_peak1_label.setVisible(_show_widgets_1)
		self.ui.jim_back2_label.setVisible(_show_widgets_2)
		self.ui.jim_peak2_label.setVisible(_show_widgets_2)

		self.ui.john_back1_label.setVisible(_show_widgets_1)
		self.ui.john_peak1_label.setVisible(_show_widgets_1)
		self.ui.john_back2_label.setVisible(_show_widgets_2)
		self.ui.john_peak2_label.setVisible(_show_widgets_2)
				
		self.ui.invalid_selection_label.setVisible(_show_widgets_1 or _show_widgets_2)
				
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
		_yaxis = self.data.ycountsdata
		xaxis = range(len(_yaxis))
		self.xaxis = xaxis
		
		_peak = self.data.peak
		_back = self.data.back
		[peak1, peak2] = _peak
		[back1, back2] = _back
		back_flag = self.data.back_flag
		self.ui.jim_back_flag.setChecked(back_flag)
		self.ui.john_back_flag.setChecked(back_flag)
		
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
		ui_plot1.plot(_yaxis, xaxis)
		ui_plot1.canvas.ax.set_xlabel(u'counts')
		ui_plot1.canvas.ax.set_ylabel(u'Pixels')
		if self.isJohnLog:
			ui_plot1.canvas.ax.set_xscale('log')
		else:
			ui_plot1.canvas.ax.set_xscale('linear')
		ui_plot1.canvas.ax.set_ylim(0,self.nbr_pixel_y_axis-1)
		ui_plot1.canvas.ax.axhline(peak1, color=colors.PEAK_SELECTION_COLOR)
		ui_plot1.canvas.ax.axhline(peak2, color=colors.PEAK_SELECTION_COLOR)

		if back_flag:
			ui_plot1.canvas.ax.axhline(back1, color=colors.BACK_SELECTION_COLOR)
			ui_plot1.canvas.ax.axhline(back2, color=colors.BACK_SELECTION_COLOR)
			
		if self.data.all_plot_axis.yi_data_interval is None:
			ui_plot1.draw()
			[xmin,xmax] = self.ui.plot_pixel_vs_counts.canvas.ax.xaxis.get_view_interval()
			[ymin,ymax] = self.ui.plot_pixel_vs_counts.canvas.ax.yaxis.get_view_interval()
			self.data.all_plot_axis.yi_data_interval = [xmin,xmax,ymin,ymax]
			self.data.all_plot_axis.yi_view_interval = [xmin,xmax,ymin,ymax]
			self.ui.plot_pixel_vs_counts.toolbar.home_settings = [xmin,xmax,ymin,ymax]
		else:
			[xmin,xmax,ymin,ymax] = self.data.all_plot_axis.yi_view_interval
			self.ui.plot_pixel_vs_counts.canvas.ax.set_xlim([xmin,xmax])
			self.ui.plot_pixel_vs_counts.canvas.ax.set_ylim([ymin,ymax])
			ui_plot1.draw()

		# Jim
		ui_plot2 = self.ui.plot_counts_vs_pixel
		ui_plot2.canvas.ax.plot(xaxis, _yaxis)
		ui_plot2.canvas.ax.set_xlabel(u'Pixels')
		ui_plot2.canvas.ax.set_ylabel(u'Counts')
		if self.isJimLog:
			ui_plot2.canvas.ax.set_yscale('log')
		else:
			ui_plot2.canvas.ax.set_yscale('linear')
		ui_plot2.canvas.ax.set_xlim(0,self.nbr_pixel_y_axis-1)
		ui_plot2.canvas.ax.axvline(peak1, color=colors.PEAK_SELECTION_COLOR)
		ui_plot2.canvas.ax.axvline(peak2, color=colors.PEAK_SELECTION_COLOR)

		if back_flag:
			ui_plot2.canvas.ax.axvline(back1, color=colors.BACK_SELECTION_COLOR)
			ui_plot2.canvas.ax.axvline(back2, color=colors.BACK_SELECTION_COLOR)
		
		self.ui.plot_counts_vs_pixel.canvas.ax.set_xlim([ymin,ymax])
		self.ui.plot_counts_vs_pixel.canvas.ax.set_ylim([xmin,xmax])
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
		
	def jim_back_flag_clicked(self, status):
		self.ui.john_back_flag.setChecked(status)
		self.data.back_flag = status
		self.update_plots()
		self.update_back_flag_widgets()
		self.check_peak_back_input_validity()		
		
	def john_back_flag_clicked(self, status):
		self.ui.jim_back_flag.setChecked(status)
		self.data.back_flag = status
		self.update_plots()
		self.update_back_flag_widgets()
		self.check_peak_back_input_validity()		

	def update_back_flag_widgets(self):
		status_flag = self.ui.jim_back_flag.isChecked()
		self.ui.jim_back1.setEnabled(status_flag)
		self.ui.jim_back2.setEnabled(status_flag)
		self.ui.john_back1.setEnabled(status_flag)
		self.ui.john_back2.setEnabled(status_flag)
				
	def set_peak_value(self, peak1, peak2):
		self.ui.john_peak1.setValue(peak1)
		self.ui.jim_peak1.setValue(peak1)
		self.ui.john_peak2.setValue(peak2)
		self.ui.jim_peak2.setValue(peak2)
		self.check_peak_back_input_validity()
	
	def set_back_value(self, back1, back2):
		self.ui.john_back1.setValue(back1)
		self.ui.jim_back1.setValue(back1)
		self.ui.john_back2.setValue(back2)
		self.ui.jim_back2.setValue(back2)
		self.check_peak_back_input_validity()

	# peak1
	def update_peak1(self, value, updateJimSpinbox=True,
	                 updateJohnSpinbox=True):
		if updateJimSpinbox:
			self.ui.jim_peak1.setValue(value)
		if updateJohnSpinbox:
			self.ui.john_peak1.setValue(value)
		self._prev_peak1 = value				
	def jim_peak1_spinbox_signal(self):
		value = self.ui.jim_peak1.value()
		if value == self._prev_peak1:
			return
		self.update_peak1(value, updateJimSpinbox=False)
		self.sort_peak_back_input()
		self.check_peak_back_input_validity()
		self.update_plots()
		
	def john_peak1_spinbox_signal(self):
		value = self.ui.john_peak1.value()
		if value == self._prev_peak1:
			return
		self.update_peak1(value, updateJohnSpinbox=False)
		self.sort_peak_back_input()
		self.check_peak_back_input_validity()
		self.update_plots()		

	# peak2
	def update_peak2(self, value, updateJimSpinbox=True,
	                 updateJohnSpinbox=True):
		if updateJimSpinbox:
			self.ui.jim_peak2.setValue(value)
		if updateJohnSpinbox:
			self.ui.john_peak2.setValue(value)
		self._prev_peak2 = value
		self.check_peak_back_input_validity()
		
	def jim_peak2_spinbox_signal(self):
		value = self.ui.jim_peak2.value()
		if value == self._prev_peak2:
			return
		self.update_peak2(value, updateJimSpinbox=False)
		self.sort_peak_back_input()
		self.check_peak_back_input_validity()
		self.update_plots()
				
	def john_peak2_spinbox_signal(self):
		value = self.ui.john_peak2.value()
		if value == self._prev_peak2:
			return
		self.update_peak2(value, updateJohnSpinbox=False)
		self.sort_peak_back_input()
		self.check_peak_back_input_validity()
		self.update_plots()
		
	# back1
	def update_back1(self, value, updateJimSpinbox=True,
	                 updateJohnSpinbox=True):
		if updateJimSpinbox:
			self.ui.jim_back1.setValue(value)
		if updateJohnSpinbox:
			self.ui.john_back1.setValue(value)
		self._prev_back1 = value
		self.check_peak_back_input_validity()			
			
	def jim_back1_spinbox_signal(self):
		value = self.ui.jim_back1.value()
		if value == self._prev_back1:
			return
		self.update_back1(value, updateJimSpinbox=False)
		self.sort_peak_back_input()
		self.check_peak_back_input_validity()		
		self.update_plots()
				
	def john_back1_spinbox_signal(self):
		value = self.ui.john_back1.value()
		if value == self._prev_back1:
			return
		self.update_back1(value, updateJohnSpinbox=False)
		self.sort_peak_back_input()
		self.check_peak_back_input_validity()
		self.update_plots()
				
	# back2
	def update_back2(self, value, updateJimSpinbox=True,
	                 updateJohnSpinbox=True):
		if updateJimSpinbox:
			self.ui.jim_back2.setValue(value)
		if updateJohnSpinbox:
			self.ui.john_back2.setValue(value)
		self._prev_back2 = value
		self.check_peak_back_input_validity()
		
	def jim_back2_spinbox_signal(self):
		value = self.ui.jim_back2.value()
		if value == self._prev_back2:
			return
		self.update_back2(value, updateJimSpinbox=False)
		self.sort_peak_back_input()
		self.check_peak_back_input_validity()
		self.update_plots()
		
	def john_back2_spinbox_signal(self):
		value = self.ui.john_back2.value()
		if value == self._prev_back2:
			return
		self.update_back2(value, updateJohnSpinbox=False)
		self.sort_peak_back_input()
		self.check_peak_back_input_validity()
		self.update_plots()
		
	def update_plots(self):
		self.update_pixel_vs_counts_plot()
		self.update_counts_vs_pixel_plot()
		
	def update_pixel_vs_counts_plot(self):
		self.ui.plot_pixel_vs_counts.clear()
		
		peak1 = self.ui.jim_peak1.value()
		peak2 = self.ui.jim_peak2.value()
		back1 = self.ui.jim_back1.value()
		back2 = self.ui.jim_back2.value()
		_yaxis = self.data.ycountsdata
		
		ui_plot1 = self.ui.plot_pixel_vs_counts
		ui_plot1.canvas.ax.plot(_yaxis, self.xaxis)
		ui_plot1.canvas.ax.set_xlabel(u'counts')
		ui_plot1.canvas.ax.set_ylabel(u'Pixels')
		if self.isJohnLog:
			ui_plot1.canvas.ax.set_xscale('log')
		else:
			ui_plot1.canvas.ax.set_xscale('linear')
		ui_plot1.canvas.ax.axhline(peak1, color=colors.PEAK_SELECTION_COLOR)
		ui_plot1.canvas.ax.axhline(peak2, color=colors.PEAK_SELECTION_COLOR)

		if self.data.back_flag:
			ui_plot1.canvas.ax.axhline(back1, color=colors.BACK_SELECTION_COLOR)
			ui_plot1.canvas.ax.axhline(back2, color=colors.BACK_SELECTION_COLOR)

		[xmin,xmax,ymin,ymax] = self.data.all_plot_axis.yi_view_interval
		self.ui.plot_pixel_vs_counts.canvas.ax.set_xlim([xmin,xmax])
		self.ui.plot_pixel_vs_counts.canvas.ax.set_ylim([ymin,ymax])
		ui_plot1.canvas.draw()
		
	def update_counts_vs_pixel_plot(self):
		self.ui.plot_counts_vs_pixel.clear()
		
		peak1 = self.ui.jim_peak1.value()
		peak2 = self.ui.jim_peak2.value()
		back1 = self.ui.jim_back1.value()
		back2 = self.ui.jim_back2.value()
		_yaxis = self.data.ycountsdata

		ui_plot2 = self.ui.plot_counts_vs_pixel
		ui_plot2.canvas.ax.plot(self.xaxis, _yaxis)
		ui_plot2.canvas.ax.set_xlabel(u'Pixels')
		ui_plot2.canvas.ax.set_ylabel(u'Counts')
		if self.isJimLog:
			ui_plot2.canvas.ax.set_yscale('log')
		else:
			ui_plot2.canvas.ax.set_yscale('linear')
		ui_plot2.canvas.ax.axvline(peak1, color=colors.PEAK_SELECTION_COLOR)
		ui_plot2.canvas.ax.axvline(peak2, color=colors.PEAK_SELECTION_COLOR)
		
		if self.data.back_flag:
			ui_plot2.canvas.ax.axvline(back1, color=colors.BACK_SELECTION_COLOR)
			ui_plot2.canvas.ax.axvline(back2, color=colors.BACK_SELECTION_COLOR)

		[xmin,xmax,ymin,ymax] = self.data.all_plot_axis.yi_view_interval
		self.ui.plot_counts_vs_pixel.canvas.ax.set_xlim([ymin,ymax])
		self.ui.plot_counts_vs_pixel.canvas.ax.set_ylim([xmin,xmax])
		ui_plot2.canvas.draw()
		
	def closeEvent(self, event=None):
		peak1 = self.ui.jim_peak1.value()
		peak2 = self.ui.jim_peak2.value()
		back1 = self.ui.jim_back1.value()
		back2 = self.ui.jim_back2.value()
		back_flag = self.ui.jim_back_flag.isChecked()
		
		self.main_gui.ui.dataPeakFromValue.setValue(peak1)
		self.main_gui.ui.dataPeakToValue.setValue(peak2)
		self.main_gui.ui.dataBackFromValue.setValue(back1)
		self.main_gui.ui.dataBackToValue.setValue(back2)
		self.main_gui.ui.dataBackgroundFlag.setChecked(back_flag)
		QApplication.processEvents()
                self.main_gui.peakBackSpinBoxValueChanged(['peak','back'], with_plot_update=False)
		self.main_gui.testPeakBackErrorWidgets()
		self.main_gui.ui.dataBackFromLabel.setEnabled(back_flag)
		self.main_gui.ui.dataBackFromValue.setEnabled(back_flag)
		self.main_gui.ui.dataBackToLabel.setEnabled(back_flag)
		self.main_gui.ui.dataBackToValue.setEnabled(back_flag)

		self.main_gui.displayPlot()
		
	
