#!/usr/bin/env python
'''
Create and format a dependency graph for the project.
'''
from subprocess import Popen, PIPE

# create the graph file
result_1=Popen(['sfood', 'quicknxs'], stdout=PIPE).communicate()[0]
dot=Popen(['sfood-graph'], stdout=PIPE, stdin=PIPE).communicate(result_1)[0]

# process result dot file data

out_dot=[]
ext_packages=[]
first_add=True

for line in dot.splitlines():
  if line.startswith('"quicknxs"') or 'version' in line or '"logging"' in line or \
        'sip' in line or 'figureoptions' in line or 'types' in line or 'nxutils.so' in line or\
        'output_templates' in line or 'os' in line or 'sys' in line:
    continue
  elif line.startswith('"quicknxs/'):
    line=line.replace('style=filled', 'style=filled, color="#00aa00" shape=box, fontsize=12').replace('quicknxs/', '')
  if 'PyQt4' in line or 'email' in line or 'scipy' in line or 'matplotlib/' in line or \
      'IPython' in line:
    line=line.split('/')[0]+'";'
    if first_add:
      first_add=False
      out_dot.append('"PyQt4" [style=filled, color="#aa0000", fontsize=20];')
      out_dot.append('"scipy" [style=filled, color="#aaaaff", fontsize=12];')
      out_dot.append('"numpy" [style=filled, color="#0000aa", fontsize=20, fontcolor=white];')
      out_dot.append('"matplotlib" [style=filled, color="#aa00aa", fontsize=20];')
      out_dot.append('"IPython" [style=filled, color="#aaaa00"];')
      out_dot.append('"h5py" [style=filled, color="#aaffaa", fontsize=20];')
      for sys_module in ['glob', 'subprocess', 'multiprocessing', 'traceback',
                         'zipfile', 'StringIO', 'cPickle', 'atexit', 'tempfile',
                         'getpass', 'time', 'copy', 'inspect', 'email', 'smtplib']:
        out_dot.append('"%s" [shape=hexagon];'%sys_module)
  line=line.replace('pylab', 'matplotlib').replace('cStringIO', 'StringIO')
  out_dot.append(line.replace('.py', ''))

out_dot='\n'.join(out_dot)

Popen(['dot', '-Tps', '-o', 'import_graph.ps'], stdout=PIPE,
      stdin=PIPE).communicate(out_dot)
