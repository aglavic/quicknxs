#-*- coding: utf-8 -*-
'''
Classes to create output files from reduced datasets,
create according file headers and reload datasets from
such headers.
'''

import os
import sys
import subprocess
import numpy as np
from logging import debug, info
from time import strftime
from zipfile import ZipFile
from cPickle import loads, dumps
from .decorators import log_call
from .mreduce import NXSData, NXSMultiData, Reflectivity, OffSpecular
from .mrcalc import smooth_data, DetectorTailCorrector
from .version import str_version
from .output_templates import *

from . import genx_data
# make sure importing and changing genx templates do only use our
# build in dummy module
sys.modules['genx.data']=genx_data
genx_data.DataList.__module__='genx.data'
genx_data.DataSet.__module__='genx.data'
TEMPLATE_PATH=os.path.join(os.path.dirname(__file__), 'genx_templates')

result_folder=os.path.expanduser(u'~/results')

class HeaderCreator(object):
  '''
  Class to create file headers from a set of Reflectivity objects.
  '''
  refls=None
  norms=None
  bgs=None
  bg_polys=None
  evts=None
  sections=None
  direct_beam_options=['P0', 'PN', 'x_pos', 'x_width', 'y_pos', 'y_width',
                       'bg_pos', 'bg_width', 'dpix', 'tth', 'number']
  dataset_options=['scale', 'P0', 'PN', 'x_pos', 'x_width', 'y_pos', 'y_width',
                   'bg_pos', 'bg_width', 'extract_fan', 'dpix', 'tth', 'number']
  bg_options=['bg_tof_constant', 'bg_scale_xfit', 'bg_poly_regions']
  event_options=['bin_type', 'bins', 'event_split_bins', 'event_split_index']

  def __init__(self, refls):
    self.refls=refls
    debug('Start collecting data for header creation.')
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
    self.bg_polys=[]
    for item in self.norms+self.refls:
      default=True
      for option in self.bg_options:
        if item.options[option]!=Reflectivity.DEFAULT_OPTIONS[option]:
          default=False
          break
      if not default:
        bg=[item.options[option] for option in self.bg_options]
        if bg[2]:
          # polygon regions are collected separately as they are lists
          poly_ids=[]
          for poly in bg[2]:
            poly=[poly[0][0], poly[0][1], poly[1][0], poly[1][1],
                  poly[2][0], poly[2][1], poly[3][0], poly[3][1]]
            if not poly in self.bg_polys:
              self.bg_polys.append(poly)
            poly_ids.append(self.bg_polys.index(poly)+1)              
          bg[2]=poly_ids
        self.bgs.append(bg)

  def _collect_event(self):
    '''
    Collect event mode readout options used to retrieve the reflectivity and normalization files.
    '''
    self.evts=[]
    for item in self.norms+self.refls:
      if type(item.origin) is list:
        if not item.origin[0][0].endswith('event.nxs'):
          continue
      else:
        if not item.origin[0].endswith('event.nxs'):
          continue
      event_opts=[item.read_options[option] for option in self.event_options]
      if not event_opts in self.evts:
        self.evts.append(event_opts)

  def _collect_data(self):
    '''
    Create actual data to be used in the output.
    '''
    self.sections=[]
    # direct beam measurements
    debug('Direct beam section')
    options=['DB_ID']+self.direct_beam_options
    if len(self.evts)>0:
      options.append('EVT_ID')
    if len(self.bgs)>0:
      options.append('BG_ID')
    options.append('File')
    data=[]
    for i, norm in enumerate(self.norms):
      datai=[i+1]+[norm.options[option] for option in self.direct_beam_options]
      if len(self.evts)>0:
        if type(norm.origin) is list and norm.origin[0][0].endswith('event.nxs')\
           or norm.origin[0].endswith('event.nxs'):
          event_opts=[norm.read_options[option] for option in self.event_options]
          datai.append(self.evts.index(event_opts)+1)
        else:
          datai.append(None)
      if len(self.bgs)>0:
        default=True
        for option in self.bg_options:
          if norm.options[option]!=Reflectivity.DEFAULT_OPTIONS[option]:
            default=False
            break
        if default:
          datai.append(None)
        else:
          bg=[norm.options[option] for option in self.bg_options]
          poly_ids=[]
          if bg[2]:
            for poly in bg[2]:
              poly=[poly[0][0], poly[0][1], poly[1][0], poly[1][1],
                    poly[2][0], poly[2][1], poly[3][0], poly[3][1]]
              poly_ids.append(self.bg_polys.index(poly))              
            bg[2]=poly_ids
          datai.append(self.bgs.index(bg))
      if type(norm.origin) is list:
        datai.append(repr([item[0] for item in norm.origin]))
      else:
        datai.append(norm.origin[0])
      data.append(datai)
    section=[u'Direct Beam Runs', options, [dict(zip(options, item)) for item in data]]
    self.sections.append(section)
    
    # extracted data measurements
    debug('data section')
    options=self.dataset_options+['DB_ID']
    if len(self.evts)>0:
      options.append('EVT_ID')
    if len(self.bgs)>0:
      options.append('BG_ID')
    options.append('File')
    data=[]
    for i, refl in enumerate(self.refls):
      datai=[refl.options[option] for option in self.dataset_options]
      datai.append(self.norms.index(refl.options['normalization'])+1)
      if len(self.evts)>0:
        if type(refl.origin) is list and refl.origin[0][0].endswith('event.nxs')\
           or refl.origin[0].endswith('event.nxs'):
          event_opts=[refl.read_options[option] for option in self.event_options]
          datai.append(self.evts.index(event_opts)+1)
        else:
          datai.append(None)
      if len(self.bgs)>0:
        default=True
        for option in self.bg_options:
          if refl.options[option]!=Reflectivity.DEFAULT_OPTIONS[option]:
            default=False
            break
        if default:
          datai.append(None)
        else:
          bg=[refl.options[option] for option in self.bg_options]
          poly_ids=[]
          if bg[2]:
            for poly in bg[2]:
              poly=[poly[0][0], poly[0][1], poly[1][0], poly[1][1],
                    poly[2][0], poly[2][1], poly[3][0], poly[3][1]]
              poly_ids.append(self.bg_polys.index(poly)+1)              
            bg[2]=poly_ids
          datai.append(self.bgs.index(bg))
      if type(refl.origin) is list:
        datai.append(repr([item[0] for item in refl.origin]))
      else:
        datai.append(refl.origin[0])
      data.append(datai)
    section=[u'Data Runs', options, [dict(zip(options, item)) for item in data]]
    self.sections.append(section)

    debug('Event mode readout section')
    # optional event mode block
    if len(self.evts)>0:
      options=['EVT_ID']+self.event_options
      data=[]
      for i, evt in enumerate(self.evts):
        data.append([i+1]+evt)
      section=[u'Event Mode Options', options,
               [dict(zip(options, item)) for item in data]]
      self.sections.append(section)

    debug('Background section')
    # optional background block
    if len(self.bgs)>0:
      options=['BG_ID']+self.bg_options
      data=[]
      for i, bg in enumerate(self.bgs):
        data.append([i+1]+bg)
      section=[u'Advanced Background Options', options,
               [dict(zip(options, item)) for item in data]]
      self.sections.append(section)
    
    #optional background polynom block
    if len(self.bg_polys)>0:
      options=['poly_region', 'l1', 'x1', 'l2', 'x2', 'l3', 'x3', 'l4', 'x4']
      data=[]
      for i, poly in enumerate(self.bg_polys):
        data.append([i+1]+poly)
      section=[u'Background Polygon Regions', options,
               [dict(zip(options, item)) for item in data]]
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
      if type(data[0][option]) in [bool, type(None), str, unicode, list]:
        item=u'%s'
        fstring=u'%%%%(%s)-%%is'%option
      elif type(data[0][option])  is int:
        item=u'% i'
        fstring=u'%%%%(%s)-%%ii'%option
      else:
        item=u'% g'
        fstring=u'%%%%(%s)-%%ig'%option
      for di in data:
        column_leni=max(column_leni, len(item%di[option]))
      column_fstrings.append(fstring%column_leni)
      section_head.append(u'%%-%is'%(column_leni)%option)
    output+=u'  '.join(section_head)+u'\n'
    data_line=u'  '.join(column_fstrings)+u'\n'
    for di in data:
      output+=data_line%di
    return output

  def __unicode__(self):
    output=self._get_general_header()
    output+=u'\n'
    for section in self.sections:
      output+=u'\n'
      output+=self._get_section(*section)
    output+=u'\n'
    return output

  if sys.version_info[0]>=3:
    def __str__(self):
      return self.__unicode__()
  else:
    def __str__(self):
      return self.__unicode__().encode('utf8', 'ignore')

  @classmethod
  def get_data_header(cls, names, units):
    '''
    Return the lines used directly before the data to indicate units and dimensions.
    '''
    output=u'[Data]\n'
    output+=u'\t'.join([u'%-20s'%(u'%s [%s]'%(name, unit)) for name, unit in zip(names, units)])
    return output+u'\n'
  
  @classmethod
  def get_data_comment(cls, names, units):
    '''
    Return the lines used directly before the data to indicate units and dimensions.
    '''
    output=u'# [Data]\n'
    output+=u'# '+u'\t'.join([u'%-20s'%(u'%s [%s]'%(name, unit)) for name, unit in zip(names, units)])
    return output+u'\n'
  
  def as_comments(self):
    output=unicode(self)
    return u'# '+u'\n# '.join([line for line in output.splitlines()])+'\n'


