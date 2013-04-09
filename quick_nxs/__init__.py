'''
Package of the QuickNXS program that can be used separately to reduce data from
the SNS magnetism reflectometer, beamline 4A.
'''
try:
  # compatibility with ipython console
  import sip
  sip.setapi('QString', 2)
  sip.setapi('QVariant', 2)
except:
  pass

# used for * imports
__all__=['mreduce', 'mrcalc', 'mrio']
