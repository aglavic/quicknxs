from PyQt4.QtGui import QDialog, QPalette, QFileDialog
from PyQt4.QtCore import Qt
from plot2d_dialog_refl_interface import Ui_Dialog as UiPlot
from mplwidget import MPLWidget
import colors
import utilities
import os
from logging import info

class Plot2dSFDialogREFL(QDialog):
	
	main_gui = None
	_open_instances = []
	data = None
	type = 'data'
	
	manual_min_tof = None
	manual_max_tof = None
	
	auto_min_tof = None
	auto_max_tof = None
	
	def __init__(self, main_gui, active_data, parent=None):

		self.main_gui = main_gui
		self.data = active_data
		
		QDialog.__init__(self, parent=parent)
		self.setWindowModality(False)
		self._open_instances.append(self)
		self.ui = UiPlot()
		self.ui.setupUi(self)
		
		self.setWindowTitle('Detector and  Pixel vs TOF  views')
		self.init_gui()
		self.populate_widgets()
		self.init_home_settings()
		
		self.update_detector_tab_plot()
		self.update_pixel_vs_tof_tab_plot()
		
		self.ui.y_pixel_vs_tof_plot.leaveFigure.connect(self.leave_figure_plot)
		self.ui.y_pixel_vs_tof_plot.toolbar.homeClicked.connect(self.home_clicked_plot)
		self.ui.y_pixel_vs_tof_plot.toolbar.exportClicked.connect(self.export_yt)
		
		self.ui.detector_plot.leaveFigure.connect(self.leave_figure_detector_plot)
		self.ui.detector_plot.toolbar.homeClicked.connect(self.home_clicked_detector_plot)
		self.ui.detector_plot.toolbar.exportClicked.connect(self.export_detector_view)
		
		# hide low_res widgets
		self.ui.frame_20.setVisible(False)
		
	def export_yt(self):
		_active_data = self.data
		run_number = _active_data.run_number
		default_filename = 'REFL_' + run_number + '_2dPxVsTof.txt'
		path = self.main_gui.path_ascii
		default_filename = path + '/' + default_filename
		filename = QFileDialog.getSaveFileName(self, 'Create 2D Pixel VS TOF', default_filename)
	      
		if str(filename).strip() == '':
			info('User Canceled Outpout ASCII')
			return
		
		self.main_gui.path_ascii = os.path.dirname(filename)
		image = _active_data.ytofdata
		utilities.output_2d_ascii_file(filename, image)

	def export_detector_view(self):
		_active_data = self.data
		run_number = _active_data.run_number
		default_filename = 'REFL_' + run_number + '_2dDetectorView.txt'
		path = self.main_gui.path_ascii
		default_filename = path + '/' + default_filename
		filename = QFileDialog.getSaveFileName(self, 'Create 2D Y Pixel VS X Pixel (Detector View)', default_filename)
	      
		if str(filename).strip() == '':
			info('User Canceled Outpout ASCII')
			return
		
		self.main_gui.path_ascii = os.path.dirname(filename)
		image = _active_data.xydata
		utilities.output_2d_ascii_file(filename, image)

	def 	init_home_settings(self):
		home_settings_1 = self.main_gui.ui.yt_plot.toolbar.home_settings
		self.ui.y_pixel_vs_tof_plot.toolbar.home_settings = home_settings_1
		
	def leave_figure_plot(self):
		[xmin, xmax]= self.ui.y_pixel_vs_tof_plot.canvas.ax.xaxis.get_view_interval()
		[ymin, ymax]= self.ui.y_pixel_vs_tof_plot.canvas.ax.yaxis.get_view_interval()
		self.ui.y_pixel_vs_tof_plot.canvas.ax.xaxis.set_data_interval(xmin, xmax)
		self.ui.y_pixel_vs_tof_plot.canvas.ax.yaxis.set_data_interval(ymin, ymax)
		self.ui.y_pixel_vs_tof_plot.draw()
		self.data.all_plot_axis.yt_view_interval = [xmin, xmax, ymin, ymax]
		
	def home_clicked_plot(self):
