__all__=['test_suites']

import os
from glob import glob

test_modules=map(os.path.basename, glob(os.path.join(os.path.dirname(__file__), '*.py')))
test_modules.remove('__init__.py')
test_modules=[test[:-3] for test in test_modules]

test_suites=[]

# read all test modules and collect their test suites
for module_name in test_modules:
  try:
    test_module=__import__('tests.'+module_name, fromlist=[module_name])
  except:
    continue
  if 'suite' in test_module.__dict__:
    test_suites.append(test_module.suite)
