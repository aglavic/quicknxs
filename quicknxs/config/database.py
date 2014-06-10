#-*- coding: utf-8 -*-
'''
Configuration for the database table.
'''

config_file=''

ADDITIONAL_FIELDS=[
                   # field name, daslog entry
                    ('T', 'SampleTemp', float),
                    ('H', 'FieldRequest', float),
                    ('s1w', 'S1HWidth', float),
                    ('s1h', 'S1VHeight', float),
                    ('s2w', 'S2HWidth', float),
                    ('s2h', 'S2VHeight', float),
                    ('s3w', 'S3HWidth', float),
                    ('s3h', 'S3VHeight', float),
                   ]

DIRECT_BEAM_COMPARE=[
                    ('s1h', 'S1VHeight', float, 1.0),
                    ('s3h', 'S3VHeight', float, 1.0),
                     ]

db_file=u'%(paths.CFG_PATH)s/database'
