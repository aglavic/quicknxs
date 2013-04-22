#-*- coding: utf-8 -*-
'''
  Helper dialogs for the GUI. ReduceDialog is used to export the extracted
  data to user defined formats.
'''

import os, sys
from tempfile import gettempdir
from zipfile import ZipFile, ZIP_DEFLATED
from cStringIO import StringIO
from time import sleep, time
from numpy import hstack, array, where, histogram2d, log10, meshgrid, sqrt
from logging import warning, debug, info

import smtplib
from email import encoders
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
from email.mime.base import MIMEBase

from PyQt4.QtGui import QDialog, QMessageBox, QFileDialog, QVBoxLayout, QLabel, QProgressBar, \
                        QApplication, QSizePolicy, QListWidgetItem
from PyQt4.QtCore import QThread, pyqtSignal

from matplotlib.lines import Line2D
from matplotlib.patches import Ellipse

from .config import PATHS, EMAIL, EXPORT
from .mplwidget import MPLWidget
from .plot_dialog import Ui_Dialog as UiPlot
from .reduce_dialog import Ui_Dialog as UiReduction
from .gisans_dialog import Ui_Dialog as UiGisans
from .smooth_dialog import Ui_Dialog as UiSmooth
from .mreduce import GISANS
from .mrio import Exporter
from .decorators import log_call, log_output
from .output_templates import *
from . import genx_data
# make sure importing and changing genx templates do only use our
# build in dummy module
sys.modules['genx.data']=genx_data
genx_data.DataList.__module__='genx.data'
genx_data.DataSet.__module__='genx.data'