class HeaderParser(object):
  '''
  Use a header written by the HeaderCreator to reconstruct the Reflectivity objects.
  '''
  direct_beam_defaults=dict(DB_ID=0, EVT_ID=None, BG_ID=None, P0=0, PN=0, x_pos=206., x_width=9.,
                            y_pos=120., y_width=120., bg_pos=80., bg_width=40.,
                            dpix=206., tth=0., number=u'', File=None)
  dataset_defaults=dict(DB_ID=0, EVT_ID=None, BG_ID=None, scale=1., extract_fan=False,
                        P0=0, PN=0, x_pos=206., x_width=9.,
                        y_pos=120., y_width=120., bg_pos=80., bg_width=40.,
                        dpix=206., tth=0., number=u'', File=None)
  bg_defaults=dict(BG_ID=0, bg_tof_constant=False, bg_scale_xfit=False, bg_poly_regions=None)
  event_defaults=dict(EVT_ID=0, bin_type=0, bins=40, event_split_bins=10, event_split_index=0)
  poly_defaults=dict(poly_region=0, l1=0., l2=0., l3=0., l4=0.,
                                    x1=0., x2=0., x3=0., x4=0.)
  callback=None
  
  def __init__(self, header):
    if type(header) is not unicode:
      header=unicode(header, 'utf8', 'ignore')
    self.header=header
    self.sections={}
    self._collect_sections()
    self._evaluate()
  
  def parse(self, callback=None):
    self.callback=callback
    self._read_direct_beam()
    self._read_datasets()
  
  def _collect_sections(self):
    '''
    Go through the header lines and locate section data.
    This is then stored in a dictionary.
    '''
    hlines=self.header.splitlines()
    hlines=map(lambda line: line.lstrip('#'), hlines)
    current_section=None
    for line in hlines:
      line=line.strip()
      if line.startswith('[') and line.endswith(']'):
        current_section=line[1:-1]
        self.sections[current_section]=[]
      elif line.strip()=='':
        current_section=None
      elif current_section is not None:
        self.sections[current_section].append(line)
  
  def _evaluate_section(self, section, defaults):
    '''
    Convert section data to python types and create a dictionary
    for each line in a section. Default values can be supplied
    to overwrite undefined values or supply integer type conversion.
    '''
    sitems=[item.strip() for item in self.sections[section][0].split(u'  ') if item.strip()!=u'']    
    sdata=[[item.strip() for item in line.split(u'  ') if item.strip()!=u'']
                                for line in self.sections[section][1:]]
    output=[]
    for item in sdata:
      idata=dict(defaults)
      for i, key in enumerate(sitems):
        value=item[i]
        if key in defaults and type(defaults[key]) in [str, unicode]:
          idata[key]=value
        elif value in ['True', 'False', 'None'] or ',' in value or \
              ('[' in value and ']' in value):
          idata[key]=eval(value)
        else:
          try:
            value=float(value)
          except ValueError:
            idata[key]=unicode(value)
          else:
            if key in defaults and type(defaults[key]) is int:
              idata[key]=int(value)
            else:
              idata[key]=value
      output.append(idata)
    return output

  def _evaluate(self):
    '''
    Evaluate given sections with their default values.
    '''
    self.section_data={}
    self.section_data['Direct Beam Runs']=self._evaluate_section('Direct Beam Runs',
                                                                 self.direct_beam_defaults)
    self.section_data['Data Runs']=self._evaluate_section('Data Runs',
                                                          self.dataset_defaults)
    if 'Event Mode Options' in self.sections:
      self.section_data['Event Mode Options']=self._evaluate_section(
                        'Event Mode Options', self.event_defaults)
    if 'Advanced Background Options' in self.sections:
      self.section_data['Advanced Background Options']=self._evaluate_section(
                        'Advanced Background Options', self.bg_defaults)
    if 'Background Polygon Regions' in self.sections:
      self.section_data['Background Polygon Regions']=self._evaluate_section(
                        'Background Polygon Regions', self.poly_defaults)
    self._collect_background_options()
  
  def _get_dataset(self, options):
    fname=options['File']
    read_opts=dict(NXSData.DEFAULT_OPTIONS)
    if options['EVT_ID'] is not None:
      if not "Event Mode Options" in self.section_data:
        raise ValueError, 'No "Event Mode Options" section defined but EVT_ID is set'
      evt_opts=self.section_data["Event Mode Options"][int(options['EVT_ID'])-1]
      for key in ['bin_type', 'bins', 'event_split_bins', 'event_split_index']:
        read_opts[key]=evt_opts[key]
    info('Reading %s'%fname)
    if type(fname) is list:
      return NXSMultiData(fname, **read_opts)
    else:
      return NXSData(fname, **read_opts)
  
  def _collect_background_options(self):
    if not 'Advanced Background Options' in self.section_data:
      return
    self._bg_options=[]
    for item in self.section_data['Advanced Background Options']:
      opt_item={}
      for key in ['bg_tof_constant', 'bg_scale_xfit']:
        opt_item[key]=item[key]
      if item['bg_poly_regions'] is not None:
        if not 'Background Polygon Regions' in self.section_data:
          raise ValueError, 'No "Background Polygon Regions" section defined but bg_poly_regions is set'
        opt_item['bg_poly_regions']=[]
        for index in item['bg_poly_regions']:
          poly=self.section_data['Background Polygon Regions'][index-1]
          opt_item['bg_poly_regions'].append([
                                              [poly['l1'], poly['x1']],
                                              [poly['l2'], poly['x2']],
                                              [poly['l3'], poly['x3']],
                                              [poly['l4'], poly['x4']],
                                              ])
      else:
        opt_item['bg_poly_regions']=None
      self._bg_options.append(opt_item)
  
  def _read_direct_beam(self):
    self.norms=[]
    self.norm_data=[]
    ilen=float(len(self.section_data['Direct Beam Runs'])+len(self.section_data['Data Runs']))
    for i, db in enumerate(self.section_data['Direct Beam Runs']):
      if self.callback:
        self.callback((i+1)/ilen)
      data=self._get_dataset(db)
      calc_opts={}
      for key in Reflectivity.DEFAULT_OPTIONS.keys():
        if key in db:
          calc_opts[key]=db[key]
      if db['BG_ID'] is not None:
        if not 'Advanced Background Options' in self.section_data:
          raise ValueError, 'No "Advanced Background Options" section defined but BG_ID is set'
        calc_opts.update(self._bg_options[int(db['BG_ID'])-1])
      norm=Reflectivity(data[0], **calc_opts)
      self.norms.append(norm)
      self.norm_data.append(data)

  def _read_datasets(self):
    self.refls=[]
    ilen=float(len(self.section_data['Direct Beam Runs'])+len(self.section_data['Data Runs']))
    dblen=len(self.section_data['Direct Beam Runs'])
    for i, db in enumerate(self.section_data['Data Runs']):
      if self.callback:
        self.callback((i+1+dblen)/ilen)
      data=self._get_dataset(db)
      calc_opts={}
      for key in Reflectivity.DEFAULT_OPTIONS.keys():
        if key in db:
          calc_opts[key]=db[key]
      if db['BG_ID'] is not None:
        if not 'Advanced Background Options' in self.section_data:
          raise ValueError, 'No "Advanced Background Options" section defined but BG_ID is set'
        calc_opts.update(self._bg_options[int(db['BG_ID'])-1])
      calc_opts['normalization']=self.norms[int(db['DB_ID'])-1]
      refl=Reflectivity(data[0], **calc_opts)
      self.refls.append(refl)      

