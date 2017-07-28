#-*- coding: utf-8 -*-
'''
REF_M specific values.
'''

config_file=''

NAME='REF_M'
BEAMLINE='4A'

# for the search of files by number
data_base=u'/home/glavic_a/data/MR/examples'
BASE_SEARCH=u'*/data/REF_M_%s_'
OLD_BASE_SEARCH=u'*/*/%s/NeXus/REF_M_%s*'
LIVE_DATA=u'/SNS/REF_M/shared/LiveData/meta_data.xml'
EXTENSION_SCRIPTS=u'/SNS/REF_M/shared/quicknxs_scripts'
#AUTOREFL_LIVE_IMAGE=u'/tmp/autorefl.png'
#AUTOREFL_LIVE_INDEX=u'/tmp/autorefl_index.txt'
#AUTOREFL_RESULT_IMAGE=u'/tmp/reflectivity_%(title)s.png'
AUTOREFL_LIVE_IMAGE=u'/SNS/REF_M/shared/LiveData/autorefl.png'
AUTOREFL_LIVE_INDEX=u'/SNS/REF_M/shared/LiveData/autorefl_index.txt'
AUTOREFL_RESULT_IMAGE=u'%(origin_path)s/../shared/autoreduce/reflectivity_%(numbers)s.png'
autorefl_folder=u'/SNS/REF_M/shared/autoreduce/'

# background pixels selected on startup
START_BG=(4, 104)

# gives the active area of a detector with SNSdetector_calibration_id as keys
DETECTOR_REGION={
                 # geometry file: (x, y)
                 'REF_M_geom_2009_03_19.xml': ((8, 295) , (8, 246)), # Brookhaven 304x256 detector
                 'REF_M_geom_2010_05_11.xml': ((8, 295) , (8, 246)), # Brookhaven 304x256 detector
                 'REF_M_geom_2014_04_24.xml': ((8, 295) , (8, 246)), # Brookhaven 304x256 detector
                 }

DATABASE_ADDITIONAL_FIELDS=[
                           # field name, daslog entry
                            ('T', 'SampleTemp', float),
                            ('H', 'FieldRequest', float),
                            ('E', 'efieldvoltageactual', float),
                            ('s1w', 'S1HWidth', float),
                            ('s1h', 'S1VHeight', float),
                            ('s2w', 'S2HWidth', float),
                            ('s2h', 'S2VHeight', float),
                            ('s3w', 'S3HWidth', float),
                            ('s3h', 'S3VHeight', float),
                           ]

database_file=u'/home/glavic_a/data/MR/examples/shared/quicknxs_database'

DATABASE_DIRECT_BEAM_COMPARE=[
                              ('s1h', 'S1VHeight', float, 1.0),
                              ('s2h', 'S2VHeight', float, 1.0),
                               ]
