from PyQt4 import QtGui
from reduced_ascii_loader import reducedAsciiLoader

class stitchingAsciiWidgetObject(object):

	loadedAsciiArray = []
	tableUi = None
	
	def __init__(self, mainGui, loadedAscii):
		
		self.loadedAsciiArray.append(loadedAscii)
		self.tableUi = mainGui.ui.reducedAsciiDataSetTable
		
	def addData(self, newLoadedAscii):
		
		rowOfThisFile = self.getRowOfThisFile(newLoadedAscii)
		if rowOfThisFile == -1:
			#add row
			self.loadedAsciiArray.append(newLoadedAscii)
		else:
			# replace
			self.loadedAsciiArray[rowOfThisFile] = newLoadedAscii
		
	def getRowOfThisFile(self, loadedAscii):
		
		newFilename = loadedAscii.asciiFilename

		nbrRow = len(self.loadedAsciiArray)
		for i in range(nbrRow):
			_tmpObject = self.loadedAsciiArray[i]
			_name = _tmpObject.asciiFilename
			
			if _name == newFilename:
				return i
			
		return -1
			
	def updateDisplay(self):
		
		self.tableUi.clearContents()
		nbrRow = len(self.loadedAsciiArray)
		for i in range(nbrRow):
			self.tableUi.removeRow(i)
		
		for i in range(nbrRow):
			
			_object = self.loadedAsciiArray[i]

			self.tableUi.insertRow(i)

			
			_item = QtGui.QTableWidgetItem(str(_object.shortAsciiFilename))
			self.tableUi.setItem(i,0,_item)
			
			_widget = QtGui.QCheckBox()
			_widget.setEnabled(True)
			self.tableUi.setCellWidget(i, 1, _widget)
			
		