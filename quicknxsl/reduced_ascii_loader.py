import os
from ascii_loader import asciiLoader

class reducedAsciiLoader(object):
	
	mainGui = None
	asciiFilename = ''
	shortAsciiFilename = ''
	
	# used when data comes from ascii file
	col1 = []
	col2 = []
	col3 = []
	col4 = []
	
	# used when data comes from Live Reduced Set
	bigTableData = []
	
	isEnabled = True
	isLiveReduced = False
	
	def __init__(self, mainGui, asciiFilename='', isLiveReduced=False, bigTableData=None):
		
		self.mainGui = mainGui
		self.isLiveReduced = isLiveReduced
		if isLiveReduced:
			self.asciiFilename = 'LAST REDUCED SET'
			self.shortAsciiFilename = 'LAST REDUCED SET'
			self.bigTableData = bigTableData
		else:
			self.asciiFilename = asciiFilename
			self.shortAsciiFilename = self.get_short_ascii_filename(asciiFilename)
			self.retrieve_ascii_data()
		
	def get_short_ascii_filename(self, fullFilename):
		return os.path.basename(fullFilename)
	
	def retrieve_ascii_data(self):
		
		filename = self.asciiFilename
		nbrColumns = 3
		_asciiData = asciiLoader(filename,
		                         nbrColumns=nbrColumns)
		
		[self.col1, self.col2, self.col3, self.col4] = _asciiData.data()
		