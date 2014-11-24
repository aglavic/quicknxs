import datetime

class FileLoadedObject(object):
	
	fullFileName = ''
	lastTimeUsed = ''
	
	def __init__(self, fullFileName):
		
		self.fullFileName = fullFileName
		self.lastTimeUsed = self.setNewTime()
		
	def setNewTime(self):
		
		self.lastTimeUsed = datetime.datetime.today()
		