class Exporter(object):
  '''
  Export data for reflectivity, offspecular or gisans to
  different file types. Mostly intended for use in the ReduceDialog
  but can also be helpful for scripts which export data.
  '''

  def __init__(self, channels, refls):
    self.norms=[]
    for refli in refls:
      if refli.options['normalization'] not in self.norms:
        self.norms.append(refli.options['normalization'])
    self.channels=list(channels) # make sure we don't alter the original list
    self.refls=refls
    self.file_header=HeaderCreator(self.refls)
    self.read_data()
    self.output_data={}
    self.exported_files_all=[]
    self.exported_files_data=[]
    self.exported_files_plots=[]

  @log_call
  def read_data(self):
    '''
    Read the raw data of all files. This means that for multiple
    extraction routines the data is only read once.
    '''
    self.indices=[]
    self.raw_data={}
    for refli in self.refls:
      if type(refli.origin) is list:
        flist=[origin[0] for origin in refli.origin]
        self.raw_data[refli.options['number']]=NXSMultiData(flist, **refli.read_options)
        self.indices.append(refli.options['number'])
      else:
        self.raw_data[refli.options['number']]=NXSData(refli.origin[0], **refli.read_options)
        self.indices.append(refli.options['number'])
    self.indices.sort()
    self.ind_str="+".join(map(str, self.indices))
    self.ipts_str=self.raw_data.values()[0].experiment

  @log_call
  def extract_reflectivity(self):
    '''
    Extract the specular reflectivity for all datasets.
    '''
    output_data=dict([(channel, []) for channel in self.channels])
    output_data['column_units']=[u'Å⁻¹', 'a.u.', 'a.u.', u'Å⁻¹', 'rad']
    output_data['column_names']=['Qz', 'R', 'dR', 'dQz', u'αi']

    for refli in self.refls:
      opts=refli.options
      index=opts['number']
      fdata=self.raw_data[index]
      P0=len(fdata[0].tof)-opts['P0']
      PN=opts['PN']
      for channel in self.channels:
        res=Reflectivity(fdata[channel], **opts)
        Qz, R, dR, dQz=res.Q, res.R, res.dR, res.dQ
        rdata=np.vstack([Qz[PN:P0], R[PN:P0], dR[PN:P0], dQz[PN:P0],
                      0.*Qz[PN:P0]+res.ai]).transpose()
        output_data[channel].append(rdata)
    for channel in self.channels:
      d=np.vstack(output_data[channel])
      # sort dataset for Qz
      order=np.argsort(d[:, 0])
      d=d[order.flatten(), :]

      output_data[channel]=d
    self.output_data['Specular']=output_data

  @log_call
  def extract_offspecular(self):
    '''
    Extract the off-specular scattering for all datasets.
    '''
    output_data=dict([(channel, []) for channel in self.channels])
    output_data['column_units']=[u'Å⁻¹', u'Å⁻¹', u'Å⁻¹', u'Å⁻¹', u'Å⁻¹', 'a.u.', 'a.u.']
    output_data['column_names']=['Qx', 'Qz', 'ki_z', 'kf_z', 'ki_z-kf_z', 'I', 'dI']


    ki_max=0.01
    for refli in self.refls:
      opts=refli.options
      index=opts['number']
      fdata=self.raw_data[index]
      P0=len(fdata[channel].tof)-opts['P0']
      PN=opts['PN']
      for channel in self.channels:
        offspec=OffSpecular(fdata[channel], **opts)
        Qx, Qz, ki_z, kf_z, S, dS=(offspec.Qx, offspec.Qz, offspec.ki_z, offspec.kf_z,
                                   offspec.S, offspec.dS)

        rdata=np.array([Qx[:, PN:P0], Qz[:, PN:P0], ki_z[:, PN:P0], kf_z[:, PN:P0],
                      ki_z[:, PN:P0]-kf_z[:, PN:P0], S[:, PN:P0], dS[:, PN:P0]],
                    copy=False).transpose((1, 2, 0))
        output_data[channel].append(rdata)
        ki_max=max(ki_max, ki_z.max())
    output_data['ki_max']=ki_max
    self.output_data['OffSpec']=output_data

  @log_call
  def extract_offspecular_corr(self):
    '''
    Extract the off-specular scattering for all datasets and correct it
    for the tails produced by the detector in x-direction.
    '''
    output_data=dict([(channel, []) for channel in self.channels])
    output_data['column_units']=[u'Å⁻¹', u'Å⁻¹', u'Å⁻¹', u'Å⁻¹', u'Å⁻¹', 'a.u.', 'a.u.']
    output_data['column_names']=['Qx', 'Qz', 'ki_z', 'kf_z', 'ki_z-kf_z', 'I', 'dI']

    corr_ds=self.norms[0]
    if type(corr_ds.origin) is list:
      flist=[origin[0] for origin in corr_ds.origin]
      corr_data=NXSMultiData(flist, **corr_ds.read_options)[0]
    else:
      corr_data=NXSData(corr_ds.origin[0], **corr_ds.read_options)[0]
    debug('Correction from normalization '+repr(corr_data))
    corrector=DetectorTailCorrector(corr_data.xdata, x0=corr_ds.options['x_pos'])

    ki_max=0.01
    for refli in self.refls:
      opts=refli.options
      index=opts['number']
      fdata=self.raw_data[index]
      P0=len(fdata[channel].tof)-opts['P0']
      PN=opts['PN']
      for channel in self.channels:
        offspec=OffSpecular(fdata[channel], **opts)
        Qx, Qz, ki_z, kf_z, S, dS=(offspec.Qx, offspec.Qz, offspec.ki_z, offspec.kf_z,
                                   offspec.S, offspec.dS)
        debug('sum(S) before '+repr(S.sum()))
        S=corrector(S)
        debug('sum(S) after '+repr(S.sum()))
        rdata=np.array([Qx[:, PN:P0], Qz[:, PN:P0], ki_z[:, PN:P0], kf_z[:, PN:P0],
                      ki_z[:, PN:P0]-kf_z[:, PN:P0], S[:, PN:P0], dS[:, PN:P0]],
                    copy=False).transpose((1, 2, 0))
        output_data[channel].append(rdata)
        ki_max=max(ki_max, ki_z.max())
    output_data['ki_max']=ki_max
    self.output_data['OffSpecCorr']=output_data

  @log_call
  def smooth_offspec(self, settings, pb=None):
    '''
    Create a smoothed dataset from the offspecular scattering.
    '''
    output_data={}
    pbinfo="Smoothing Channel "
    if 'OffSpecCorr' in self.output_data:
      odata=self.output_data['OffSpecCorr']
    else:
      odata=self.output_data['OffSpec']
    for i, channel in enumerate(self.channels):
      if pb is not None:
        pb.info.setText(pbinfo+channel)
        pb.add=100*i
      data=np.hstack(odata[channel])
      I=data[:, :, 5].flatten()
      Qzmax=data[:, :, 2].max()*2.
      if settings['xy_column']==0:
        x=data[:, :, 4].flatten()
        y=data[:, :, 1].flatten()
        output_data['column_units']=[u'Å⁻¹', u'Å⁻¹', 'a.u.']
        output_data['column_names']=['ki_z-kf_z', 'Qz', 'I']
        axis_sigma_scaling=2
        xysigma0=Qzmax/3.
      elif settings['xy_column']==1:
        x=data[:, :, 0].flatten()
        y=data[:, :, 1].flatten()
        output_data['column_units']=[u'Å⁻¹', u'Å⁻¹', 'a.u.']
        output_data['column_names']=['Qx', 'Qz', 'I']
        axis_sigma_scaling=2
        xysigma0=Qzmax/3.
      else:
        x=data[:, :, 2].flatten()
        y=data[:, :, 3].flatten()
        output_data['column_units']=[u'Å⁻¹', u'Å⁻¹', 'a.u.']
        output_data['column_names']=['ki_z', 'kf_z', 'I']
        axis_sigma_scaling=3
        xysigma0=Qzmax/6.
      x, y, I=smooth_data(settings, x, y, I, callback=pb.progress, sigmas=settings['sigmas'],
                          axis_sigma_scaling=axis_sigma_scaling, xysigma0=xysigma0)
      output_data[channel]=[np.array([x, y, I]).transpose((1, 2, 0))]
    output_data['ki_max']=self.output_data['OffSpec']['ki_max']
    self.output_data['OffSpecSmooth']=output_data

  @log_call
  def export_data(self, directory=result_folder,
                  naming=u'REF_M_{numbers}_{item}_{state}.{type}',
                  multi_ascii=True,
                  combined_ascii=False,
                  matlab_data=False,
                  numpy_data=False,
                  check_exists=lambda ignore: True,
                  ):
    '''
    Write all datasets to the selected format output.
    '''
    ofname=os.path.join(directory, naming)
    for key, output_data in self.output_data.items():
      if multi_ascii:
        debug('Export multi_ascii')
        for channel in self.channels:
          value=output_data[channel]
          output=ofname.replace('{item}', key).replace('{state}', channel)\
                       .replace('{type}', 'dat').replace('{numbers}', self.ind_str)
          if not check_exists(output):
            continue
          of=open(output, 'w')
          # write the file header
          of.write((self.file_header.as_comments()%{
                                'datatype': key,
                                'indices': self.ind_str,
                                'states': channel,
                                }).encode('utf8'))
          of.write((self.file_header.get_data_comment(output_data['column_names'],
                                                     output_data['column_units'])
                    ).encode('utf8'))
          # write the data
          if type(value) is not list:
            np.savetxt(of, value, delimiter='\t', fmt='%-18e')
          else:
            for filemap in value:
              # separate first dimension steps by empty line
              for scan in filemap:
                np.savetxt(of, scan, delimiter='\t', fmt='%-18e')
                of.write('\n')
            of.write('\n\n')
          self.exported_files_all.append(output);self.exported_files_data.append(output)
      if combined_ascii:
        debug('Export multi_ascii')
        output=ofname.replace('{item}', key).replace('{state}', 'all')\
                     .replace('{type}', 'dat').replace('{numbers}', self.ind_str)
        if check_exists(output):
          of=open(output, 'w')
          # write the file header
          of.write((self.file_header.as_comments()%{
                                'datatype': key,
                                'indices': self.ind_str,
                                'states': u", ".join(self.channels),
                                }).encode('utf8'))
          # write all channel data separated by three empty lines and one comment
          for channel in self.channels:
            of.write('# Start of channel %s\n'%channel)
            of.write((self.file_header.get_data_comment(output_data['column_names'],
                                                       output_data['column_units'])
                      ).encode('utf8'))
            value=output_data[channel]
            if type(value) is not list:
              np.savetxt(of, value, delimiter='\t', fmt='%-18e')
            else:
              for filemap in value:
                # separate first dimension steps by empty line
                for scan in filemap:
                  np.savetxt(of, scan, delimiter='\t', fmt='%-18e')
                  of.write('\n')
              of.write('\n\n')
            of.write('# End of channel %s\n\n\n'%channel)
          of.close()
          self.exported_files_all.append(output);self.exported_files_data.append(output)
    if matlab_data:
      debug('Export matlab')
      from scipy.io import savemat
      for key, output_data in self.output_data.items():
        dictdata=self.dictize_data(output_data)
        output=ofname.replace('{item}', key).replace('{state}', 'all')\
                       .replace('{type}', 'mat').replace('{numbers}', self.ind_str)
        if not check_exists(output):
          continue
        savemat(output, dictdata, oned_as='column')
        self.exported_files_all.append(output);self.exported_files_data.append(output)
    if numpy_data:
      debug('Export numpy')
      for key, output_data in self.output_data.items():
        dictdata=self.dictize_data(output_data)
        output=ofname.replace('{item}', key).replace('{state}', 'all')\
                       .replace('{type}', 'npz').replace('{numbers}', self.ind_str)
        if not check_exists(output):
          continue
        np.savez(output, **dictdata)
        self.exported_files_all.append(output);self.exported_files_data.append(output)

  def dictize_data(self, output_data):
    '''
    Create a dictionary for export of data for e.g. Matlab files.
    '''
    output={}
    # items containing information on the saved columns
    output["columns"]=output_data['column_names']
    output["units"]=output_data['column_units']
    for channel in self.channels:
      data=output_data[channel]
      if type(data) is not list:
        output[DICTIZE_CHANNELS[channel]]=data
      else:
        for i, plotmap in enumerate(data):
          output[DICTIZE_CHANNELS[channel]+"_"+str(i)]=plotmap
    return output

  @log_call
  def create_gnuplot_scripts(self, directory=result_folder,
                  naming=u'REF_M_{numbers}_{item}_{state}.{type}',
                  check_exists=lambda ignore: True):
    '''
    Create gnuplot scripts in images for all exported datasets.
    '''
    for title, output_data in self.output_data.items():
        self._create_gnuplot_script(output_data, title, directory, naming, check_exists)
    
  def _create_gnuplot_script(self, output_data, title, directory, naming, check_exists):
    ind_str=self.ind_str
    ofname_full=os.path.join(directory, naming)
    output=ofname_full.replace('{item}', title).replace('{state}', 'all')\
                 .replace('{type}', 'gp').replace('{numbers}', ind_str)
    if not check_exists(output):
      return
    if type(output_data[self.channels[0]]) is not list:
      # 2D PLot
      params=dict(
                  output=naming.replace('{item}', title).replace('{state}', 'all')\
                         .replace('{type}', '').replace('{numbers}', ind_str),
                  xlabel=u"Q_z [Å^{-1}]",
                  ylabel=u"Reflectivity",
                  pix_x=1600,
                  pix_y=1200,
                  title=ind_str,
                  )
      plotlines=[]
      for i, channel in enumerate(self.channels):
        filename=naming.replace('{item}', title).replace('{state}', channel)\
                     .replace('{type}', 'dat').replace('{numbers}', ind_str)
        plotlines.append(GP_LINE%dict(file_name=filename, channel=channel, index=i+1))
      params['plot_lines']=GP_SEP.join(plotlines)
      script=GP_TEMPLATE%params
      open(output, 'w').write(script.encode('utf8'))
    else:
      # 3D plot
      if 'ki_max' in output_data:
        ki_max=output_data['ki_max']
      else:
        ki_max=None
      rows=1+int(len(self.channels)>2)
      cols=1+int(len(self.channels)>1)
      params=dict(
                  output=naming.replace('{item}', title).replace('{state}', 'all')\
                         .replace('{type}', '').replace('{numbers}', ind_str),
                  zlabel=u"I [a.u.]",
                  title=ind_str,
                  rows=rows,
                  cols=cols,
                  )
      params['pix_x']=1000*cols
      params['pix_y']=200+1200*rows
      if title in ['OffSpec', 'OffSpecCorr']:
        params['ratio']=1.5
        params['ylabel']=u"Q_z [Å^{-1}]"
        params['xlabel']=u"k_{i,z}-k_{f,z} [Å^{-1}]"
        params['xrange']="%f:%f"%(-0.025, 0.025)
        params['yrange']="%f:%f"%(0.0, 1.413*ki_max)
        line_params=dict(x=5, y=2, z=6)
      else:
        line_params=dict(x=1, y=2, z=3)
        if output_data['column_names'][0]=='Qy':
          # GISANS
          params['ratio']=1.
          params['ylabel']=u"Q_z [Å^{-1}]"
          params['yrange']="*:*"
          params['xlabel']=u"Q_y [Å^{-1}]"
          params['xrange']="*:*"
        elif output_data['column_names'][1]=='Qz':
          params['ratio']=1.5
          params['ylabel']=u"Q_z [Å^{-1}]"
          params['yrange']="%f:%f"%(0.0, 1.413*ki_max)
          if output_data['column_names'][0]=='Qx':
            params['xlabel']=u"Q_x [Å^{-1}]"
            params['xrange']="%f:%f"%(-0.0005, 0.0005)
          else:
            params['xlabel']=u"k_{i,z}-k_{f,z} [Å^{-1}]"
            params['xrange']="%f:%f"%(-0.025, 0.025)
        else:
          params['ratio']=1.
          params['xlabel']=u"k_{i,z} [Å^{-1}]"
          params['ylabel']=u"k_{f,z} [Å^{-1}]"
          params['xrange']="%f:%f"%(0., ki_max)
          params['yrange']="%f:%f"%(0., ki_max)
          params['pix_x']=1400*cols
      zmax=1e-6
      zmin=1e6
      for channel in self.channels:
        for data in output_data[channel]:
          z=data[:, :, line_params['z']-1]
          zmax=max(zmax, z.max())
          zmin=min(zmin, z[z>0].min())
      params['zmin']="%.1e"%(zmin*0.8)
      params['zmax']="%.1e"%zmax
      plotlines=''
      for channel in self.channels:
        line_params['file_name']=naming.replace('{item}', title).replace('{state}', channel)\
                     .replace('{type}', 'dat').replace('{numbers}', ind_str)
        plotlines+=GP_SEP_3D%channel+GP_LINE_3D%line_params
      params['plot_lines']=plotlines
      script=GP_TEMPLATE_3D%params
      open(output, 'w').write(script.encode('utf8'))
    self.exported_files_all.append(output)
    try:
      subprocess.call(['gnuplot', output], cwd=directory, shell=False)
    except:
      pass
    else:
      folder=os.path.dirname(output)
      if type(output_data[self.channels[0]]) is not list:
        output=os.path.join(folder, params['output']+'png')
      else:
        output=os.path.join(folder, params['output']+'png')
      self.exported_files_all.append(output);self.exported_files_plots.append(output)

  @log_call
  def create_genx_file(self, directory=result_folder,
                       naming=u'REF_M_{numbers}_{item}_{state}.{type}',
                       check_exists=lambda ignore: True):
    '''
    Create a Genx .gx model file with the right polarization states
    and the reflectivity data already included for convenience.
    '''
    ofname=os.path.join(directory, naming)
    if 'x' in self.channels:
      template=os.path.join(TEMPLATE_PATH, 'unpolarized.gx')
    elif '+' in self.channels or '-' in self.channels:
      template=os.path.join(TEMPLATE_PATH, 'polarized.gx')
    else:
      template=os.path.join(TEMPLATE_PATH, 'spinflip.gx')
    for key, output_data in self.output_data.items():
      if not key in ['Specular', 'TrueSpecular']:
        continue
      output=ofname.replace('{item}', key).replace('{state}', 'all')\
                   .replace('{type}', 'gx').replace('{numbers}', self.ind_str)
      if not check_exists(output):
        continue
      oz=ZipFile(output, 'w')
      iz=ZipFile(template, 'r')
      for key in ['script', 'parameters', 'fomfunction', 'config', 'optimizer']:
        oz.writestr(key, iz.read(key))
      model_data=loads(iz.read('data'))
      for i, channel in enumerate(self.channels):
        model_data[i].x_raw=output_data[channel][:, 0]
        model_data[i].y_raw=output_data[channel][:, 1]
        model_data[i].error_raw=output_data[channel][:, 2]
        model_data[i].xerror_raw=output_data[channel][:, 3]
        model_data[i].name=channel
        model_data[i].run_command()
      oz.writestr('data', dumps(model_data))
      iz.close()
      oz.close()
      self.exported_files_all.append(output)

