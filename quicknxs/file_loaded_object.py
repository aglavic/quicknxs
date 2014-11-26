import datetime

class FileLoadedObject(object):
	
	fullFileName = ''
	lastTimeUsed = ''
	
	def __init__(self, fullFileName, date=None):
		self.fullFileName = fullFileName
		if date is None:
			self.setNewTime()
		else:
			self.lastTimeUsed = date
		
	def setNewTime(self):
		self.lastTimeUsed = str(datetime.datetime.today())
		
