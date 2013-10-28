#-*- coding: utf-8 -*-
'''
Email options set by the user when exporting.
'''

config_file='reduction'

ZIPData=True
To=u'%(paths.USER)s@ornl.gov'
Cc=u''
Subject=u'SNS BL %(instrument.BEAMLINE)s extraction {ipts}'
Text=u'''Dear User,

Here is the data extracted for the files {numbers}.

Regards from beamline %(instrument.BEAMLINE)s'''
SendAll=False
SendPlots=False
SendData=True
