""" Connection Module
"""
import httplib2
import parse
from answer import Answer

class Connection(object):
	""" Connection object
	"""
	def __init__(self, settings):
		""" Set up the object

			:param settings: The settings required for the connection to be established
			:type settings: Dict

		"""
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

	def _send_request(self, request_method, path, body='', headers=None):
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
		if not headers:
			headers = {}
		uri = httplib2.urlparse.urljoin(self.host, path)
		try:
			resp, content = self.httpcon.request(uri, request_method,
												 body=body, headers=headers)
		except httplib2.ServerNotFoundError:
			raise
		return resp, content

	def send_delete(self, path):
		""" Send a DELETE request
			
			This request may apply to both a file or a collection (folder).
			In case of a folder, the whole content will be deleted recursively.
			If any resource(file) of the collection can not be deleted, none will !

			:param path: The path (without host) to the resource to delete
			:type path: String

		"""
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
		try:
			resp, content = self._send_request('HEAD', path, headers=headers)
			return resp
		except httplib2.ServerNotFoundError:
			raise

	def send_get(self, path, headers={}, callback=False):
		""" Send a GET request
			NOTE: callback is not yet implimented. It's purpose is to allow
			the user to specify a callback so that when x percent of the file
			has been retrieved, the callback will be executed. This makes
			allowances for users who may require a progress to be kept track of.

			:param path: The path (without host) to the resource to get
			:type path: String

			:param headers: Additional headers for the request should be added here
			:type headers: Dict

			:param callback: Not yet implimented. This will allow a callback to be added to the method. This is for such uses as keeping track ofupload progress.
			:type callback: Method or Function

		"""
		try:
			resp, content = self._send_request('GET', path, headers=headers)
			return resp, content
		except httplib2.ServerNotFoundError:
			raise

	def send_put(self, path, body, headers={}):
		""" This PUT request will put data files onto a webdav server.
			However, please note that due to the way in which httplib2 sends
			files, it is not currently possible to break a file up into chunks
			and read it in. In other words, the whole file has to be read into
			memory for sending. This could be problematic for large files.

			:param path: The path (without host) to the desired file destination
			:type path: String

			:param body: Body of the request. This is the data which to send to the destination file
			:type body: String

			:param headers: Additional headers for the request may be added here
			:type headers: Dict

		"""
		try:
			resp, content = self._send_request('PUT', path, body=body,
											   headers=headers)
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

