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
	
	def activate_or_not_low_res_widgets(self, low_res_flag):
		self.ui.low_res1.setEnabled(low_res_flag)
		self.ui.low_res2.setEnabled(low_res_flag)
		self.ui.low_res1_label.setEnabled(low_res_flag)
		self.ui.low_res2_label.setEnabled(low_res_flag)
		
		