class ReduceDialog(QDialog):
  CHANNEL_NAMINGS=['UpUp', 'DownDown', 'UpDown', 'DownUp']
  CHANNEL_COMPARE=[
                   ['x', '+', '++', '0V'],
                   ['-', '--', '+V'],
                   ['+-', '-V'],
                   ['-+']
                   ]
  _overwrite_all=False

  def __init__(self, parent, channels, refls):
    QDialog.__init__(self, parent)
    self.cmap=parent.color
    self.ui=UiReduction()
    self.ui.setupUi(self)
    self.channels=list(channels) # make sure we don't alter the original list
    self.refls=refls
    if not os.path.exists(PATHS['results']):
      self.ui.directoryEntry.setText(os.path.dirname(refls[0].origin[0]))
    else:
      self.ui.directoryEntry.setText(PATHS['results'])
    self.ui.fileNameEntry.setText(PATHS['export_name'])
    self.set_email_texts()
    for i in range(4):
      if not any(map(lambda item: item in self.CHANNEL_COMPARE[i], channels)):
        checkbutton=getattr(self.ui, 'export'+self.CHANNEL_NAMINGS[i])
        checkbutton.setEnabled(False)
        checkbutton.setChecked(False)
    for key, value in EXPORT.items():
      option=getattr(self.ui, key)
      if hasattr(option, 'setChecked'):
        option.setChecked(value)
      else:
        option.setText(value)
    self.tempfiles=[]

  @log_call
  def exec_(self):
    '''
      Run the dialog and perform reflectivity extraction.
    '''
    if QDialog.exec_(self):
      self.exported_files_all=[]
      self.exported_files_plots=[]
      self.exported_files_data=[]
      foldername=unicode(self.ui.directoryEntry.text())
      if not os.path.exists(foldername):
        result=QMessageBox.question(self, 'Creat Folder?',
                      'The folder "%s" does not exist. Do you want to create it?'%foldername,
                      buttons=QMessageBox.Yes|QMessageBox.No)
        if result==QMessageBox.Yes:
          os.makedirs(foldername)
        else:
          return
      self.save_settings()
      # remove channels not selected
      if not self.ui.exportDownUp.isChecked():
        self.rm_channel(['-+'])
      if not self.ui.exportUpDown.isChecked():
        self.rm_channel(['+-', '-V'])
      if not self.ui.exportDownDown.isChecked():
        self.rm_channel(['-', '--', '+V'])
      if not self.ui.exportUpUp.isChecked():
        self.rm_channel(['x', '+', '++', '0V'])
      # calculate and collect reflectivities
      self.exporter=Exporter(self.channels, self.refls)
      info('Re-reading all datasets...')
      self.exporter.read_data()

      if self.ui.exportSpecular.isChecked():
        info('Extracting reflectivity...')
        self.exporter.extract_reflectivity()
      if self.ui.exportOffSpecular.isChecked() or self.ui.exportOffSpecularSmoothed.isChecked():
        info('Extracting off-specular data...')
        self.exporter.extract_offspecular()
      if self.ui.exportOffSpecularCorr.isChecked():
        info('Extracting corrected off-specular data...')
        self.exporter.extract_offspecular_corr()
      if self.ui.exportOffSpecularSmoothed.isChecked():
        self.smooth_offspec()
        if not self.ui.exportOffSpecular.isChecked():
          del(self.exporter.output_data['OffSpec'])
      if self.ui.exportGISANS.isChecked():
        self.extract_gisans()

      directory=unicode(self.ui.directoryEntry.text())
      naming=unicode(self.ui.fileNameEntry.text())
      self.exporter.export_data(
                                directory, naming,
                                multi_ascii=self.ui.multiAscii.isChecked(),
                                combined_ascii=self.ui.combinedAscii.isChecked(),
                                matlab_data=self.ui.matlab.isChecked(),
                                numpy_data=self.ui.numpy.isChecked(),
                                check_exists=self.check_exists,
                                )
      if self.ui.gnuplot.isChecked():
        info('Creating gnuplot scripts...')
        self.exporter.create_gnuplot_scripts(directory, naming)
      if self.ui.genx.isChecked():
        info('Creating genx file...')
        self.exporter.create_genx_file(directory, naming)
      if self.ui.plot.isChecked():
        info('Plotting...')
        for title, output_data in self.exporter.output_data.items():
          self.plot_result(output_data, title)

      if self.ui.emailSend.isChecked():
        self.send_email()
      for tmp in self.tempfiles:
        os.remove(tmp)
      return True
      info('Finished')
    else:
      return False

  @log_call
  def extract_gisans(self):
    '''
      Extract the GISANS data for all datasets.
    '''
    output_data=dict([(channel, []) for channel in self.channels])
    for refli in self.refls:
      opts=refli.options
      index=opts['number']
      fdata=self.exporter.raw_data[index]
      for channel in self.channels:
        gisans=GISANS(fdata[channel], **opts)
        output_data[channel].append(gisans)
    dia=GISANSDialog(self, output_data[self.channels[0]])
    result=dia.exec_()
    lmin=dia.ui.lambdaMin.value()
    lmax=dia.ui.lambdaMax.value()
    gridQy=dia.ui.gridQy.value()
    gridQz=dia.ui.gridQz.value()
    nslices=dia.ui.numberSlices.value()
    dia.destroy()
    app=QApplication.instance()
    if result==QDialog.Accepted:
      for channel in self.channels:
        thread=GISANSCalculation(output_data[channel], lmin, lmax, nslices, gridQy, gridQz)
        thread.start()
        while not thread.isFinished():
          app.processEvents()
        output_data[channel]=[]
        for item in thread.results:
          output_data[channel].append(array([item[1], item[2], item[0], item[5]]).transpose(1, 2, 0))
      for i in range(nslices):
        output=dict([(channel, [output_data[channel][i]]) for channel in self.channels])
        output['column_units']=['A^-1', 'A^-1', 'a.u.', 'a.u.']
        output['column_names']=['Qy', 'Qz', 'I', 'dI']
        self.exporter.output_data['GISANS_%i'%i]=output

  @log_call
  def smooth_offspec(self):
    data=self.exporter.output_data['OffSpec'][self.channels[0]]
    dia=SmoothDialog(self.parent(), data)
    if not dia.exec_():
      dia.destroy()
      return
    settings=dia.getOptions()
    dia.destroy()
    pbinfo="Smoothing Channel "
    pb=ProgressDialog(self.parent(), title="Smoothing",
                      info_start=pbinfo+self.channels[0],
                      maximum=100*len(self.channels))
    pb.show()
    self.exporter.smooth_offspec(settings, pb)
    pb.destroy()

  @log_call
  def check_exists(self, filename):
    '''
      If the filename exists, prompt the user if it should be overwritten.
      :return: If the file should be written or not.
    '''
    if self._overwrite_all or not os.path.exists(filename):
      return True
    result=QMessageBox.question(self, 'Overwrite file?',
                                'The file "%s" already exists, overwrite it?'%filename,
                                buttons=QMessageBox.Yes|QMessageBox.YesToAll|QMessageBox.No)
    if result==QMessageBox.YesToAll:
      self._overwrite_all=True
      return True
    elif result==QMessageBox.Yes:
      return True
    else:
      return False

  @log_call
  def plot_result(self, output_data, title):
    ind_str=self.exporter.ind_str
    if type(output_data[self.channels[0]]) is not list:
      # plot the results in a new window
      dialog=PlotDialog()
      plot=dialog.plot
      plot.toolbar.coordinates=True
      for channel in self.channels:
        data=output_data[channel]
        plot.errorbar(data[:, 0], data[:, 1], yerr=data[:, 2], label=channel)
      plot.legend()
      plot.set_xlabel(u'Q$_z$ [Å$^{-1}$]')
      plot.set_ylabel(u'R [a.u.]')
      plot.set_yscale('log')
      plot.set_title(ind_str+' - '+title)
      plot.draw()
      dialog.show()
      self.parent().open_plots.append(dialog)
      if self.ui.emailSend.isChecked() and not self.ui.gnuplot.isChecked():
        self._save_plot(plot)
    else:
      if title in ['OffSpec', 'OffSpecCorr']:
        x, y, z=4, 1, 5
        xl=u'k$_{i,z}$-k$_{f,z}$ [Å$^{-1}$]'
        yl=u'Q$_z$ [Å$^{-1}$]'
      else:
        x, y, z=0, 1, 2
        xl=u'%s [Å$^{-1}$]'%output_data['column_names'][0]
        yl=u'%s [Å$^{-1}$]'%output_data['column_names'][1]
      dialogs=[]
      for channel in self.channels:
        # plot the results in a new window
        dialog=PlotDialog()
        dialog._open_instances=dialogs
        dialog.show()
        dialog.resize(450, 450)
        dialog.move(100+450*(len(dialogs)%2),
                    50+450*(len(dialogs)//2))
        dialogs.append(dialog)
        plot=dialog.plot
        plot.toolbar.coordinates=True
        Imin=1.
        Imax=1e-6
        cmap=self.cmap
        for data in output_data[channel]:
          Imin=min(Imin, data[:, :, z][data[:, :, z]>0].min())
          Imax=max(Imax, data[:, :, z].max())

          plot.pcolormesh(data[:, :, x], data[:, :, y], data[:, :, z], log=True,
                             imin=data[:, :, z][data[:, :, z]>0].min(), imax=None,
                             label=channel, cmap=cmap)
        for item in plot.canvas.ax.collections:
          item.set_clim(Imin*0.8, Imax)
        dialog.showMinMax(Imin*0.8, Imax)
        plot.canvas.fig.colorbar(plot.cplot)
        plot.set_xlabel(xl)
        plot.set_ylabel(yl)
        plot.set_title(ind_str+' - '+title+' - (%s)'%channel)
        plot.draw()
        dialog.show()
        self.parent().open_plots.append(dialog)
        if self.ui.emailSend.isChecked() and not self.ui.gnuplot.isChecked():
          self._save_plot(plot)

  @log_call
  def _save_plot(self, plot):
    fname=os.path.join(gettempdir(), 'plot_%i.png'%len(self.tempfiles))
    try:
      plot.canvas.print_figure(fname)
    except:
      pass
    else:
      self.exported_files_plots.append(fname)
      self.tempfiles.append(fname)

  def rm_channel(self, names):
    for name in names:
      if name in self.channels:
        self.channels.remove(name)
        return

  @log_call
  def changeDir(self):
    oldd=self.ui.directoryEntry.text()
    newd=QFileDialog.getExistingDirectory(parent=self, caption=u'Select new folder',
                                          directory=oldd)
    if newd is not None:
      self.ui.directoryEntry.setText(newd)

  @log_call
  def set_email_texts(self):
    for name, value in EMAIL.items():
      entry=getattr(self.ui, 'email'+name)
      if entry.__class__.__name__=='QPlainTextEdit':
        entry.setPlainText(value)
      elif entry.__class__.__name__=='QLineEdit':
        entry.setText(value)
      else:
        entry.setChecked(value)

  def save_settings(self):
    PATHS['results']=unicode(self.ui.directoryEntry.text())
    PATHS['export_name']=unicode(self.ui.fileNameEntry.text())
    for key in EXPORT.keys():
      option=getattr(self.ui, key)
      if hasattr(option, 'setChecked'):
        EXPORT[key]=option.isChecked()
      else:
        EXPORT[key]=unicode(option.text())
    self.save_email_texts()

  @log_call
  def save_email_texts(self):
    for name, value in EMAIL.items():
      entry=getattr(self.ui, 'email'+name)
      if entry.__class__.__name__=='QPlainTextEdit':
        value=entry.toPlainText()
      elif entry.__class__.__name__=='QLineEdit':
        value=entry.text()
      else:
        value=entry.isChecked()
      EMAIL[name]=value

  def _email_replace(self, text):
    return text.replace('{ipts}', self.exporter.ipts_str).replace('{numbers}',
                                                                  self.exporter.ind_str)

  @log_call
  def send_email(self):
    '''
    Collect all files and send them to the user via smtp mail.
    '''
    msg=MIMEMultipart()
    msg['Subject']=self._email_replace(EMAIL['Subject'])
    msg['From']='BL4A@ornl.gov'
    msg['To']=EMAIL['To'].replace(';', ', ')
    msg['CC']=EMAIL['CC'].replace(';', ', ')
    text=self._email_replace(EMAIL['Text'])
    msg.preamble=text
    msg.attach(MIMEText(text))

    if EMAIL['Data']:
      exported_files=self.exporter.exported_files_data
    elif EMAIL['Plots']:
      exported_files=self.exporter.exported_files_plots
    else:
      exported_files=self.exporter.exported_files_all
    if EMAIL['ZIP']:
      # create an in-memory zip file which gets attached to the mail
      fobj=StringIO()
      zipfile=ZipFile(fobj, 'w', ZIP_DEFLATED)
      for item in exported_files:
        zipfile.write(item, arcname=os.path.basename(item))
      zipfile.close()
      fobj.seek(0)
      mitem=MIMEBase('application', 'zip')
      mitem.set_payload(fobj.read())
      encoders.encode_base64(mitem)
      mitem.add_header('Content-Disposition', 'attachment',
                       filename=self._email_replace('results_{numbers}.zip'))
      msg.attach(mitem)
    else:
      # read each file, which was exported and attach it to the mail
      for item in exported_files:
        try:
          if item.endswith('.png'):
            mitem=MIMEImage(open(item, 'rb').read(), 'png')
          elif item.endswith('.pdf'):
            mitem=MIMEText(open(item, 'rb').read(), 'pdf')
          elif item.endswith('.dat') or item.endswith('.gp'):
            mitem=MIMEText(open(item, 'rb').read())
          else:
            mitem=MIMEBase('application', item[-3:])
            mitem.set_payload(open(item, 'rb').read())
            encoders.encode_base64(mitem)
        except:
          continue
        mitem.add_header('Content-Disposition', 'attachment', filename=os.path.basename(item))
        msg.attach(mitem)

    try:
      debug('Trying to send data via smtp.ornl.gov')
      smtp=smtplib.SMTP('160.91.4.26', timeout=10)
      smtp.sendmail(msg['From'],
                    map(unicode.strip, msg['To'].split(',')+msg['CC'].split(',')),
                    msg.as_string())
      smtp.quit()
    except:
      warning("Could not send email, perhaps you're not in the ORNL network.", exc_info=True)
    else:
      debug('Email sent successfully')


class PlotDialog(QDialog):
  '''
  Dialog to show a single plot.
  '''
  _open_instances=[]

  def __init__(self, parent=None):
    QDialog.__init__(self, parent=parent)
    self._open_instances.append(self)
    self.ui=UiPlot()
    self.ui.setupUi(self)
    self.hideMinMax()
    self.plot=self.ui.plot

  def showMinMax(self, Imin=1e-6, Imax=1.):
    self.ui.Imin.setValue(log10(Imin))
    self.ui.Imax.setValue(log10(Imax))
    self.ui.Imin.show()
    self.ui.Imax.show()
    self.ui.ImaxLabel.show()
    self.ui.IminLabel.show()
    self.ui.clipButton.show()
    self.ui.applyButton.show()

  def hideMinMax(self):
    self.ui.Imin.hide()
    self.ui.Imax.hide()
    self.ui.ImaxLabel.hide()
    self.ui.IminLabel.hide()
    self.ui.clipButton.hide()
    self.ui.applyButton.hide()

  def redrawColorscale(self):
    plot=self.plot
    Imin=10**self.ui.Imin.value()
    Imax=10**self.ui.Imax.value()
    if plot.cplot is not None and Imin<Imax:
      for item in plot.canvas.ax.images:
        item.set_clim(Imin, Imax)
      for item in plot.canvas.ax.collections:
        item.set_clim(Imin, Imax)
      plot.draw()

  def clipData(self):
    plot=self.plot
    Imin=1e10
    if plot.cplot is not None:
      for item in plot.canvas.ax.images:
        I=item.get_array()
        Imin=min(Imin, I[I>0].min())
      for item in plot.canvas.ax.collections:
        I=item.get_array()
        Imin=min(Imin, I[I>0].min())
      for item in plot.canvas.ax.images:
        I=item.get_array()
        I[I<=0]=Imin
        item.set_array(I)
      for item in plot.canvas.ax.collections:
        I=item.get_array()
        I[I<=0]=Imin
        item.set_array(I)
      plot.draw()

  def applyScaling(self):
    if self.plot.cplot is None:
      return
    xlim=self.plot.canvas.ax.get_xlim()
    ylim=self.plot.canvas.ax.get_ylim()
    Imin=self.ui.Imin.value()
    Imax=self.ui.Imax.value()
    for dialog in self._open_instances:
      if dialog.plot.cplot is None or dialog is self:
        continue
      dialog.plot.canvas.ax.set_xlim(*xlim)
      dialog.plot.canvas.ax.set_ylim(*ylim)
      dialog.ui.Imin.setValue(Imin)
      dialog.ui.Imax.setValue(Imax)
      for item in dialog.plot.canvas.ax.images:
        item.set_clim(10**Imin, 10**Imax)
      for item in dialog.plot.canvas.ax.collections:
        item.set_clim(10**Imin, 10**Imax)
      dialog.plot.draw()

  def closeEvent(self, event):
    self._open_instances.remove(self)
    return QDialog.closeEvent(self, event)

class SmoothDialog(QDialog):
  '''
    Dialog to define smoothing parameters.
  '''
  drawing=False

  def __init__(self, parent, data):
    QDialog.__init__(self, parent)
    self.ui=UiSmooth()
    self.ui.setupUi(self)
    self.data=data
    self.ui.plot.canvas.mpl_connect('motion_notify_event', self.plotSelect)
    self.ui.plot.canvas.mpl_connect('button_press_event', self.plotSelect)
    self.drawPlot()

  def drawPlot(self):
    '''
      Plot the unsmoothed data.
    '''
    self.drawing=True
    data=self.data
    plot=self.ui.plot
    plot.clear()
    Qzmax=0.001
    for item in data:
      Qx=item[:, :, 0]
      Qz=item[:, :, 1]
      ki_z=item[:, :, 2]
      kf_z=item[:, :, 3]
      I=item[:, :, 5]

      Qzmax=max(ki_z.max()*2., Qzmax)
      if self.ui.kizmkfzVSqz.isChecked():
        plot.pcolormesh((ki_z-kf_z), Qz, I, log=True,
                        imin=1e-6, imax=1., shading='gouraud')
      elif self.ui.qxVSqz.isChecked():
        plot.pcolormesh(Qx, Qz, I, log=True,
                        imin=1e-6, imax=1., shading='gouraud')
      else:
        plot.pcolormesh(ki_z, kf_z, I, log=True,
                        imin=1e-6, imax=1., shading='gouraud')
    if self.ui.kizmkfzVSqz.isChecked():
      plot.canvas.ax.set_xlim([-0.035, 0.035])
      plot.canvas.ax.set_ylim([0., Qzmax*1.01])
      plot.set_xlabel(u'k$_{i,z}$-k$_{f,z}$ [Å$^{-1}$]')
      plot.set_ylabel(u'Q$_z$ [Å$^{-1}$]')
      x1=-0.03
      x2=0.03
      y1=0.
      y2=Qzmax
      sigma_pos=(0., Qzmax/3.)
      sigma_ang=0.
      self.ui.sigmasCoupled.setChecked(True)
      self.ui.sigmaY.setEnabled(False)
      self.ui.sigmaX.setValue(0.0005)
      self.ui.sigmaY.setValue(0.0005)
    elif self.ui.qxVSqz.isChecked():
      plot.canvas.ax.set_xlim([-0.0005, 0.0005])
      plot.canvas.ax.set_ylim([0., Qzmax*1.01])
      plot.set_xlabel(u'Q$_x$ [Å$^{-1}$]')
      plot.set_ylabel(u'Q$_z$ [Å$^{-1}$]')
      x1=-0.0002
      x2=0.0002
      y1=0.
      y2=Qzmax
      sigma_pos=(0., Qzmax/3.)
      sigma_ang=0.
      self.ui.sigmasCoupled.setChecked(False)
      self.ui.sigmaY.setEnabled(True)
      self.ui.sigmaX.setValue(0.00001)
      self.ui.sigmaY.setValue(0.0005)
    else:
      plot.canvas.ax.set_xlim([0., Qzmax/2.*1.01])
      plot.canvas.ax.set_ylim([0., Qzmax/2.*1.01])
      plot.set_xlabel(u'k$_{i,z}$ [Å$^{-1}$]')
      plot.set_ylabel(u'k$_{f,z}$ [Å$^{-1}$]')
      x1=0.0
      x2=Qzmax/2.
      y1=0.
      y2=Qzmax/2.
      sigma_pos=(Qzmax/6., Qzmax/6.)
      sigma_ang=0.#-45.
      self.ui.sigmasCoupled.setChecked(True)
      self.ui.sigmaX.setValue(0.0005)
      self.ui.sigmaY.setValue(0.0005)
    if plot.cplot is not None:
      plot.cplot.set_clim([1e-6, 1.])
    self.rect_region=Line2D([x1, x1, x2, x2, x1], [y1, y2, y2, y1, y1])
    self.sigma_1=Ellipse(sigma_pos, self.ui.sigmaX.value()*2, self.ui.sigmaY.value()*2,
                            sigma_ang, fill=False)
    self.sigma_2=Ellipse(sigma_pos, self.ui.sigmaX.value()*4, self.ui.sigmaY.value()*4,
                            sigma_ang, fill=False)
    self.sigma_3=Ellipse(sigma_pos, self.ui.sigmaX.value()*6, self.ui.sigmaY.value()*6,
                            sigma_ang, fill=False)
    plot.canvas.ax.add_line(self.rect_region)
    plot.canvas.ax.add_artist(self.sigma_1)
    plot.canvas.ax.add_artist(self.sigma_2)
    plot.canvas.ax.add_artist(self.sigma_3)
    plot.draw()
    # set parameter values
    self.ui.gridXmin.setValue(x1)
    self.ui.gridXmax.setValue(x2)
    self.ui.gridYmin.setValue(y1)
    self.ui.gridYmax.setValue(y2)
    self.updateGrid()
    self.drawing=False

  def updateSettings(self):
    if self.drawing:
      return
    self.drawing=True
    if self.ui.sigmasCoupled.isChecked():
      self.ui.sigmaY.setValue(self.ui.sigmaX.value())
    self.updateGrid()
    # redraw indicators
    x1=self.ui.gridXmin.value()
    x2=self.ui.gridXmax.value()
    y1=self.ui.gridYmin.value()
    y2=self.ui.gridYmax.value()
    self.rect_region.set_data([x1, x1, x2, x2, x1], [y1, y2, y2, y1, y1])
    self.sigma_1.width=2*self.ui.sigmaX.value()
    self.sigma_1.height=2*self.ui.sigmaY.value()
    self.sigma_2.width=4*self.ui.sigmaX.value()
    self.sigma_2.height=4*self.ui.sigmaY.value()
    self.sigma_3.width=6*self.ui.sigmaX.value()
    self.sigma_3.height=6*self.ui.sigmaY.value()
    self.ui.plot.draw()
    self.drawing=False

  def updateGrid(self):
    if self.ui.gridSizeCoupled.isChecked():
      sx=self.ui.sigmaX.value()
      sy=self.ui.sigmaY.value()
      x1=self.ui.gridXmin.value()
      x2=self.ui.gridXmax.value()
      y1=self.ui.gridYmin.value()
      y2=self.ui.gridYmax.value()
      self.ui.gridSizeX.setValue(int((x2-x1)/sx*1.41))
      self.ui.gridSizeY.setValue(int((y2-y1)/sy*1.41))

  def plotSelect(self, event):
    '''
      Plot for y-projection has been clicked.
    '''
    if event.button==1 and self.ui.plot.toolbar._active is None and \
        event.xdata is not None:
      x=event.xdata
      y=event.ydata
      x1=self.ui.gridXmin.value()
      x2=self.ui.gridXmax.value()
      y1=self.ui.gridYmin.value()
      y2=self.ui.gridYmax.value()
      if x<x1 or abs(x-x1)<abs(x-x2):
        x1=x
      else:
        x2=x
      if y<y1 or abs(y-y1)<abs(y-y2):
        y1=y
      else:
        y2=y
      self.drawing=True
      self.ui.gridXmin.setValue(x1)
      self.ui.gridXmax.setValue(x2)
      self.ui.gridYmin.setValue(y1)
      self.ui.gridYmax.setValue(y2)
      self.drawing=False
      self.updateSettings()

  @log_output
  def getOptions(self):
    output={}
    x1=self.ui.gridXmin.value()
    x2=self.ui.gridXmax.value()
    y1=self.ui.gridYmin.value()
    y2=self.ui.gridYmax.value()
    output['region']=[x1, x2, y1, y2]
    width=self.ui.sigmaX.value()
    height=self.ui.sigmaY.value()
    output['sigma']=(width, height)
    output['sigmas']=self.ui.rSigmas.value()
    gx=self.ui.gridSizeX.value()
    gy=self.ui.gridSizeY.value()
    output['grid']=(gx, gy)
    output['xy_column']=1*self.ui.qxVSqz.isChecked()+2*self.ui.kizVSkfz.isChecked()
    return output

class GISANSCalculation(QThread):
  '''
    Perform gisans projection calculation in the background and
    send a signal aver each subframe has been finished.
  '''
  frameFinished=pyqtSignal(int)

  def __init__(self, datasets, lmin, lmax, lsteps, gridQy=50, gridQz=50):
    QThread.__init__(self)
    self.datasets=datasets
    self.lmin=lmin
    self.lmax=lmax
    self.lsteps=lsteps
    self.grid=(gridQy+1, gridQz+1)

  def run(self):
    self.results=[]
    for i in range(self.lsteps):
      result=self.calc_single(i)
      self.results.append(result)
      self.frameFinished.emit(i)

  def calc_single(self, i):
    lsize=(self.lmax-self.lmin)/self.lsteps
    lmin=self.lmin+i*lsize
    lmax=self.lmin+(i+1)*lsize

    data=self.datasets[0]
    P0=len(data.lamda)-data.options['P0']
    PN=data.options['PN']
    # filter the points
    region=where((data.lamda[PN:P0]>=lmin)&(data.lamda[PN:P0]<=lmax))
    I=data.S[:, :, region].flatten()
    dI=data.dS[:, :, region].flatten()
    qy=data.Qy[:, :, region].flatten()
    qz=data.Qz[:, :, region].flatten()
    for data in self.datasets[1:]:
      # add points from all datasets
      P0=len(data.lamda)-data.options['P0']
      PN=data.options['PN']
      # filter the points
      region=where((data.lamda[PN:P0]>=lmin)&(data.lamda[PN:P0]<=lmax))
      I=hstack([I, data.S[:, :, region].flatten()])
      dI=hstack([dI, data.dS[:, :, region].flatten()])
      qy=hstack([qy, data.Qy[:, :, region].flatten()])
      qz=hstack([qz, data.Qz[:, :, region].flatten()])
    Isum, ignore, ignore=histogram2d(qy, qz, bins=self.grid, weights=I)
    dIsum, ignore, ignore=histogram2d(qy, qz, bins=self.grid, weights=dI**2)
    Npoints, Qy, Qz=histogram2d(qy, qz, bins=self.grid)
    Isum[Npoints>0]/=Npoints[Npoints>0]
    dIsum=sqrt(dIsum)
    dIsum[Npoints>0]/=Npoints[Npoints>0]
    Qy=(Qy[:-1]+Qy[1:])/2.
    Qz=(Qz[:-1]+Qz[1:])/2.
    Qz, Qy=meshgrid(Qz, Qy)
    return Isum, Qy, Qz, lmin, lmax, dIsum


class GISANSDialog(QDialog):
  '''
  Dialog to define GISANS extraction parameters.
  Shows a plot of intensity vs. lambda and alows to select different
  slices to be extractes as Qy,Qz projection with a preview.
  '''
  drawing=False
  _calculator=None
  _listItems={}

  def __init__(self, parent, datasets):
    QDialog.__init__(self, parent)
    self.ui=UiGisans()
    self.ui.setupUi(self)
    self.datasets=datasets
    self.ui.splitter.setSizes([350, 250])
    self.drawLambda()
    self.ui.iMax.setValue(log10(datasets[0].S.max()*2.))
    self.ui.iMin.setValue(log10(datasets[0].S[datasets[0].I>0].min()/40.))

  @log_call
  def drawLambda(self):
    '''
    Plot intensity vs. lambda.
    '''
    self.ui.lambdaPlot.clear()
    self.ui.lambdaPlot.canvas.ax.set_xlim(1.9, 9.5)
    drawn_norms=[]
    for dataset in self.datasets:
      # draw each normalization
      norm=dataset.options['normalization']
      if norm in drawn_norms:
        continue
      drawn_norms.append(norm)
      self.ui.lambdaPlot.semilogy(norm.lamda, norm.Rraw)
    self.ui.lambdaPlot.canvas.ax.set_ylim(norm.Rraw.max()*0.01, norm.Rraw.max()*1.5)
    lmin=self.ui.lambdaMin.value()
    lmax=self.ui.lambdaMax.value()
    lsteps=(lmax-lmin)/self.ui.numberSlices.value()
    self.line_left=self.ui.lambdaPlot.canvas.ax.axvline(lmin)
    self.line_right=self.ui.lambdaPlot.canvas.ax.axvline(lmax)
    self.step_lines=[]
    for i in range(self.ui.numberSlices.value()-1):
      pos=self.ui.lambdaMin.value()+(i+1)*lsteps
      self.step_lines.append(self.ui.lambdaPlot.canvas.ax.axvline(pos, color='red'))

    self.ui.lambdaPlot.set_xlabel(u'$\\lambda{}$ [Å]')
    self.ui.lambdaPlot.set_ylabel(u'I($\\lambda{}$)')
    self.ui.lambdaPlot.canvas.fig.subplots_adjust(left=0.15, bottom=0.18, right=0.99, top=0.99)
    self.ui.lambdaPlot.draw()

  @log_call
  def lambdaRangeChanged(self):
    '''
    Change the vertical lines on the lambda plot.
    '''
    lmin=self.ui.lambdaMin.value()
    lmax=self.ui.lambdaMax.value()
    self.line_left.set_xdata([lmin, lmin])
    self.line_right.set_xdata([lmax, lmax])
    lsteps=(lmax-lmin)/self.ui.numberSlices.value()
    for i, line in enumerate(self.step_lines):
      line.set_xdata(lmin+(i+1)*lsteps)
    self.ui.lambdaPlot.draw()

  @log_call
  def numberSlicesChanged(self):
    '''
    Change the number of lines drawn on the lambda plot.
    '''
    old_steps=len(self.step_lines)+1
    new_steps=self.ui.numberSlices.value()
    lmin=self.ui.lambdaMin.value()
    lmax=self.ui.lambdaMax.value()
    lsteps=(lmax-lmin)/self.ui.numberSlices.value()
    if old_steps>new_steps:
      for ignore in range(old_steps-new_steps):
        line=self.step_lines.pop(0)
        line.remove()
      for i, line in enumerate(self.step_lines):
        line.set_xdata(lmin+(i+1)*lsteps)
    elif new_steps>old_steps:
      i=-1
      for i, line in enumerate(self.step_lines):
        line.set_xdata(lmin+(i+1)*lsteps)
      for j in range(new_steps-old_steps):
        self.step_lines.append(self.ui.lambdaPlot.canvas.ax.axvline(lmin+(i+j+2)*lsteps,
                                                                    color='red'))
    self.ui.lambdaPlot.draw()

  @log_call
  def createProjectionPlots(self):
    '''
    Start a thread that calculates porjections to be plotted.
    '''
    for child in self.ui.resultImageArea.children():
      if not type(child) is MPLWidget:
        continue
      child.setParent(None)
    self._listItems={}
    self.ui.plotShowList.clear()
    self.projection_plots=[]
    self._calculator=GISANSCalculation(self.datasets, self.ui.lambdaMin.value(),
                                       self.ui.lambdaMax.value(), self.ui.numberSlices.value(),
                                       self.ui.gridQy.value(), self.ui.gridQz.value())
    self._calculator.frameFinished.connect(self.drawProjectionPlot)
    self._calculator.start()
    self._calculator.setPriority(QThread.LowPriority)

  @log_call
  def drawProjectionPlot(self, i):
    '''
    Plot one projection.
    '''
    result=self._calculator.results[i]
    r0=self._calculator.results[0]
    policy=QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
    plot=MPLWidget(self.ui.resultImageArea, False)
    self.ui.resultImageLayout.addWidget(plot, 0)
    plot.setSizePolicy(policy)
    plot.canvas.fig.subplots_adjust(left=0.18, bottom=0.12, right=0.99, top=0.92)
    plot.imshow(result[0][:, ::-1].transpose(), aspect='auto',
                extent=[result[1].min(), result[1].max(), result[2].min(), result[2].max()],
                cmap='default', log=True,
                imin=10**(self.ui.iMin.value()), imax=10**(self.ui.iMax.value()))
    plot.canvas.ax.set_xlim(r0[1].min(), r0[1].max())
    plot.canvas.ax.set_ylim(r0[2].min(), r0[2].max())
    plot.set_xlabel(u'Q$_y$ [Å$^{-1}$]')
    plot.set_ylabel(u'Q$_z$ [Å$^{-1}$]')
    title=u'$\\lambda{}$=%.2f-%.2fÅ'%(result[3], result[4])
    list_title=u'λ=%.2f-%.2fÅ'%(result[3], result[4])
    plot.set_title(title)
    plot.draw()
    item=QListWidgetItem(list_title)
    self.ui.plotShowList.addItem(item)
    self.ui.plotShowList.setItemSelected(item, True)
    self._listItems[item]=plot

  @log_call
  def changePlotSelection(self):
    selection=self.ui.plotShowList.selectedItems()
    for item, plot in self._listItems.items():
      if item in selection:
        plot.show()
      else:
        plot.hide()

  @log_call
  def changePlotScale(self):
    from matplotlib.colors import LogNorm
    norm=LogNorm(10**(self.ui.iMin.value()), 10**(self.ui.iMax.value()))
    for plot in self._listItems.values():
      plot.cplot.set_norm(norm)
      plot.draw()

class ProgressDialog(QDialog):

  def __init__(self, parent, title='', info_start='', maximum=100, add=0):
    QDialog.__init__(self, parent)
    self.add=add
    self.setWindowTitle(title)
    vbox=QVBoxLayout()
    self.info=QLabel(self)
    vbox.addWidget(self.info)
    self.info.setText(info_start)
    self.progressBar=QProgressBar()
    self.progressBar.setMaximum(maximum)
    self.progressBar.setMinimum(0)
    vbox.addWidget(self.progressBar)
    self.setLayout(vbox)

  def progress(self, value):
    param=value*100+self.add
    self.progressBar.setValue(param)
    app=QApplication.instance()
    app.processEvents()

class DelayedTrigger(QThread):
  '''
    A loop that carries out tasks after a short delay.
    If the tasks are triggered again later, the first
    ones are ignored and the delay is reset.
    
    This allows the GUI to be more responsive when changing
    parameters for e.g. a plot that takes longer time to
    draw.
  '''
  parent=None
  stay_alive=True
  refresh=0.01
  delay=0.25
  actions={}

  activate=pyqtSignal(str, tuple)

  def __init__(self):
    QThread.__init__(self)
    self.actions={}

  def run(self):
    while self.stay_alive:
      for name, items in self.actions.items():
        ti, args=items
        if time()-ti>self.delay:
          self.activate.emit(name, args)
          del(self.actions[name])
      sleep(self.refresh)

  def __call__(self, action, *args):
    self.actions[action]=(time(), args)
