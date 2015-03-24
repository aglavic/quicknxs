from xml.dom import minidom

class LoadSFConfigXmlFile (object):
	
	sf_gui = None
	loading_status = False
	filename = ''
	dom = None
	
	def __init__(cls, parent=None, filename=''):
		cls.sf_gui = parent
		cls.filename = filename
		cls.parseXML()

	def parseXML(cls):
		_filename = cls.filename
		try: 
			cls.dom = minidom.parse(_filename)
		except:
			return
		cls.loading_status = True
		
	def getDom(cls):
		return cls.dom
	
	def getLoadingStatus(cls):
		return cls.loading_status