# compatibility with ipython console
import sip
sip.setapi('QString', 2)
sip.setapi('QVariant', 2)

# used for * imports
__all__=['mreduce', 'mrcalc']
