import httplib2
from lxml import etree

class ResourceProperties(object):
	""" ResourceProperties Object for storing information about WebDAV resource
		Stored at a given path
	"""
	
	path  = ""
	props = {}
	dels  = []
	href  = ""
	status = ""
	
	def __init__(self):
		""" Set up the object
		"""
	
	def __getitem__(self, name):
		return self.props[name]
	
	def __setitem__(self, name, value):
		if hasattr(self, name):
			object.__setattr__(self, name, value)
			return
		self.props[name] = value
		if self.dels.count(name):
			self.dels.remove(name) #make sure has not been marked for deletion
		
	def __delitem__(self, name):
		del self.props[name]
		self.dels.append(name)
		
	def __iter__(self):
		return props.__iter__()
	
	def has_key(self, key):
		return key in self.props
		
	def __len__(self):
		return props.__len__()

class Lock(object):
    """ This is an object for storing resource lock information
    """
    def __init__(self):
        """ There are no inputs for this object but self.locktype and
            self.lockscope will be initialised to None when the instance is
            created
        """
        self.locktype  = None
        self.lockscope = None

#TODO: implement a property cache

class Answer(object):
	""" Answer parses and stores xml answers. It also
		contains helpers to build some requests
    """
	def __init__(self, xml):
		""" launch an answer parse
			
			:param xml: raw XML answer
			:type  xml: String
		"""
		
		self.props = []
		parser = etree.XMLParser(remove_blank_text=True)
		root = etree.XML(xml, parser)
		
		for response in root.iter("{DAV:}response"):
			if isinstance(response.tag, basestring):#make sure it is an elem
				prop = ResourceProperties()
				prop.href = response.findtext(".//{DAV:}href")
				prop.status = response.findtext(".//{DAV:}status")
				for p in response.find(".//{DAV:}prop").getchildren():
					tag = p.tag[6:]
					if tag == "resourcetype":
						prop[tag] = "collection"#fixme: do the actual detection. In practice, this is always true
					else:
						prop[tag] = p.text
				self.props.append(prop)


