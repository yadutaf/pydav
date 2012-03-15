import httplib2
from lxml import etree
import time

class ResourceProperties(object):
	""" ResourceProperties Object for storing information about WebDAV resource
		Stored at a given path
		
		The goal of this class is store the properties and record their editions/deletions
		to help generate the proppatch command. It is able to handle any property name the only assumption
		being that it belongs to the "DAV:" namespace. Some properties have a builtin special behaviour. "resourcetype", "getcontentlength"
		, "getlastmodified" and "creationdate" for instance.
		
		A list of properties included in the DAV namespace includes :
		* creationdate (ISO 8601)
		* displayname
		* getcontentlanguage
		* getcontentlength => TODO: implement a way to refresh it...
		* getcontenttype
		* getetag
		* getlastmodified (ISO 8601)
		* lockdiscovery
	"""
	
	def __init__(self, prop):
		""" Set up the object
			
			:param prop: XML response Node to be parsed as initial data
			:type  prop: XML node
		"""
		#init local data
		self.path  = ""
		self.props = {}
		self.dels  = []
		self.edits = []
		self.href  = ""
		self.status = ""
		
		#init the object from the response object
		self.href = prop.findtext(".//{DAV:}href")
		self.status = prop.findtext(".//{DAV:}status")
		for p in prop.find(".//{DAV:}prop").getchildren():
			tag = p.tag[6:]
			if tag == "resourcetype":
				if len(p.getchildren()) > 0 and p.getchildren()[0].tag=="{DAV:}collection":
					self.props[tag] = "collection"
				else:
					self.props[tag] = "resource"
			else:
				self.props[tag] = p.text
	
	def buildDate(self, tuple_time):
		tuple_time = time.gmtime(tuple_time)
		return time.strftime("%Y-%m-%dT%H:%M:%S", tuple_time)
	
	def buildProppatch(self):
		""" Build the "propertyupdate" part of the PROPPATCH command
		"""
		xml = '<D:propertyupdate xmlns:D="DAV:"xmlns:Z="http://www.w3.com/standards/z39.50/">'
		#commit editions
		if len(self.edits):
			xml += '<D:set><D:prop>'
			for name in self.edits:
				xml += '<S:'+name+'>'
				xml += self.props[name]
				xml += '</S:'+name+'>'
			xml += '</D:prop></D:set>'
		#commit editions
		if len(self.dels):
			xml += '<D:remove><D:prop>'
			for name in self.dels:
				ns = 'S' if name.startswith("synchro") else 'D'
				xml += '<S:'+name+'/>'
			xml += '</D:prop></D:remove>'
		xml += '</D:propertyupdate>'
		#reset tracker
		self.edits = []
		self.dels  = []
		#return
		return xml
			
			 
	
	def __getitem__(self, name):
		return self.props[name]
	
	def __setitem__(self, name, value):
		if name == "resourcetype":     return #this is a non-sense to change the resource type !
		if name == "getcontentlength": return #this is a non-sense to change the content length !

		self.props[name] = value
		if not self.edits.append(name):#record edition
			self.edits.append(name)
		if self.dels.count(name):#record NO delete
			self.dels.remove(name)
		
	def __delitem__(self, name):
		if name == "displayname":      return #it is forbidden to remove this header !
		if name == "creationdate":     return #it is forbidden to remove this header !
		if name == "resourcetype":     return #it is forbidden to remove this header !
		if name == "getcontentlength": return #this is a non-sense to change the content length !
		
		del self.props[name]
		if not self.dels.append(name):#record deletion
			self.dels.append(name)
		if self.edits.count(name):#record NO edited
			self.edits.remove(name)
		
	def __iter__(self):
		return self.props.__iter__()
	
	def has_key(self, key):
		return key in self.props
		
	def __len__(self):
		return self.props.__len__()

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
				prop = ResourceProperties(response)
				self.props.append(prop)
				