#		[xmin,xmax,ymin,ymax] = self.data.all_plot_axis.yt_data_interval
		[xmin,xmax,ymin,ymax] = self.ui.y_pixel_vs_tof_plot.toolbar.home_settings
		self.ui.y_pixel_vs_tof_plot.canvas.ax.set_xlim([xmin,xmax])
		self.ui.y_pixel_vs_tof_plot.canvas.ax.set_ylim([ymin,ymax])
		self.ui.y_pixel_vs_tof_plot.draw()

	def leave_figure_detector_plot(self):
		[xmin, xmax]= self.ui.detector_plot.canvas.ax.xaxis.get_view_interval()
		[ymin, ymax]= self.ui.detector_plot.canvas.ax.yaxis.get_view_interval()
		self.ui.detector_plot.canvas.ax.xaxis.set_data_interval(xmin, xmax)
		self.ui.detector_plot.canvas.ax.yaxis.set_data_interval(ymin, ymax)
		self.ui.detector_plot.draw()
		self.data.all_plot_axis.detector_view_interval = [xmin, xmax, ymin, ymax]
		
	def home_clicked_detector_plot(self):
		[xmin,xmax,ymin,ymax] = self.data.all_plot_axis.detector_data_interval
		self.ui.detector_plot.canvas.ax.set_xlim([xmin,xmax])
		self.ui.detector_plot.canvas.ax.set_ylim([ymin,ymax])
		self.ui.detector_plot.draw()

	def update_detector_tab_plot(self):
		self.ui.detector_plot.clear()
		xydata = self.data.xydata
		self.ui.detector_plot.draw()
		
		[ymax,xmax] = xydata.shape
		self.ui.detector_plot.imshow(xydata, log=True, aspect='auto',
		                             origin='lower', extent=[0,xmax,0,ymax])
		self.ui.detector_plot.set_xlabel(u'x (pixel)')
		self.ui.detector_plot.set_ylabel(u'y (pixel)')
	
		[peak1, peak2, back1, back2, backFlag] = self.retrievePeakBack()
	
		p1 = self.ui.detector_plot.canvas.ax.axhline(peak1, color=colors.PEAK_SELECTION_COLOR)
		p2 = self.ui.detector_plot.canvas.ax.axhline(peak2, color=colors.PEAK_SELECTION_COLOR)
		
		if backFlag:
			b1 = self.ui.detector_plot.canvas.ax.axhline(back1, color=colors.BACK_SELECTION_COLOR)
			b2 = self.ui.detector_plot.canvas.ax.axhline(back2, color=colors.BACK_SELECTION_COLOR)
	
		if self.data.all_plot_axis.detector_data_interval is None:
			self.ui.detector_plot.draw()
			[xmin,xmax] = self.ui.detector_plot.canvas.ax.xaxis.get_view_interval()
			[ymin,ymax] = self.ui.detector_plot.canvas.ax.yaxis.get_view_interval()
			self.data.all_plot_axis.detector_data_interval = [xmin, xmax, ymin, ymax]
			self.data.all_plot_axis.detector_view_interval = [xmin, xmax, ymin, ymax]
			self.ui.detector_plot.toolbar.home_settings = [xmin, xmax, ymin, ymax]
		else:
			[xmin, xmax, ymin, ymax] = self.data.all_plot_axis.detector_view_interval
			self.ui.detector_plot.canvas.ax.set_xlim([xmin, xmax])
			self.ui.detector_plot.canvas.ax.set_ylim([ymin, ymax])
			self.ui.detector_plot.draw()
	
	def update_pixel_vs_tof_tab_plot(self):
		ytof = self.data.ytofdata
		tof_axis = self.data.tof_axis_auto_with_margin
		tof_from = tof_axis[0]
		tof_to = tof_axis[-1]
		if tof_from > 1000: # stay in ms
			tof_from /= 1000.
			tof_to /= 1000.
		pixel_from = 0
		pixel_to = self.data.y.shape[0]-1
		
		self.ui.y_pixel_vs_tof_plot.clear()
		self.ui.y_pixel_vs_tof_plot.imshow(ytof, log=True, aspect='auto',
		                                   origin='lower', extent=[tof_from, tof_to, pixel_from, pixel_to])
		self.ui.y_pixel_vs_tof_plot.set_xlabel(u't (ms)')
		self.ui.y_pixel_vs_tof_plot.set_ylabel(u'y (pixel)')

		[tmin,tmax,peak1,peak2,back1,back2,backFlag] = self.retrieveTofPeakBack()
		if tmin > 1000: # stay in ms
			tmin /= 1000
			tmax /= 1000
		
		t1 = self.ui.y_pixel_vs_tof_plot.canvas.ax.axvline(tmin, color=colors.TOF_SELECTION_COLOR)
		t2 = self.ui.y_pixel_vs_tof_plot.canvas.ax.axvline(tmax, color=colors.TOF_SELECTION_COLOR)
		
		p1 = self.ui.y_pixel_vs_tof_plot.canvas.ax.axhline(peak1, color=colors.PEAK_SELECTION_COLOR)
		p2 = self.ui.y_pixel_vs_tof_plot.canvas.ax.axhline(peak2, color=colors.PEAK_SELECTION_COLOR)
		
		if backFlag:
			b1 = self.ui.y_pixel_vs_tof_plot.canvas.ax.axhline(back1, color=colors.BACK_SELECTION_COLOR)
			b2 = self.ui.y_pixel_vs_tof_plot.canvas.ax.axhline(back2, color=colors.BACK_SELECTION_COLOR)
		
		if self.data.all_plot_axis.yt_data_interval is None:
			self.ui.y_pixel_vs_tof_plot.canvas.ax.set_ylim(0,pixel_to)
			self.ui.y_pixel_vs_tof_plot.canvas.draw()
			[xmin,xmax] = self.ui.y_pixel_vs_tof_plot.canvas.ax.xaxis.get_view_interval()
			[ymin,ymax] = self.ui.y_pixel_vs_tof_plot.canvas.ax.yaxis.get_view_interval()
			self.data.all_plot_axis.yt_data_interval = [xmin, xmax, ymin, ymax]
			self.data.all_plot_axis.yt_view_interval = [xmin, xmax, ymin, ymax]
			self.ui.y_pixel_vs_tof_plot.toolbar.home_settings = [xmin, xmax, ymin, ymax]
		else:
			[xmin,xmax,ymin,ymax] = self.data.all_plot_axis.yt_view_interval
			self.ui.y_pixel_vs_tof_plot.canvas.ax.set_xlim([xmin,xmax])
			self.ui.y_pixel_vs_tof_plot.canvas.ax.set_ylim([ymin,ymax])
			self.ui.y_pixel_vs_tof_plot.draw()
		
	def retrieveTofPeakBack(self):
		tmin = float(self.ui.tof_from.text())
		tmax = float(self.ui.tof_to.text())
		[peak1,peak2,back1,back2, backFlag] = self.retrievePeakBack()
		return [tmin, tmax, peak1, peak2, back1, back2, backFlag]
				
	def retrievePeakBack(self):
		peak1 = self.ui.peak1.value()
		peak2 = self.ui.peak2.value()
		back1 = self.ui.back1.value()
		back2 = self.ui.back2.value()
		backFlag = self.ui.back_flag.isChecked()
		return [peak1,peak2,back1,back2,backFlag]
		
	def init_gui(self):
		palette = QPalette()
		palette.setColor(QPalette.Foreground, Qt.red)
		if self.data.new_detector_geometry_flag:
			yrange = [0,303]
			xrange = [0,255]
		else:
			yrange = [0,255]
			xrange = [0,303]
		self.ui.error_label.setVisible(False)
		self.ui.error_label.setPalette(palette)
		
		self.ui.peak1_label.setVisible(False)
		self.ui.peak1_label.setPalette(palette)
		self.ui.peak2_label.setVisible(False)
		self.ui.peak2_label.setPalette(palette)
		self.ui.back1_label.setVisible(False)
		self.ui.back1_label.setPalette(palette)
		self.ui.back2_label.setVisible(False)
		self.ui.back2_label.setPalette(palette)
		
		# peak
		self.ui.peak1.setMinimum(yrange[0])
		self.ui.peak1.setMaximum(yrange[1])
		self.ui.peak2.setMinimum(yrange[0])
		self.ui.peak2.setMaximum(yrange[1])

		# back
		self.ui.back1.setMinimum(yrange[0])
		self.ui.back1.setMaximum(yrange[1])
		self.ui.back2.setMinimum(yrange[0])
		self.ui.back2.setMaximum(yrange[1])

		# low res
		self.ui.low_res1.setMinimum(xrange[0])
		self.ui.low_res1.setMaximum(xrange[1])
		self.ui.low_res2.setMinimum(xrange[0])
		self.ui.low_res2.setMaximum(xrange[1])
		
	def populate_widgets(self):
		_data = self.data

		peak = _data.peak
		back = _data.back
		back_flag = _data.back_flag
		tof_auto_flag = _data.tof_auto_flag
		tof_range_auto = _data.tof_range_auto
		tof_range = _data.tof_range
	
		# make sure we are in ms
		tof_range_auto_min = float(tof_range_auto[0])
		tof_range_auto_max = float(tof_range_auto[1])
		if tof_range_auto_min > 1000:
			tof_range_auto_min /= 1000.
			tof_range_auto_max /= 1000.
		self.auto_max_tof = tof_range_auto_max
		self.auto_min_tof = tof_range_auto_min
		
		tof_range_manual_min = float(tof_range[0])
		tof_range_manual_max = float(tof_range[1])
		if tof_range_manual_min > 1000:
			tof_range_manual_min /= 1000.
			tof_range_manual_max /= 1000.
		self.manual_max_tof = tof_range_manual_max
		self.manual_min_tof = tof_range_manual_min
		self.manual_auto_tof_clicked(plot_refresh=False)
	
		self.ui.peak1.setValue(int(peak[0]))
		self.ui.peak2.setValue(int(peak[1]))
	
		self.ui.back1.setValue(int(back[0]))
		self.ui.back2.setValue(int(back[1]))

		self.activate_or_not_back_widgets(back_flag, plot_refresh=False)
				
	def activate_or_not_back_widgets(self, back_flag, plot_refresh=True):
		self.ui.back_flag.setChecked(back_flag)
		self.ui.back1.setEnabled(back_flag)
		self.ui.back2.setEnabled(back_flag)
		self.check_peak_back_input_validity()
		if plot_refresh:
			self.update_plots()
			
	def sort_peak_back_input(self):		
		peak1 = self.ui.peak1.value()
		peak2 = self.ui.peak2.value()		
		peak_min = min([peak1, peak2])
		peak_max = max([peak1, peak2])
		if peak_min != peak1:
			self.ui.peak1.setValue(peak2)
			self.ui.peak2.setValue(peak1)
			
		back1 = self.ui.back1.value()
		back2 = self.ui.back2.value()		
		back_min = min([back1, back2])
		back_max = max([back1, back2])
		if back_min != back1:
			self.ui.back1.setValue(back2)
			self.ui.back2.setValue(back1)

	def update_plots(self):
		self.update_pixel_vs_tof_tab_plot()
		self.update_detector_tab_plot()

	def manual_input_peak1(self):
		self.sort_and_check_widgets()
		self.update_plots()
					
	def manual_input_peak2(self):
		self.sort_and_check_widgets()
		self.update_plots()
			
	def manual_input_back1(self):
		self.sort_and_check_widgets()
		self.update_plots()
			
	def manual_input_back2(self):
		self.sort_and_check_widgets()
		self.update_plots()
			
	def sort_and_check_widgets(self):
		self.sort_peak_back_input()
		self.check_peak_back_input_validity()

	def check_peak_back_input_validity(self):
		peak1 = self.ui.peak1.value()
		peak2 = self.ui.peak2.value()
		back1 = self.ui.back1.value()
		back2 = self.ui.back2.value()
		
		_show_widgets_1 = False
		_show_widgets_2 = False
		
		if self.ui.back_flag.isChecked():
			if back1 > peak1:
				_show_widgets_1 = True
			if back2 < peak2:
				_show_widgets_2 = True
				
		self.ui.back1_label.setVisible(_show_widgets_1)
		self.ui.peak1_label.setVisible(_show_widgets_1)
		
		self.ui.back2_label.setVisible(_show_widgets_2)
		self.ui.peak2_label.setVisible(_show_widgets_2)
		
		self.ui.error_label.setVisible(_show_widgets_1 or _show_widgets_2)
					
	def manual_input_of_low_res_field(self):
		value1 = self.ui.low_res1.value()
		value2 = self.ui.low_res2.value()
		value_min = min([value1,value2])
		value_max = max([value1,value2])
		self.ui.detector_plot()
	
	def manual_input_of_tof_field(self):
		tof1 = float(self.ui.tof_from.text())
		tof2 = float(self.ui.tof_to.text())
		tof_min = min([tof1, tof2])
		tof_max = max([tof1, tof2])
		str_tof_min = ("%.2f"%tof_min)
		str_tof_max = ("%.2f"%tof_max)
		self.ui.tof_from.setText(str_tof_min)
		self.ui.tof_to.setText(str_tof_max)
		self.manual_min_tof = tof_min
		self.manual_max_tof = tof_max
		self.update_pixel_vs_tof_tab_plot()
	
	def manual_auto_tof_clicked(self, plot_refresh=True):
		isManualChecked = self.ui.tof_manual_flag.isChecked()
		self.activate_tof_widgets(isManualChecked)
		if isManualChecked:
			_from_value = "%.2f"%self.manual_min_tof
			_to_value = "%.2f"%self.manual_max_tof
		else:
			_from_value = "%.2f"%self.auto_min_tof
			_to_value = "%.2f"%self.auto_max_tof
		self.ui.tof_from.setText(_from_value)
		self.ui.tof_to.setText(_to_value)
		if plot_refresh:
			self.update_pixel_vs_tof_tab_plot()
		
	def activate_tof_widgets(self, status):
		self.ui.tof_from.setEnabled(status)
		self.ui.tof_to.setEnabled(status)
		self.ui.tof_from_label.setEnabled(status)
		self.ui.tof_to_label.setEnabled(status)
		self.ui.tof_from_units.setEnabled(status)
		self.ui.tof_to_units.setEnabled(status)
