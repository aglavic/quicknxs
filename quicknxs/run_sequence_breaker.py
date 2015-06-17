class RunSequenceBreaker(object):
	
	final_list = None
	str_final_list = None
	
	def __init__(cls, run_sequence=None):
		final_list = []
		str_final_list = []
		if run_sequence is None:
			return
		try:
			# remove white spaces
			_run_sequence = run_sequence.replace(" ", "")
			
			if _run_sequence == "":
				cls.final_list = [-1]
				cls.str_final_list = ['']
				return
			
			# coma separated
			coma_separated = _run_sequence.split(',')
			
			for _element in coma_separated:
				hypen_separated = _element.split('-')
				nbr_element = len(hypen_separated)
				if nbr_element > 1:
					_range = cls.getRangeBetweenTwoNumbers(hypen_separated[0], hypen_separated[1])
					for _r in _range:
						final_list.append(_r)
						str_final_list.append(str(_r))
						
				else:
					final_list.append(int(hypen_separated[0]))
					str_final_list.append(str(hypen_separated[0]))
		except:
			final_list = [-2]
			str_final_list = ['']
		cls.final_list = final_list
		cls.str_final_list = str_final_list
	
	def getRangeBetweenTwoNumbers(cls, num1, num2):
		_num1 = int(num1)
		_num2 = int(num2)

		from_num = min([_num1, _num2])
		to_num = max([_num1, _num2])
		return range(from_num, to_num+1)
	
	def getFinalList(cls):
		return cls.final_list
	
	def getStringFinalList(cls):
		return cls.str_final_list
		