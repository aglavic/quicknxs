#-*- coding: utf-8 -*-
'''
  Classes to create output files from reduced datasets,
  create according file headers and reload datasets from
  such headers.
'''

import os
from time import strftime
import numpy as np
from .mreduce import NXSData, NXSMultiData, Reflectivity
from .version import str_version

class HeaderCreator(object):
  '''
    Class to create file headers from a set of Reflectivity objects.
  '''
  refls=None
  norms=None
  bgs=None
  evts=None
  sections=None
  direct_beam_options=['P0', 'PN', 'x_pos', 'x_width', 'y_pos', 'x_width',
                       'bg_pos', 'bg_width', 'dpix', 'tth', 'number']
  dataset_options=['scale', 'P0', 'PN', 'x_pos', 'x_width', 'y_pos', 'x_width',
                   'bg_pos', 'bg_width', 'extract_fan', 'dpix', 'tth', 'number']
  bg_options=['bg_tof_constant', 'bg_poly_regions', 'bg_scale_xfit']
  event_options=['bin_type', 'bins', 'event_split_bins', 'event_split_index']

  def __init__(self, refls):
    self.refls=refls
    self._collect_norms()
    self._collect_background()
    self._collect_event()
    self._collect_data()

  def _collect_norms(self):
    '''
      Create a list of unique normalization datasets needed for the reflectivity list.
    '''
    self.norms=[]
    for refli in self.refls:
      if refli.options['normalization'] not in self.norms:
        self.norms.append(refli.options['normalization'])

  def _collect_background(self):
    '''
      Create a list of unique advanced background options used in the reflectivity list.
    '''
    self.bgs=[]
    for refli in self.refls:
      default=True
      for option in self.bg_options:
        if refli.options[option]!=Reflectivity.DEFAULT_OPTIONS[option]:
          default=False
          break
      if not default:
        bg=[refli.option[option] for option in self.bg_options]
        self.bgs.append(bg)

  def _collect_event(self):
    '''
      Collect event mode readout options used to retrieve the reflectivity and normalization files.
    '''
    self.evts=[]
    for refli in self.refls:
      if type(refli.origin) is list:
        if not refli.origin[0][0].endswith('event.nxs'):
          continue
      else:
        if not refli.origin[0].endswith('event.nxs'):
          continue
      event_opts=[refli.read_options[option] for option in self.event_options]
      if not event_opts in self.evts:
        self.evts.append(event_opts)

  def _collect_data(self):
    '''
      Create actual data to be used in the output.
    '''
    self.sections=[]
    # direct beam measurements
    options=self.direct_beam_options
    section=[u'Direct Beam Runs', options, []]

    self.sections.append(section)
    options=self.dataset_options
    section=[u'Data Runs', options, []]
    self.sections.append(section)

    if len(self.evts)>0:
      options=self.event_options
      section=[u'Event Mode Options', options,
               [dict(zip(options, evt)) for evt in self.evts]]
      self.sections.append(section)

    if len(self.bgs)>0:
      options=self.bg_options
      section=[u'Advanced Background Options', options,
               [dict(zip(options, bg)) for bg in self.bgs]]
      self.sections.append(section)

  def _get_general_header(self):
    '''
      Return header lines present in any file, indipendent of datasets.
    '''
    output=[u'Datafile created by QuickNXS %s'%str_version]
    output.append(u'Date: %s'%strftime(u"%Y-%m-%d %H:%M:%S"))
    output.append(u'Type: %(datatype)s')
    output.append(u'Input file indices: %(indices)s')
    output.append(u'Extracted states: %(states)s')
    return u'\n'.join(output)

  def _get_section(self, section, options, data):
    '''
      Return one section from given data. Format each column so
      it does not get different size.
    '''
    output=u'[%s]\n'%section
    section_head=[]
    column_fstrings=[]
    # first run through all data and headers to determine each column widths
    for option in options:
      column_leni=len(option)
      if type(data[0][option]) in [bool, type(None), str, unicode]:
        item='%s'
        fstring='%%%%(%s) %%is'%option
      elif type(data[0][option])  is int:
        item=u'% i'
        fstring='%%%%(%s) %%ii'%option
      else:
        item=u'% g'
        fstring=u'%%%%(%s) %%ig'%option
      for di in data:
        column_leni=max(column_leni, len(item%di[option]))
      column_fstrings.append(fstring%column_leni)
      section_head.append(u'%% %is'%(column_leni)%option)
      print column_leni, option
    output+=u'  '.join(section_head)+u'\n'
    data_line=u'  '.join(column_fstrings)+u'\n'
    for di in data:
      output+=data_line%di
    return output

  def __unicode__(self):
    output=self._get_general_header()
    for section in self.sections:
      output+='\n'
      output+=self._get_section(*section)
    output+='\n'
    return output

  def __str__(self):
    return unicode(self).encode('utf8', 'ignore')

  @classmethod
  def get_data_header(cls, names, units):
    '''
      Return the lines used directly before the data to indicate units and dimensions.
    '''
    output='[Data]\n'
    output+='\t'.join(['%-20s'%('%s [%s]'%(name, unit)) for name, unit in zip(names, units)])
    return output