#		self.update_pixel_vs_tof_tab_plot()

	def closeEvent(self, event=None):
		[tof1, tof2, peak1, peak2, back1, back2, backFlag]= self.retrieveTofPeakBack()
		self.main_gui.ui.dataPeakFromValue.setValue(peak1)
		self.main_gui.ui.dataPeakToValue.setValue(peak2)
		self.main_gui.ui.dataBackFromValue.setValue(back1)
		self.main_gui.ui.dataBackToValue.setValue(back2)
		self.main_gui.ui.dataBackgroundFlag.setChecked(backFlag)
		QApplication.processEvents()
                self.main_gui.peakBackSpinBoxValueChanged(['peak','back'], with_plot_update=False)
		self.main_gui.testPeakBackErrorWidgets()
		self.main_gui.ui.dataBackFromLabel.setEnabled(backFlag)
		self.main_gui.ui.dataBackFromValue.setEnabled(backFlag)
		self.main_gui.ui.dataBackToLabel.setEnabled(backFlag)
		self.main_gui.ui.dataBackToValue.setEnabled(backFlag)
		
		tof_auto_switch = self.ui.tof_auto_flag.isChecked()
		self.main_gui.tofValidation(tof_auto_switch, tof1, tof2, with_plot_update=False)
			
		self.main_gui.displayPlot()
		
	def activate_or_not_low_res_widgets(self, low_res_flag):
		pass
	
	def manual_input_of_low_res_field(self):
		pass

	