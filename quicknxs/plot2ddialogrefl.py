from PyQt4.QtGui import QDialog, QPalette
from PyQt4.QtCore import Qt
from plot2d_dialog_refl import Ui_Dialog as UiPlot
from mplwidget import MPLWidget

class Plot2dDialogREFL(QDialog):
	
	main_gui = None
	_open_instances = []
	data = None
	
	def __init__(self, main_gui, data, parent=None):

		self.main_gui = main_gui
		self.data = data
		
		QDialog.__init__(self, parent=parent)
		self.setWindowModality(False)
		self._open_instances.append(self)
		self.ui = UiPlot()
		self.ui.setupUi(self)
		
		self.init_gui()
		self.populate_widgets()
		
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
		self.ui.peak1_label_2.setVisible(False)
		self.ui.peak1_label_2.setPalette(palette)
		self.ui.peak2_label_2.setVisible(False)
		self.ui.peak2_label_2.setPalette(palette)
		self.ui.back1_label_2.setVisible(False)
		self.ui.back1_label_2.setPalette(palette)
		self.ui.back2_label_2.setVisible(False)
		self.ui.back2_label_2.setPalette(palette)
		
		# peak
		self.ui.peak1.setMinimum(yrange[0])
		self.ui.peak1.setMaximum(yrange[1])
		self.ui.peak2.setMinimum(yrange[0])
		self.ui.peak2.setMaximum(yrange[1])
		self.ui.peak1_2.setMinimum(yrange[0])
		self.ui.peak1_2.setMaximum(yrange[1])
		self.ui.peak2_2.setMinimum(yrange[0])
		self.ui.peak2_2.setMaximum(yrange[1])

		# back
		self.ui.back1.setMinimum(yrange[0])
		self.ui.back1.setMaximum(yrange[1])
		self.ui.back2.setMinimum(yrange[0])
		self.ui.back2.setMaximum(yrange[1])
		self.ui.back1_2.setMinimum(yrange[0])
		self.ui.back1_2.setMaximum(yrange[1])
		self.ui.back2_2.setMinimum(yrange[0])
		self.ui.back2_2.setMaximum(yrange[1])
		
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
		low_res = _data.low_res
		low_res_flag = _data.low_res_flag
		tof_auto_flag = _data.tof_auto_flag
		tof_range_auto = _data.tof_range_auto
		tof_range = _data.tof_range
	
		self.ui.peak1.setValue(int(peak[0]))
		self.ui.peak2.setValue(int(peak[1]))
		self.ui.peak1_2.setValue(int(peak[0]))
		self.ui.peak2_2.setValue(int(peak[1]))
	
		self.ui.back1.setValue(int(back[0]))
		self.ui.back2.setValue(int(back[1]))
		self.ui.back1_2.setValue(int(back[0]))
		self.ui.back2_2.setValue(int(back[1]))
		self.activate_or_not_back_widgets(back_flag)
		
		self.ui.low_res1.setValue(int(low_res[0]))
		self.ui.low_res2.setValue(int(low_res[1]))
		self.activate_or_not_low_res_widgets(low_res_flag)
		
	def activate_or_not_back_widgets(self, back_flag):
		self.ui.back_flag.setChecked(back_flag)
		self.ui.back_2_flag.setChecked(back_flag)
		self.ui.back1.setEnabled(back_flag)
		self.ui.back2.setEnabled(back_flag)
		self.ui.back1_2.setEnabled(back_flag)
		self.ui.back2_2.setEnabled(back_flag)
		self.check_peak_back_input_validity()
	
	def activate_or_not_low_res_widgets(self, low_res_flag):
		self.ui.low_res1.setEnabled(low_res_flag)
		self.ui.low_res2.setEnabled(low_res_flag)
		self.ui.low_res1_label.setEnabled(low_res_flag)
		self.ui.low_res2_label.setEnabled(low_res_flag)
		
	def sort_peak_back_input(self):		
		peak1 = self.ui.peak1.value()
		peak2 = self.ui.peak2.value()		
		peak_min = min([peak1, peak2])
		peak_max = max([peak1, peak2])
		if peak_min != peak1:
			self.ui.peak1.setValue(peak2)
			self.ui.peak1_2.setValue(peak2)
			self.ui.peak2.setValue(peak1)
			self.ui.peak2_2.setValue(peak1)
			
		back1 = self.ui.back1.value()
		back2 = self.ui.back2.value()		
		back_min = min([back1, back2])
		back_max = max([back1, back2])
		if back_min != back1:
			self.ui.back1.setValue(back2)
			self.ui.back1_2.setValue(back2)
			self.ui.back2.setValue(back1)
			self.ui.back2_2.setValue(back1)

	def manual_input_peak1(self):
		self.ui.peak1_2.setValue(self.ui.peak1.value())
		self.sort_and_check_widgets()
			
	def manual_input_peak2(self):
		self.ui.peak2_2.setValue(self.ui.peak2.value())
		self.sort_and_check_widgets()
			
	def manual_input_peak1_2(self):
		self.ui.peak1.setValue(self.ui.peak1_2.value())
		self.sort_and_check_widgets()
			
	def manual_input_peak2_2(self):
		self.ui.peak2.setValue(self.ui.peak2_2.value())
		self.sort_and_check_widgets()

	def manual_input_back1(self):
		self.ui.back1_2.setValue(self.ui.back1.value())
		self.sort_and_check_widgets()
			
	def manual_input_back2(self):
		self.ui.back2_2.setValue(self.ui.back2.value())
		self.sort_and_check_widgets()
			
	def manual_input_back1_2(self):
		self.ui.back1.setValue(self.ui.back1_2.value())
		self.sort_and_check_widgets()
			
	def manual_input_back2_2(self):
		self.ui.back2.setValue(self.ui.back2_2.value())
		self.sort_and_check_widgets()

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
		
		if not self.ui.back_flag.isChecked():
			_show_widgets_2 = False
			_show_widgets_1 = False
		else:
			if back1 > peak1:
				_show_widgets_1 = True
			if back2 < peak2:
				_show_widgets_2 = True
				
		self.ui.back1_label.setVisible(_show_widgets_1)
		self.ui.back1_label_2.setVisible(_show_widgets_1)
		self.ui.peak1_label.setVisible(_show_widgets_1)
		self.ui.peak1_label_2.setVisible(_show_widgets_1)
		
		self.ui.back2_label.setVisible(_show_widgets_2)
		self.ui.back2_label_2.setVisible(_show_widgets_2)
		self.ui.peak2_label.setVisible(_show_widgets_2)
		self.ui.peak2_label_2.setVisible(_show_widgets_2)
		
		self.ui.error_label.setVisible(_show_widgets_1 or _show_widgets_2)
			
	def manual_input_of_peak_back_field(self):
		self.sort_peak_back_input()
		self.check_peak_back_input_validity()
		
	def manual_input_of_low_res_field(self):
		pass
	
	def manual_input_of_tof_field(self):
		pass
	
	def manual_auto_tof_clicked(self):
		status = self.ui.tof_manual_flag.isChecked()
		self.activate_tof_widgets(status)
		
	def activate_tof_widgets(self, status):
		self.ui.tof_from.setEnabled(status)
		self.ui.tof_to.setEnabled(status)
		self.ui.tof_from_label.setEnabled(status)
		self.ui.tof_to_label.setEnabled(status)
		self.ui.tof_from_units.setEnabled(status)
		self.ui.tof_to_units.setEnabled(status)

	