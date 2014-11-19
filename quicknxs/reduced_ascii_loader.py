import os
from ascii_loader import asciiLoader

class reducedAsciiLoader(object):
	
	mainGui = None
	asciiFilename = ''
	shortAsciiFilename = ''
	
	col1 = []
	col2 = []
	col3 = []
	col4 = []
	
	isEnabled = True
	
	def __init__(self, mainGui, asciiFilename):
		
		self.mainGui = mainGui
		self.asciiFilename = asciiFilename
		self.shortAsciiFilename = self.getShortAsciiFilename(asciiFilename)
		
		self.retrieve_ascii_data()
		
	def getShortAsciiFilename(self, fullFilename):
		return os.path.basename(fullFilename)
	
	def retrieve_ascii_data(self):
		
		filename = self.asciiFilename
		nbrColumns = 3
		_asciiData = asciiLoader(filename,
		                         nbrColumns=nbrColumns)
		
		
		[self.col1, self.col2, self.col3, self.col4] = _asciiData.data()
		