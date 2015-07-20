import numpy as np

class asciiLoader(object):
	
	filename = ''
	dataCol1 = []
	dataCol2 = []
	dataCol3 = []
	dataCol4 = []
	
	def __init__(self, filename, nbrColumns=3):
		
		if nbrColumns is not 3:
			raise nbrColumnError('only 3 supported for now!')
		
		data = np.genfromtxt(filename, dtype=float, comments='#')
		                    
		self.dataCol1 = data[:,0]
		self.dataCol2 = data[:,1]
		self.dataCol3 = data[:,2]
#		self.dataCol4 = data[:,3]
		
	def data(self):
		
		return [self.dataCol1, self.dataCol2, self.dataCol3, self.dataCol4]