class HeaderParser(object):
  '''
    Use a header written by the HeaderCreator to reconstruct the Reflectivity objects.
  '''

class Exporter(object):
  '''
    Export data for reflectivity, offspecular or gisans data to
    different file types.
  '''


#  def export_data(self):
#    '''
#      Write all datasets to the selected format output.
#    '''
#    ofname=os.path.join(unicode(self.ui.directoryEntry.text()),
#                        unicode(self.ui.fileNameEntry.text()))
#    nlines=u''
#    plines=u''
#    for i, normi in enumerate(self.norms):
#      opts=dict(normi.options)
#      if type(normi.origin) is list:
#        fname=u";".join([origin[0] for origin in normi.origin])
#      else:
#        fname=normi.origin[0]
#      opts.update({'norm_index': i+1,
#                   'file_number': normi.options['number'],
#                   'file_name': fname,
#                   })
#      nlines+='# '+FILE_HEADER_PARAMS%opts
#      nlines+='\n'
#    for refli in self.refls:
#      opts=dict(refli.options)
#      if type(refli.origin) is list:
#        fname=u";".join([origin[0] for origin in refli.origin])
#      else:
#        fname=refli.origin[0]
#      opts.update({'norm_index': self.norms.index(refli.options['normalization'])+1,
#                   'file_number': refli.options['number'],
#                   'file_name': fname,
#                   })
#      plines+=u'# '+FILE_HEADER_PARAMS%opts
#      plines+='\n'
#    nlines=nlines[:-1] # remove last newline
#    plines=plines[:-1] # remove last newline
#    for key, output_data in self.output_data.items():
#      if self.ui.multiAscii.isChecked():
#        for channel in self.channels:
#          value=output_data[channel]
#          output=ofname.replace('{item}', key).replace('{state}', channel)\
#                       .replace('{type}', 'dat').replace('{numbers}', self.ind_str)
#          if not self.check_exists(output):
#            continue
#          of=open(output, 'w')
#          # write the file header
#          of.write((FILE_HEADER%{
#                                'date': strftime(u"%Y-%m-%d %H:%M:%S"),
#                                'version': str_version,
#                                'datatype': key,
#                                'indices': self.ind_str,
#                                'params_lines': plines,
#                                'norm_lines': nlines,
#                                'column_units': u"\t".join(output_data['column_units']),
#                                'column_names':  u"\t".join(output_data['column_names']),
#                                'channels': channel,
#                                }).encode('utf8'))
#          # write the data
#          if type(value) is not list:
#            savetxt(of, value, delimiter='\t')
#          else:
#            for filemap in value:
#              # separate first dimension steps by empty line
#              for scan in filemap:
#                savetxt(of, scan, delimiter='\t')
#                of.write('\n')
#            of.write('\n\n')
#          self.exported_files_all.append(output);self.exported_files_data.append(output)
#      if self.ui.combinedAscii.isChecked():
#        output=ofname.replace('{item}', key).replace('{state}', 'all')\
#                     .replace('{type}', 'dat').replace('{numbers}', self.ind_str)
#        if self.check_exists(output):
#          of=open(output, 'w')
#          # write the file header
#          of.write((FILE_HEADER%{
#                                'date': strftime(u"%Y-%m-%d %H:%M:%S"),
#                                'datatype': key,
#                                'indices': self.ind_str,
#                                'params_lines': plines,
#                                  'norm_lines': nlines,
#                                'column_units': u"\t".join(output_data['column_units']),
#                                'column_names':  u"\t".join(output_data['column_names']),
#                                'channels': u", ".join(self.channels),
#                                }).encode('utf8'))
#          # write all channel data separated by three empty lines and one comment
#          for channel in self.channels:
#            of.write('# Start of channel %s\n'%channel)
#            value=output_data[channel]
#            if type(value) is not list:
#              savetxt(of, value, delimiter='\t')
#            else:
#              for filemap in value:
#                # separate first dimension steps by empty line
#                for scan in filemap:
#                  savetxt(of, scan, delimiter='\t')
#                  of.write('\n')
#              of.write('\n\n')
#            of.write('# End of channel %s\n\n\n'%channel)
#          of.close()
#          self.exported_files_all.append(output);self.exported_files_data.append(output)
#    if self.ui.matlab.isChecked():
#      from scipy.io import savemat
#      for key, output_data in self.output_data.items():
#        dictdata=self.dictize_data(output_data)
#        output=ofname.replace('{item}', key).replace('{state}', 'all')\
#                       .replace('{type}', 'mat').replace('{numbers}', self.ind_str)
#        if not self.check_exists(output):
#          continue
#        savemat(output, dictdata, oned_as='column')
#        self.exported_files_all.append(output);self.exported_files_data.append(output)
#    if self.ui.numpy.isChecked():
#      for key, output_data in self.output_data.items():
#        dictdata=self.dictize_data(output_data)
#        output=ofname.replace('{item}', key).replace('{state}', 'all')\
#                       .replace('{type}', 'npz').replace('{numbers}', self.ind_str)
#        if not self.check_exists(output):
#          continue
#        savez(output, **dictdata)
#        self.exported_files_all.append(output);self.exported_files_data.append(output)
