'''
  Use git to update the current minor version number to the number of commits
 till the last version tag
'''


from subprocess import Popen, PIPE
tag,revision,rev_name=Popen(['git','describe'], stdout=PIPE).communicate()[0].split('-',3)
revision=revision.strip()
last_change=Popen(['git', 'show', '-s', '--format=%ci'], stdout=PIPE).communicate()[0].rsplit(None,1)[0]

versiontxt=open("quick_nxs/version.py",'r').readlines()

output=open("quick_nxs/version.py",'w')
for line in versiontxt:
  if line.startswith('version='):
    old_revision=line.rsplit(',',1)[1].split(')',1)[0].strip()
    if old_revision==revision:
      exit()
    line=line.rsplit(',',1)[0]+', '+revision+')'+line.rsplit(',',1)[1].split(')',1)[1]
  if line.startswith('last_changes='):
    line='last_changes="%s"\n'%last_change
  output.write(line)
output.close()
