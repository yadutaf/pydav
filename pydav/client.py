""" Client Module
"""

from connection import Connection
from answer import Answer
import os
import urllib
import httplib2#fimxe: this is imported only for exceptions

class Client(object):
	""" This class is for interacting with webdav. Its main purpose is to be
		used by the client.py module but may also be used by developers
		who wish to use more direct webdav access.
	"""
	def __init__(self, settings):
		""" Set up the object

			:param settings: The settings required for the connection to be established
			:type settings: Dict

		"""
		self.connection = Connection(settings)
		if('maxChunkSize' in settings):
			self._maxChunkSize = settings['maxChunkSize']
		else:
			self._maxChunkSize = 100000000#100MB
	
	def mkdir(self, path):
		self.connection.send_mkcol(urllib.quote(path))

	def getProperties(self, path, maxdepth=0, properties=[]):
		""" Get a list of property objects

			:param path: the path of the resource / collection minus the host section
			:type path: String

			:param properties: list of property names to get. If left empty, will get all
			:type properties: List
			
			:param maxdepth: Specify the maximum depth for the copy. 1 by default.
			:type  maxdepth: Integer

			Returns a list of ResourceProperties.

		"""
		
		path = urllib.quote(path)
		if path and path[-1] != '/':
			path += '/'

		resp, prop = self.connection.send_propfind(path, properties, maxdepth)
		if resp.status >= 200 and resp.status < 300:
			return prop
		else:
			raise httplib2.HttpLib2Error([resp, prop])

	def getProperty(self, path, property_name):
		""" Get a property object

			:param path: the path of the resource / collection minus the host section
			:type  path: String

			:param property_name: Property name
			:type  property_name: String

			Returns the property value as a string

		"""
		property_obj = self.get_properties(self.connection, path, 1
										   [property_name])[0]
		return property_obj[property_name]
	
	def setProperties(self, properties):
		""" Set the properties of a resource
			
			:param properties: Property holder. It also holds the resource relatives Path on the server
			:type  properties: ResourceProperties

			Returns a list of ResourceProperties.

		"""
		
		path = urllib.quote(properties.href)

		resp, prop = self.connection.send_proppatch(path, properties)
		if resp.status >= 200 and resp.status < 300:
			return prop
		else:
			raise httplib2.HttpLib2Error([resp, prop])
	
	def getFile(self, path, local_file_name,
				 extra_headers={}):
		""" Download file

			:param path: the path of the resource / collection minus the host section
			:type path: String

			:param local_file_name: Local file where the resource will be saved
			:type local_file_name: String

			:param extra_headers: Add any extra headers for the request here
			:type extra_headers: Dict

		"""
		path = urllib.quote(path)
		resp, data = self.connection.send_get(path, headers=extra_headers)
		file_fd = open(local_file_name, 'w')
		file_fd.write(data)
		file_fd.close()
	
	def _sendFileChunk(self, path, local_file_path, begin, chunksize, filesize, extra_headers={}):
		local_file_fd = open(local_file_path, 'r')
		local_file_fd.seek(begin, os.SEEK_SET)
		data = local_file_fd.read(chunksize)
		
		resp, contents = self.connection.send_put_partial(path, data, begin, filesize, headers=extra_headers)
		return resp, contents
	
	def sendFileChunk(self, path, local_file_path, begin, chunksize, extra_headers={}):
		""" Send file chunk. This method may be used to resume uploads or
			send big files in multiple chunks.

			:param path: the path of the resource / collection minus the host section
			:type  path: String

			:param local_file_path: the path of the local file
			:type  local_file_path: String

			:param extra_headers: Additional headers may be added here
			:type  extra_headers: Dict
		"""
		filesize = os.stat(local_file_path).st_size
		path = urllib.quote(path)
		return self._sendFileChunk(path, local_file_path, begin, chunksize, filesize, extra_headers)
	
	def sendFile(self, path, local_file_path, initial_offset=0, extra_headers={}):
		""" Send file

			:param path: the path of the resource / collection minus the host section
			:type  path: String

			:param local_file_path: the path of the local file
			:type  local_file_path: String
			
			:param local_file_path: initial offset in the file. Nice to resume :)
			:type  local_file_path: Integer

			:param extra_headers: Additional headers may be added here
			:type  extra_headers: Dict

		"""
		filesize = os.stat(local_file_path).st_size
		path = urllib.quote(path)
		
		if filesize < self._maxChunkSize and not initial_offset:#small enough file. I keep it separate as this is the safest upload method
			local_file_fd = open(local_file_path, 'r')
			local_file_fd.seek(initial_offset, os.SEEK_SET)
			data = local_file_fd.read()
			resp, contents = self.connection.send_put(path, data, headers=extra_headers)
			return resp, contents
		
		#big files and resume cases
		local_file_fd = open(local_file_path, 'r')
		local_file_fd.seek(initial_offset, os.SEEK_SET)
		cursor = initial_offset
		while cursor < filesize:
			chunksize = min(filesize-cursor, self._maxChunkSize)
			data = local_file_fd.read(chunksize)
			resp, contents = self._sendFileChunk(path, local_file_path, cursor, chunksize, filesize, extra_headers)
			cursor += chunksize
		
		return resp, contents#of the last one :/
						

	def cp(self, resource_path, resource_destination, allow_overwrite=False, maxdepth=-1):
		""" Copy a resource from point a to point b on the server

			:param resource_path: Path to the required resource
			:type  resource_path: String

			:param resource_destination: Destination of the copied resource
			:type  resource_destination: String
			
			:param allow_overwrite: Allow the destination resource to be overwritten if already exists. Defaults to False.
			:type  allow_overwrite: Boolean
			
			:param maxdepth: Specify the maximum depth for the copy. Infinity(-1) by default.
			:type  maxdepth: Integer

		"""
		resp, contents = self.connection.send_copy(resource_path,
		                                           resource_destination,
		                                           allow_overwrite,
		                                           maxdepth)
		return resp, contents
	
	def mv(self, resource_path, resource_destination, allow_overwrite=False):
		""" Moves a resource from point a to point b on the server

			:param resource_path: Path to the required resource
			:type  resource_path: String

			:param resource_destination: Destination of the copied resource
			:type  resource_destination: String
			
			:param allow_overwrite: Allow the destination resource to be overwritten if already exists. Defaults to False.
			:type  allow_overwrite: Boolean

		"""
		resp, contents = self.connection.send_copy(resource_path,
		                                           resource_destination,
		                                           allow_overwrite)
		return resp, contents

	def ls(self, path, maxdepth=1):
		""" List content of a collection. May do it recursively if supported on the server side (not SABRE for instance ...)
			This is a helper function in top of getProperties. It maps all set of
			properties to the corresponding "href"

			:param path: Base path
			:type  path: String
			
			:param maxdepth: Specify the maximum depth for the copy. 1 by default.
			:type  maxdepth: Integer

		"""
		props = self.getProperties(path, maxdepth).props
		files = {}
		for prop in props:
			files[prop.href] = prop
		return files
	
	def rm(self, path):
		""" Delete resource. The resource may either be a collection (folder)
			or a file. If this is a folder, all content will be deleted recursively.
			In case at least one of the subresource may not be deleted, none will.

			:param path: URI of the resource
			:type path: String

		"""
		resp, contents = self.connection.send_delete(path)
		return resp, contents
	
	def rmdir(self,  path):
		""" Convenient Alias for deleteResource. Removes *all* content recursively !
		
			param path: URI of the resource
			:type path: String
		"""
		return self.deleteResource(path)

# ------------------------------------------- NOT YET IMPLEMENTED -------------------------------- #
	def getLock(self, path):
		""" Get a file lock

			:param path: the path of the resource / collection minus the host section
			:type path: String

		"""
		lock = self.connection.send_lock(path)
		self.connection.locks[path] = LockToken(lock)
		return lock

	def releaseLock(self, path):
		""" Release a file lock

			:param path: the path of the resource / collection minus the host section
			:type path: String

		"""
		# If there's not a lock recorded, return false for now. We should
		# really raise an exception to make it more obvious.
		if not self.connection.locks.get(path):
			return False
		resp, cont = self.connection.send_unlock(path, self.connection.locks[path])
		# remove from our dictionary if the lock was released successfully
		if resp >= 200 and resp < 300:
			del self.connection.locks[path]
		return resp
