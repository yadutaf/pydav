""" Connection Module
"""
import httplib2
import parse
from answer import Answer

#TODO
# * detection of the server type
# * detection of the server methods
# * FIXME: some methods are only advertised on existing resource...

class MethodNotAvailable(httplib2.HttpLib2Error): pass

class Connection(object):
	""" Connection object
	"""
	def __init__(self, settings):
		""" Set up the object

			:param settings: The settings required for the connection to be established
			:type settings: Dict

		"""
		if (settings['path'][-1] != "/"):
			settings['path'] = settings['path'] + "/"
		
		# Get network settings
		self.username = settings['username']
		self.password = settings['password']
		self.realm = settings['realm']
		self.host = settings['host']
		self.path = settings['path']
		self.port = settings['port']
		self.locks = {}

		# Make an http object for this connection
		self.httpcon = httplib2.Http()
		self.httpcon.add_credentials(self.username, self.password)
		
		# Detect server capabilities at root
		self._detect_capabilities()
	
	def _send_request(self, request_method, path, body='', headers={}):
		""" Send a request over http to the webdav server

			:param request_method: HTML / WebDAV request method (such as GET or PUT)
			:type request_method: String

			:param path: The path (without host) to the target of the request
			:type path: String

			:param body: Keyword argument. The body of the request method
			:type body: String

			:param headers: Keyword argument. This is where additional headers for the request caan be added
			:type headers: Dict

		"""
		uri = httplib2.urlparse.urljoin(self.host, self.path)
		uri = httplib2.urlparse.urljoin(uri, path)
		try:
			resp, content = self.httpcon.request(uri, request_method,
												 body=body, headers=headers)
		except httplib2.ServerNotFoundError:
			raise
		return resp, content
	
	def _detect_capabilities(self):
		resp, content = self.send_options()
		
		# Get list of supported methods
		if resp['allow']:
			self.methods = resp['allow'].split(", ")
		else:
			self.methods = []
		
		# Try to guess the server type
		if resp['x-sabre-version']:
			self.server = "sabre"
		elif resp['DAV']:
			self.server = "apache"
		else:
			self.server = "generic"
	
	def send_options(self):
		""" Send an OPTION request
			
			Read the server capabilities. Not all servers are able to handle
			partial PUT requests. Some, like SabreDav does via a custom PATCH
			method (TODO: I'm the contributor of this => actually write it :) )

		"""
		
		try:
			resp, content = self._send_request('OPTIONS', "")
			return resp, content
		except httplib2.ServerNotFoundError, err:
			raise
		
	def send_delete(self, path):
		""" Send a DELETE request
			
			This request may apply to both a file or a collection (folder).
			In case of a folder, the whole content will be deleted recursively.
			If any resource(file) of the collection can not be deleted, none will !

			:param path: The path (without host) to the resource to delete
			:type path: String

		"""
		if 'DELETE' not in self.methods: raise MethodNotAvailable()
		try:
			resp, content = self._send_request('DELETE', path)
			return resp, content
		except httplib2.ServerNotFoundError, err:
			raise

	def send_head(self, path, headers={}):
		""" Send a HEAD request.

			:param path: The path (without host) to the resource to get
			:type path: String

			:param headers: Additional headers for the request should be added here
			:type headers: Dict

		"""
		if 'HEAD' not in self.methods: raise MethodNotAvailable()
		try:
			resp, content = self._send_request('HEAD', path, headers=headers)
			return resp
		except httplib2.ServerNotFoundError:
			raise

	def send_get(self, path, headers={}):
		""" Send a GET request
			NOTE: callback is not yet implimented. It's purpose is to allow
			the user to specify a callback so that when x percent of the file
			has been retrieved, the callback will be executed. This makes
			allowances for users who may require a progress to be kept track of.

			:param path: The path (without host) to the resource to get
			:type path: String

			:param headers: Additional headers for the request should be added here
			:type headers: Dict

		"""
		if 'GET' not in self.methods: raise MethodNotAvailable()
		try:
			resp, content = self._send_request('GET', path, headers=headers)
			return resp, content
		except httplib2.ServerNotFoundError:
			raise
	
	def send_put_partial(self, path, body, begin, filesize, headers={}):
		""" This is a wrapper/helper function over send_put. It will generate 
			the "Content-Range" headers to allow partial resource sending over
			the network.
			It will then pass over the control and actual sending to send_put.
			This utility function may be used to add progess support, resume
			file upload, bypass max_upload_size on the server size...

			:param path: The path (without host) to the desired file destination
			:type path: String

			:param body: Body of the request. This is the data which to send to the destination file
			:type  body: String
			
			:param begin: First byte index of the chunk. Included
			:type  begin: Integer
			
			:param filesize: Whole file size
			:type  filesize: Integer

			:param headers: Additional headers for the request may be added here
			:type  headers: Dict

		"""
		
		#compute end:
		end = begin + len(body) - 1
		if end > filesize:
			raise httplib2.ServerNotFoundError
			
		#We have 3 options here:
		# * the server supports the PATCH method (recommended)
		# * the server support partial PUT requests
		# * none of them :/
		
		if self.server == "sabre": #newer versions *may* support PATCH but none partial PUT
			headers['X-Update-Range'] = "bytes "+str(begin)+"-"+str(end)
			return self.send_patch(path, body, headers)
		else: 
			headers['Content-Range'] = "bytes "+str(begin)+"-"+str(end)+"/"+str(filesize)
			return self.send_put(path, body, headers)
	
	def send_patch(self, path, body, headers={}):
		""" This PATCH request will modify existing data files onto a 
		    (Sabre) webdav server.

			:param path: The path (without host) to the desired file destination
			:type  path: String

			:param body: Body of the request. This is the data which to send to the destination file
			:type  body: String

			:param headers: Additional headers for the request may be added here
			:type  headers: Dict

		"""
		#if 'PATCH' not in self.methods: raise MethodNotAvailable()
		headers['Content-Type'] = "application/x-sabredav-partialupdate"
		try:
			resp, content = self._send_request('PATCH', path, body=body, headers=headers)
			return resp, content
		except httplib2.ServerNotFoundError:
			raise
			
	def send_put(self, path, body, headers={}):
		""" This PATCH request will put data files onto a webdav server.
			However, please note that due to the way in which httplib2 sends
			files, the whole file has to be read into memory for sending. 
			This could be problematic for large files.
			If this is a problem, please use send_put_partial multiple times
			instead.

			:param path: The path (without host) to the desired file destination
			:type  path: String

			:param body: Body of the request. This is the data which to send to the destination file
			:type  body: String

			:param headers: Additional headers for the request may be added here
			:type  headers: Dict

		"""
		if 'PUT' not in self.methods: raise MethodNotAvailable()
		try:
			resp, content = self._send_request('PUT', path, body=body, headers=headers)
			return resp, content
		except httplib2.ServerNotFoundError:
			raise

	def send_propfind(self, path, properties=[], maxdepth=1, extra_headers={}):
		""" Send a PROPFIND request

			:param path: Path (without host) to the resource from which the properties are required
			:type path: String

			:param body: The body of the request
			:type body: String

			:param extra_headers: Additional headers for the request may be added here
			:type extra_headers: Dict

		"""
		if 'PROPFIND' not in self.methods: 
			print self.methods
			print "TOTO"
			raise MethodNotAvailable()
		# Build body
		body = '<?xml version="1.0" encoding="utf-8" ?>'
		body += '<D:propfind xmlns:D="DAV:">'
		if properties:
			body += '<D:prop>'
			for prop in properties:
				body += '<D:' + prop + '/>'
			body += '</D:prop>'
		else:
			body += '<D:allprop/>'
		body += '</D:propfind>'
		
		try:
			headers = {}
			if maxdepth > -1: 
				headers['Depth'] = str(maxdepth)
			headers.update(extra_headers)
			resp, content = self._send_request('PROPFIND', path, body=body,
											   headers=headers)
			return resp, Answer(content)
		except httplib2.ServerNotFoundError:
			raise

	def send_proppatch(self, path, properties,extra_headers={}):
		""" Send a PROPPATCH request

			:param path: Path (without host) to the resource from which the properties are required
			:type path: String

			:param body: The body of the request
			:type body: String

			:param extra_headers: Additional headers for the request may be added here
			:type extra_headers: Dict

		"""
		if 'PROPPATCH' not in self.methods: raise MethodNotAvailable()
		body  = '<?xml version="1.0" encoding="utf-8" ?>'
		body += properties.buildProppatch()
		
		try:
			headers = {'Depth':'1'}
			headers.update(extra_headers)
			resp, content = self._send_request('PROPPATCH', path, body=body,
											   headers=headers)
			return resp, Answer(content)
		except httplib2.ServerNotFoundError:
			raise

	def send_lock(self, path):
		""" Send a LOCK request

			:param path: Path (without host) to the resource to lock
			:type path: String

		"""
		if 'LOCK' not in self.methods: raise MethodNotAvailable()
		try:
			body = '<?xml version="1.0" encoding="utf-8" ?>'
			body += '<D:lockinfo xmlns:D="DAV:"><D:lockscope><D:exclusive/>'
			body += '</D:lockscope><D:locktype><D:write/></D:locktype><D:owner>'
			body += '<D:href>%s</D:href>' % httplib2.urlparse.urljoin(
				self.host, path)
			body += '</D:owner></D:lockinfo>'
			resp, content = self._send_request('LOCK', path, body=body)
			lock_token = LockToken(resp['lock-token'])
			return resp, content, lock_token
		except httplib2.ServerNotFoundError:
			raise

	def send_unlock(self, path, lock_token):
		""" Send an UNLOCK request

			:param path: Path (without host) to the resource to unlock
			:type path: String

			:param lock_token: LockToken object retrived while locking the resource
			:type lock_token: LockToken

		"""
		if 'UNLOCK' not in self.methods: raise MethodNotAvailable()
		try:
			headers = {'Lock-Token': lock_token.token}
			body = '<?xml version="1.0" encoding="utf-8" ?>'
			body += '<D:lockinfo xmlns:D="DAV:"><D:lockscope><D:exclusive/>'
			body += '</D:lockscope><D:locktype><D:write/></D:locktype><D:owner>'
			body += '<D:href>%s</D:href>' % httplib2.urlparse.urljoin(
				self.host, path)
			body += '</D:owner></D:lockinfo>'
			resp, content = self._send_request('UNLOCK', path, headers=headers,
											   body=body)
			return resp, content
		except httplib2.ServerNotFoundError:
			raise

	def send_mkcol(self, path):
		""" Send a MKCOL request

			:param path: Path (without host) to the desired place of the new collection
			:type path: String

		"""
		# No control on availability : For reasons I do not know, it is never advertised...
		try:
			resp, content = self._send_request('MKCOL', path)
			return resp, content
		except httplib2.ServerNotFoundError, err:
			raise

	def send_copy(self, path, destination, allow_overwrite=False, maxdepth=-1):
		""" Send a COPY request

			:param path: Path (without host) to the source resource to copy
			:type  path: String

			:param destination: Path (without host) to the destination of the copied resource
			:type  destination: String
						
			:param allow_overwrite: Allow the destination resource to be overwritten if already exists. Defaults to False.
			:type  allow_overwrite: Boolean
			
			:param maxdepth: Specify the maximum depth for the copy. Infinity(-1) by default.
			:type  maxdepth: Integer

		"""
		if 'COPY' not in self.methods: raise MethodNotAvailable()
		try:
			headers = {}
			full_destination = httplib2.urlparse.urljoin(self.host, destination)
			headers['Destination'] = full_destination
			if not allow_overwrite : headers['Overwrite'] = "F"
			if maxdepth > -1       : headers['Depth']     = str(maxdepth)
			resp, content = self._send_request('COPY', path, headers=headers)
			return resp, content
		except httplib2.ServerNotFoundError:
			raise
			
	def send_move(self, path, destination, allow_overwrite=False):
		""" Send a MOVE request

			:param path: Path (without host) to the source resource to copy
			:type  path: String

			:param destination: Path (without host) to the destination of the copied resource
			:type  destination: String
						
			:param allow_overwrite: Allow the destination resource to be overwritten if already exists. Defaults to False.
			:type  allow_overwrite: Boolean
		"""
		try:
			headers = {}
			full_destination = httplib2.urlparse.urljoin(self.host, destination)
			headers['Destination'] = full_destination
			if not allow_overwrite : headers['Overwrite'] = "F"
			resp, content = self._send_request('MOVE', path, headers=headers)
			return resp, content
		except httplib2.ServerNotFoundError:
			raise

class LockToken(object):
	""" LockToken object. This is an object that contains information about a
		lock on a resource or collection
	"""
	def __init__(self, lock_token):
		""" Make a lock token
		"""
		self.token = lock_token

