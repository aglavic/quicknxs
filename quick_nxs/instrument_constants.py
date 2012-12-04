#-*- coding: utf-8 -*-
'''
  Parameters needed for some calculations.
'''

H_OVER_M_NEUTRON=3.956034e-7 # h/m_n [m²/s]

TOF_DISTANCE=21.2535 # m
#RAD_PER_PIX=0.000171
#RAD_PER_PIX=0.000171*1.125
RAD_PER_PIX=0.0002734242
DETECTOR_X_REGION=(8, 295)

# position and maximum deviation of polarizer and analzer in it's working position
ANALYZER_IN=(0., 100.)
POLARIZER_IN=(-348., 50.)

MAPPING_FULLPOL=(
                 (u'++', u'entry-Off_Off'),
                 (u'--', u'entry-On_On'),
                 (u'+-', u'entry-Off_On'),
                 (u'-+', u'entry-On_Off'),
                 )
MAPPING_HALFPOL=(
                 (u'+', u'entry-Off_Off'),
                 (u'-', u'entry-On_Off'),
                 )
MAPPING_UNPOL=((u'x', u'entry-Off_Off'))
