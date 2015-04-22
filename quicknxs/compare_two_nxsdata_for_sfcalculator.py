class CompareTwoNXSDataForSFcalculator(object):
	'''
	will return -1, 0 or 1 according to the position of the nexusToPosition in relation to the 
	nexusToCompareWith based on the following criteria
	#1: number of attenuators (ascending order)
	#2: lambda requested (descending order)
	#3: S2W (ascending order)
	#4: S2H (descending order)
	#5 if everything up to this point is identical, return 0
	'''
	nexusToCompareWithRun = None
	nexusToPositionRun = None
	resultComparison = 0
	
	def __init__(cls, nxsdataToCompareWith, nxsdataToPosition):
		cls.nexusToCompareWithRun = nxsdataToCompareWith.active_data.nxs.getRun()
		cls.nexusToPositionRun = nxsdataToPosition.active_data.nxs.getRun()
				
		compare1 = cls.compareParameter('LambdaRequest','descending')
		if compare1 != 0:
			cls.resultComparison = compare1
			return
		
		compare2 = cls.compareParameter('vATT','ascending')
		if compare2 != 0:
			cls.resultComparison = compare2
			return
		
		compare3 = cls.compareParameter('SiHWidth','ascending', param_backup='S2HWidth')
		if compare3 != 0:
			cls.resultComparison = compare3
			return
		
		compare4 = cls.compareParameter('SiVHeight','ascending', param_backup = 'S2VHeight')
		if compare4 != 0:
			cls.resultComparison = compare4
			return
		
		compare5 = cls.compareParameter('S1HWidth','ascending')
		if compare5 != 0:
			cls.resultComparison = compare5
			return
		
		compare6 = cls.compareParameter('S1VHeight','ascending')
		if compare6 != 0:
			cls.resultComparison = compare6
			return
		
		
	def compareParameter(cls, param, order, param_backup=None):
		_nexusToCompareWithRun = cls.nexusToCompareWithRun
		_nexusToPositionRun = cls.nexusToPositionRun
		
		try:
			_paramNexusToCompareWith = float(_nexusToCompareWithRun.getProperty(param).value[0])
			_paramNexusToPosition = float(_nexusToPositionRun.getProperty(param).value[0])
		except:
			_paramNexusToCompareWith = float(_nexusToCompareWithRun.getProperty(param_backup).value[0])
			_paramNexusToPosition = float(_nexusToPositionRun.getProperty(param_backup).value[0])
			
		if order == 'ascending':
			resultLessThan = -1
			resultMoreThan = 1
		else:
			resultLessThan = 1
			resultMoreThan = -1
		
		if (_paramNexusToPosition < _paramNexusToCompareWith):
			return resultLessThan
		elif (_paramNexusToPosition > _paramNexusToCompareWith):
			return resultMoreThan
		else:
			return 0
		
	def result(cls):
		return cls.resultComparison