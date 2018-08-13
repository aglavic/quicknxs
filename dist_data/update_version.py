'''
  Use git to update the current minor version number to the number of commits
 till the last version tag
'''


from subprocess import Popen, PIPE
try:
  tag, maj_revision, revision=unicode(Popen(['git', 'describe'], stdout=PIPE).communicate()[0],
                                  encoding='utf8').split('.', 3)
except ValueError:
  tag=unicode(Popen(['git', 'describe'], stdout=PIPE).communicate()[0], encoding='utf8')
  revision=u'0'
revision=revision.strip()
last_change=Popen(['git', 'show', '-s', '--format=%ci'], stdout=PIPE).communicate()[0].rsplit(None,1)[0]

versiontxt=open("quicknxs/version.py",'r').readlines()

output=''
for line in versiontxt:
  if line.startswith('version='):
    old_revision=line.rsplit(',',1)[1].split(')',1)[0].strip()
    if old_revision!=revision:
      line=line.rsplit(',', 1)[0]+', '+revision+')'+line.rsplit(',', 1)[1].split(')', 1)[1]
  if line.startswith('last_changes='):
    line='last_changes="%s"\n'%last_change
  output+=line
open("quicknxs/version.py",'w').write(output)
