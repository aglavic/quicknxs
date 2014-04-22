#-*- coding: utf-8 -*-
'''
REF_M specific values.
'''

config_file=''

NAME='REF_M'
BEAMLINE='4A'

# for the search of files by number
data_base=u'/SNS/REF_M'
BASE_SEARCH=u'*/data/REF_M_%s_'
OLD_BASE_SEARCH=u'*/*/%s/NeXus/REF_M_%s*'
LIVE_DATA=u'/SNS/REF_M/shared/LiveData/meta_data.xml'

# background pixels selected on startup
START_BG=(4, 104)

# gives the active area of a detector with SNSdetector_calibration_id as keys
DETECTOR_REGION={
                 # geometry file: (x, y)
                 'REF_M_geom_2009_03_19.xml': ((8, 295) , (8, 246)), # Brookhaven 304x256 detector
                 'REF_M_geom_2010_05_11.xml': ((8, 295) , (8, 246)), # Brookhaven 304x256 detector
                 }
