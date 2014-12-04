from PyQt4.QtGui import QDialog
from plot_dialog_refl import Ui_Dialog as UiPlot
from mplwidget import MPLWidget

class PlotDialogREFL(QDialog):
	
	_open_instances = []
	yaxis = None
	peak = None
	back = None
	
	def __init__(self,yaxis, peak, back, new_detector_geometry_flag, parent=None):
		self.yaxis = yaxis
		self.peak = peak
		self.back = back
		_new_detector_geometry_flag = new_detector_geometry_flag

		QDialog.__init__(self, parent=parent)
		self.setWindowModality(False)
		self._open_instances.append(self)
		self.ui = UiPlot()
		self.ui.setupUi(self)

		if not _new_detector_geometry_flag:
			self.reset_max_ui_value()
		self.init_plot()

	def reset_max_ui_value(self):
		self.ui.john_peak1.setMaximum(255)
		self.ui.john_peak2.setMaximum(255)
		self.ui.jim_peak1.setMaximum(255)
		self.ui.jim_peak2.setMaximum(255)
		self.ui.john_back1.setMaximum(255)
		self.ui.john_back2.setMaximum(255)
		self.ui.jim_back1.setMaximum(255)
		self.ui.jim_back2.setMaximum(255)

		self.ui.john_slider_peak1.setMaximum(255)
		self.ui.john_slider_peak2.setMaximum(255)
		self.ui.jim_slider_peak1.setMaximum(255)
		self.ui.jim_slider_peak2.setMaximum(255)
		self.ui.john_slider_back1.setMaximum(255)
		self.ui.john_slider_back2.setMaximum(255)
		self.ui.jim_slider_back1.setMaximum(255)
		self.ui.jim_slider_back2.setMaximum(255)

	def init_plot(self):
		xaxis = range(len(self.yaxis))
		self.xaxis = xaxis
		[peak1, peak2] = self.peak
		[back1, back2] = self.back
		
		peak1 = int(peak1)
		peak2 = int(peak2)
		back1 = int(back1)
		back2 = int(back2)
		
		# John
		ui_plot1 = self.ui.plot_pixel_vs_counts
		ui_plot1.canvas.ax.plot(self.yaxis, xaxis)
		ui_plot1.canvas.ax.set_xlabel(u'counts')
		ui_plot1.canvas.ax.set_ylabel(u'Pixels')
		ui_plot1.canvas.ax.axhline(peak1, color='#00aa00')
		ui_plot1.canvas.ax.axhline(peak2, color='#00aa00')
		ui_plot1.canvas.ax.axhline(back1, color='#aa0000')
		ui_plot1.canvas.ax.axhline(back2, color='#aa0000')

		# Jim
		ui_plot2 = self.ui.plot_counts_vs_pixel
		ui_plot2.canvas.ax.plot(xaxis, self.yaxis)
		ui_plot2.canvas.ax.set_xlabel(u'Pixels')
		ui_plot2.canvas.ax.set_ylabel(u'Counts')
		ui_plot2.canvas.ax.axvline(peak1, color='#00aa00')
		ui_plot2.canvas.ax.axvline(peak2, color='#00aa00')
		ui_plot2.canvas.ax.axvline(back1, color='#aa0000')
		ui_plot2.canvas.ax.axvline(back2, color='#aa0000')
		
		# John and Jim peak and back
		self.set_peak_value(peak1, peak2)
		self.set_back_value(back1, back2)
		
	def set_peak_value(self, peak1, peak2):
		self.ui.john_peak1.setValue(peak1)
		self.ui.jim_peak1.setValue(peak1)
		self.ui.john_slider_peak1.setValue(peak1)
		self.ui.jim_slider_peak1.setValue(peak1)

		self.ui.john_peak2.setValue(peak2)
		self.ui.jim_peak2.setValue(peak2)
		self.ui.john_slider_peak2.setValue(peak2)
		self.ui.jim_slider_peak2.setValue(peak2)
	
	def set_back_value(self, back1, back2):
		self.ui.john_back1.setValue(back1)
		self.ui.jim_back1.setValue(back1)
		self.ui.john_slider_back1.setValue(back1)
		self.ui.jim_slider_back1.setValue(back1)

		self.ui.john_back2.setValue(back2)
		self.ui.jim_back2.setValue(back2)
		self.ui.john_slider_back2.setValue(back2)
		self.ui.jim_slider_back2.setValue(back2)

	# peak1
	def update_peak1(self, value, updateJimSpinbox=True,
	                 updateJimSlider=True,
	                 updateJohnSpinbox=True,
	                 updateJohnSlider=True):
		if updateJimSpinbox:
			self.ui.jim_peak1.setValue(value)
		if updateJimSlider:
			self.ui.jim_slider_peak1.setValue(value)
		if updateJohnSpinbox:
			self.ui.john_peak1.setValue(value)
		if updateJohnSlider:
			self.ui.john_slider_peak1.setValue(value)
		
	def jim_peak1_spinbox_signal(self, value):
		self.update_peak1(value, updateJimSpinbox=False)
		self.make_sure_peak1_lt_peak2()
		
	def jim_peak1_slider_signal(self, value):
		self.update_peak1(value, updateJimSlider=False)
		self.make_sure_peak1_lt_peak2()

	def john_peak1_spinbox_signal(self, value):
		self.update_peak1(value, updateJohnSpinbox=False)
		self.make_sure_peak1_lt_peak2()
		
	def john_peak1_slider_signal(self, value):
		self.update_peak1(value, updateJohnSlider=False)
		self.make_sure_peak1_lt_peak2()

	# peak2
	def update_peak2(self, value, updateJimSpinbox=True,
	                 updateJimSlider=True,
	                 updateJohnSpinbox=True,
	                 updateJohnSlider=True):
		if updateJimSpinbox:
			self.ui.jim_peak2.setValue(value)
		if updateJimSlider:
			self.ui.jim_slider_peak2.setValue(value)
		if updateJohnSpinbox:
			self.ui.john_peak2.setValue(value)
		if updateJohnSlider:
			self.ui.john_slider_peak2.setValue(value)
		
	def jim_peak2_spinbox_signal(self, value):
		self.update_peak2(value, updateJimSpinbox=False)
		self.make_sure_peak2_gt_peak1()
		
	def jim_peak2_slider_signal(self, value):
		self.update_peak2(value, updateJimSlider=False)
		self.make_sure_peak2_gt_peak1()

	def john_peak2_spinbox_signal(self, value):
		self.update_peak2(value, updateJohnSpinbox=False)
		self.make_sure_peak2_gt_peak1()
		
	def john_peak2_slider_signal(self, value):
		self.update_peak2(value, updateJohnSlider=False)
		self.make_sure_peak2_gt_peak1()

	# back1
	def update_back1(self, value, updateJimSpinbox=True,
	                 updateJimSlider=True,
	                 updateJohnSpinbox=True,
	                 updateJohnSlider=True):
		if updateJimSpinbox:
			self.ui.jim_back1.setValue(value)
		if updateJimSlider:
			self.ui.jim_slider_back1.setValue(value)
		if updateJohnSpinbox:
			self.ui.john_back1.setValue(value)
		if updateJohnSlider:
			self.ui.john_slider_back1.setValue(value)
		
	def jim_back1_spinbox_signal(self, value):
		self.update_back1(value, updateJimSpinbox=False)
		self.make_sure_back1_lt_back2()
		
	def jim_back1_slider_signal(self, value):
		self.update_back1(value, updateJimSlider=False)
		self.make_sure_back1_lt_back2()
		
	def john_back1_spinbox_signal(self, value):
		self.update_back1(value, updateJohnSpinbox=False)
		self.make_sure_back1_lt_back2()
		
	def john_back1_slider_signal(self, value):
		self.update_back1(value, updateJohnSlider=False)
		self.make_sure_back1_lt_back2()
		
	# back2
	def update_back2(self, value, updateJimSpinbox=True,
	                 updateJimSlider=True,
	                 updateJohnSpinbox=True,
	                 updateJohnSlider=True):
		if updateJimSpinbox:
			self.ui.jim_back2.setValue(value)
		if updateJimSlider:
			self.ui.jim_slider_back2.setValue(value)
		if updateJohnSpinbox:
			self.ui.john_back2.setValue(value)
		if updateJohnSlider:
			self.ui.john_slider_back2.setValue(value)
		
	def jim_back2_spinbox_signal(self, value):
		self.update_back2(value, updateJimSpinbox=False)
		self.make_sure_back2_gt_back1()
		
	def jim_back2_slider_signal(self, value):
		self.update_back2(value, updateJimSlider=False)
		self.make_sure_back2_gt_back1()

	def john_back2_spinbox_signal(self, value):
		self.update_back2(value, updateJohnSpinbox=False)
		self.make_sure_back2_gt_back1()
				
	def john_back2_slider_signal(self, value):
		self.update_back2(value, updateJohnSlider=False)
		self.make_sure_back2_gt_back1()
		
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
		ui_plot1.canvas.ax.axhline(peak1, color='#00aa00')
		ui_plot1.canvas.ax.axhline(peak2, color='#00aa00')
		ui_plot1.canvas.ax.axhline(back1, color='#aa0000')
		ui_plot1.canvas.ax.axhline(back2, color='#aa0000')

		# Jim
		ui_plot2 = self.ui.plot_counts_vs_pixel
		ui_plot2.canvas.ax.plot(self.xaxis, self.yaxis)
		ui_plot2.canvas.ax.set_xlabel(u'Pixels')
		ui_plot2.canvas.ax.set_ylabel(u'Counts')
		ui_plot2.canvas.ax.axvline(peak1, color='#00aa00')
		ui_plot2.canvas.ax.axvline(peak2, color='#00aa00')
		ui_plot2.canvas.ax.axvline(back1, color='#aa0000')
		ui_plot2.canvas.ax.axvline(back2, color='#aa0000')
		