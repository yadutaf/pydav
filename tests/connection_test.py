import unittest
import os
import httplib2
import socket
import mock
import python_webdav.connection

class TestConnection(unittest.TestCase):
    def setUp(self):
        settings = dict(username='wibble',
                        password = 'fish',
                        realm = 'test-realm',
                        port = 80,
                        host = 'http://webdav.example.com/webdav',
                        path = '.')
        self.connection_obj = python_webdav.connection.Connection(settings)

    def tearDown(self):
        pass

    def test_connection_settings(self):
        self.assertEquals(self.connection_obj.username, 'wibble')
        self.assertEquals(self.connection_obj.password, 'fish')
        self.assertEquals(self.connection_obj.realm, 'test-realm')
        self.assertEquals(self.connection_obj.port, 80)
        self.assertEquals(self.connection_obj.host, 'http://webdav.example.com/webdav')
        self.assertEquals(self.connection_obj.path, '.')
        self.assertEquals(type(self.connection_obj.httpcon), type(httplib2.Http()))
        self.assertEquals(self.connection_obj.httpcon.credentials.credentials, [('', 'wibble', 'fish')])

    def test_send_request(self):
        self.connection_obj.host = 'http://localhost/myWebDAV'
        resp, content = self.connection_obj._send_request('GET', '')
        self.assertEquals(resp.status, 200)

    def test_send_get(self):
        self.connection_obj.host = 'http://localhost/myWebDAV'
        path = ''
        resp, content = self.connection_obj.send_get(path)
        self.assertEquals(resp.status, 200)

    def test_send_get_raises_error(self):
        path = 'cake'
        self.assertRaises(httplib2.ServerNotFoundError,
                          self.connection_obj.send_get, path)

    def test_send_put(self):
        self.connection_obj.host = 'http://localhost/myWebDAV'
        path = '/myWebDAV/test_file_post.txt'
        file_to_send = open('test_data/test_file_post.txt', 'r')
        body = file_to_send.read()
        resp, content = self.connection_obj.send_put(path, body=body)
        self.assertTrue(resp.status in [201, 204])

    def test_send_put_raises(self):
        self.connection_obj.host = 'http://imnothere-haghashkddshkahdskhds.com'
        path = '/myWebDAV/test_file_post.txt'
        body = ''
        self.assertRaises(httplib2.ServerNotFoundError,
                          self.connection_obj.send_put, path, body=body)

    def test_send_delete(self):
        self.connection_obj.host = 'http://localhost/myWebDAV'
        path = '/myWebDAV/test_file_post.txt'
        resp, content = self.connection_obj.send_delete(path)
        self.assertTrue(resp.status in [204])

    def test_send_delete_not_there(self):
        self.connection_obj.host = 'http://localhost/myWebDAV'
        path = '/myWebDAV/imnothere'
        resp, content = self.connection_obj.send_delete(path)
        self.assertEquals(resp.status, 404)

    def test_send_delete_raises(self):
        self.connection_obj.host = 'http://imnothere-ahsadhashadshds.com'
        path = '/myWebDAV/test_file_post.txt'
        self.assertRaises(httplib2.ServerNotFoundError,
                          self.connection_obj.send_delete, path)

    def test_send_propget_root(self):
        self.connection_obj.host = 'http://localhost/myWebDAV/'
        path = ''
        resp, content = self.connection_obj.send_propfind(path)

        expected_resp_status = 207
        expected_content = '<?xml version="1.0" encoding="utf-8"?>\n<D:multistatus xmlns:D="DAV:">'
        content_sample = '\n'.join(content.split('\n')[:2])

        self.assertEquals(expected_resp_status, resp.status)
        self.assertEquals(expected_content, content_sample)

    def test_send_propget_file(self):
        self.connection_obj.host = 'http://localhost/myWebDAV/test_file1.txt'
        path = ''
        resp, content = self.connection_obj.send_propfind(path)

        expected_resp_status = 207
        expected_content = '<?xml version="1.0" encoding="utf-8"?>\n<D:multistatus xmlns:D="DAV:">'
        content_sample = '\n'.join(content.split('\n')[:2])

        self.assertEquals(expected_resp_status, resp.status)
        self.assertEquals(expected_content, content_sample)

    def test_send_propget_path(self):
        self.connection_obj.host = 'http://localhost/myWebDAV/'
        path = 'test_dir1/'
        resp, content = self.connection_obj.send_propfind(path)

        expected_resp_status = 207
        expected_content = '<?xml version="1.0" encoding="utf-8"?>\n<D:multistatus xmlns:D="DAV:">'
        content_sample = '\n'.join(content.split('\n')[:2])

        self.assertEquals(expected_resp_status, resp.status)
        self.assertEquals(expected_content, content_sample)

    def test_send_propget_raises_error(self):
        self.connection_obj.host = 'http://nothereabsbdbabsbdabbabsdbashsjh.com'
        path = ''
        self.assertRaises(httplib2.ServerNotFoundError,
                          self.connection_obj.send_propfind, path)

    def test_send_lock(self):
        self.connection_obj.host = 'http://localhost/myWebDAV/'
        path = 'test_file1.txt'
        resp, content, lock = self.connection_obj.send_lock(path)
        lock_fd = open('tst_lock.txt', 'w')
        lock_fd.write(lock.token)
        lock_fd.close()
        self.assertEquals(200, resp.status)
        self.assertTrue(lock.token)

    def test_send_unlock(self):
        self.connection_obj.host = 'http://localhost/myWebDAV/test_file1.txt'
        path = ''
        lock_fd = open('tst_lock.txt', 'r')
        token = lock_fd.read()
        lock_fd.close()
        os.remove('tst_lock.txt')
        lock_token = python_webdav.connection.LockToken(token)
        resp, content = self.connection_obj.send_unlock(path, lock_token)
        self.assertEquals(204, resp.status)

    def test_send_mkcol(self):
        self.connection_obj.host = 'http://localhost/myWebDAV/'
        path = 'wibble/'
        resp, content = self.connection_obj.send_mkcol(path)
        self.assertEquals(201, resp.status)

    def test_send_rmcol(self):
        self.connection_obj.host = 'http://localhost/myWebDAV/'
        path = 'wibble/'
        resp, content = self.connection_obj.send_rmcol(path)
        self.assertEquals(204, resp.status)

    def test_send_copy_same_dir(self):
        self.connection_obj.host = 'http://localhost/myWebDAV'
        path = 'myWebDAV/test_file1.txt'
        destination = 'myWebDAV/temp_file_copy.txt'
        resp, content = self.connection_obj.send_copy(path, destination)
        self.connection_obj.send_delete(destination)
        self.assertEquals(201, resp.status)


class TestProperty(unittest.TestCase):
    def setUp(self):
        self.prop_obj = python_webdav.connection.Property()

    def set_property_test(self):
        self.prop_obj.set_property('wibble', 123)
        self.assertEquals(self.prop_obj.wibble, 123)


class TestClient(unittest.TestCase):
    def setUp(self):
        self.client_obj = python_webdav.connection.Client()

    def test_parse_xml_prop(self):
        xml = '''<?xml version="1.0" encoding="utf-8"?>
<D:multistatus xmlns:D="DAV:">
<D:response xmlns:lp1="DAV:" xmlns:lp2="http://apache.org/dav/props/">
<D:href>/myWebDAV/</D:href>
<D:propstat>
<D:prop>
<lp1:resourcetype><D:collection/></lp1:resourcetype>
<lp1:creationdate>2009-09-02T20:50:58Z</lp1:creationdate>
<lp1:getlastmodified>Wed, 02 Sep 2009 20:50:58 GMT</lp1:getlastmodified>
<lp1:getetag>"31411a-1000-4729e6c869080"</lp1:getetag>
<D:supportedlock>
<D:lockentry>
<D:lockscope><D:exclusive/></D:lockscope>
<D:locktype><D:write/></D:locktype>
</D:lockentry>
<D:lockentry>
<D:lockscope><D:shared/></D:lockscope>
<D:locktype><D:write/></D:locktype>
</D:lockentry>
</D:supportedlock>
<D:lockdiscovery/>
<D:getcontenttype>httpd/unix-directory</D:getcontenttype>
</D:prop>
<D:status>HTTP/1.1 200 OK</D:status>
</D:propstat>
</D:response>
<D:response xmlns:lp1="DAV:" xmlns:lp2="http://apache.org/dav/props/">
<D:href>/myWebDAV/foobag.txt</D:href>
<D:propstat>
<D:prop>
<lp1:resourcetype/>
<lp1:creationdate>2009-09-02T20:31:52Z</lp1:creationdate>
<lp1:getcontentlength>7</lp1:getcontentlength>
<lp1:getlastmodified>Wed, 02 Sep 2009 20:31:52 GMT</lp1:getlastmodified>
<lp1:getetag>"314189-7-4729e2837fe00"</lp1:getetag>
<lp2:executable>F</lp2:executable>
<D:supportedlock>
<D:lockentry>
<D:lockscope><D:exclusive/></D:lockscope>
<D:locktype><D:write/></D:locktype>
</D:lockentry>
<D:lockentry>
<D:lockscope><D:shared/></D:lockscope>
<D:locktype><D:write/></D:locktype>
</D:lockentry>
</D:supportedlock>
<D:lockdiscovery/>
<D:getcontenttype>text/plain</D:getcontenttype>
</D:prop>
<D:status>HTTP/1.1 200 OK</D:status>
</D:propstat>
</D:response>
<D:response xmlns:lp1="DAV:" xmlns:lp2="http://apache.org/dav/props/">
<D:href>/myWebDAV/cake/</D:href>
<D:propstat>
<D:prop>
<lp1:resourcetype><D:collection/></lp1:resourcetype>
<lp1:creationdate>2009-09-02T20:50:58Z</lp1:creationdate>
<lp1:getlastmodified>Wed, 02 Sep 2009 20:50:58 GMT</lp1:getlastmodified>
<lp1:getetag>"314188-1000-4729e6c869080"</lp1:getetag>
<D:supportedlock>
<D:lockentry>
<D:lockscope><D:exclusive/></D:lockscope>
<D:locktype><D:write/></D:locktype>
</D:lockentry>
<D:lockentry>
<D:lockscope><D:shared/></D:lockscope>
<D:locktype><D:write/></D:locktype>
</D:lockentry>
</D:supportedlock>
<D:lockdiscovery/>
<D:getcontenttype>httpd/unix-directory</D:getcontenttype>
</D:prop>
<D:status>HTTP/1.1 200 OK</D:status>
</D:propstat>
</D:response>
</D:multistatus>'''
        #properties = self.client_obj.parse_xml_prop(xml)
        import python_webdav.parse
        parser = python_webdav.parse.Parser()
        parser.parse(xml)
        properties = parser.response_objects
        self.assertEquals(len(properties), 3)
        self.assertEquals(sorted(properties[0].__dict__),
                          sorted({'getetag': u'"31411a-1000-4729e6c869080"',
                                  'status': u'HTTP/1.1 200 OK',
                                  'getlastmodified': u'Wed, 02 Sep 2009 20:50:58 GMT',
                                  'resourcetype': u'collection',
                                  'href': u'/myWebDAV/',
                                  'getcontenttype': u'httpd/unix-directory',
                                  'locks': [],
                                  'executable': None,
                                  'getcontentlength': None,
                                  'creationdate': u'2009-09-02T20:50:58Z'}))
        self.assertEquals(sorted(properties[1].__dict__),
                          sorted({'getetag': u'"314189-7-4729e2837fe00"',
                                  'status': u'HTTP/1.1 200 OK',
                                  'getlastmodified': u'Wed, 02 Sep 2009 20:31:52 GMT',
                                  'resourcetype': 'resource',
                                  'href': u'/myWebDAV/foobag.txt',
                                  'getcontenttype': u'text/plain',
                                  'locks': [],
                                  'executable': u'F',
                                  'getcontentlength': u'7',
                                  'creationdate': u'2009-09-02T20:31:52Z'}))
        self.assertEquals(sorted(properties[2].__dict__),
                          sorted({'getetag': u'"314188-1000-4729e6c869080"',
                                  'status': u'HTTP/1.1 200 OK',
                                  'getlastmodified': u'Wed, 02 Sep 2009 20:50:58 GMT',
                                  'resourcetype': u'collection',
                                  'href': u'/myWebDAV/cake/',
                                  'getcontenttype': u'httpd/unix-directory',
                                  'locks': [],
                                  'executable': None,
                                  'getcontentlength': None,
                                  'creationdate': u'2009-09-02T20:50:58Z'}))

    def test_get_properties(self):
        settings = settings = dict(username='wibble',
                                   password = 'fish',
                                   realm = 'test-realm',
                                   port = 80,
                                   host = 'http://localhost/myWebDAV',
                                   path = 'myWebDAV')
        connection_obj = python_webdav.connection.Connection(settings)

        client = python_webdav.connection.Client()
        client.get_properties = mock.Mock()
        mock_prop1 = MockProperty()
        mock_prop1.john = 'cleese'
        mock_prop1.eric = 'idle'
        mock_prop1.graham = 'chapman'
        mock_prop1.terry = 'gilliam'
        mock_prop1.Terry = 'jones'
        mock_prop1.michael = 'palin'

        client.get_properties.return_value = [mock_prop1]
        properties = ['john', 'eric', 'graham', 'terry', 'Terry', 'michael']
        result_properties = client.get_properties(connection_obj,
                                                  'myWebDAV/test_file1.txt',
                                                  properties=properties)
        result = result_properties[-1]
        self.assertEquals(result.terry, 'gilliam')
        self.assertEquals(result.michael, 'palin')
        self.assertEquals(result.Terry, 'jones')
        self.assertEquals(result.john, 'cleese')
        self.assertEquals(result.graham, 'chapman')
        self.assertEquals(result.eric, 'idle')

    def test_get_property(self):
        settings = settings = dict(username='wibble',
                                   password = 'fish',
                                   realm = 'test-realm',
                                   port = 80,
                                   host = 'http://localhost/myWebDAV',
                                   path = 'myWebDAV')
        connection_obj = python_webdav.connection.Connection(settings)
        client = python_webdav.connection.Client()
        client.get_properties = mock.Mock()
        mock_prop = MockProperty()
        mock_prop.parrot = 'dead'
        client.get_properties.return_value = [mock_prop]
        property_name = 'parrot'
        requested_value = client.get_property(connection_obj,
                                              'myWebDAV/test_file1.txt',
                                              property_name)
        self.assertEquals(requested_value, 'dead')

    def test_get_file(self):
        settings = settings = dict(username='wibble',
                                   password = 'fish',
                                   realm = 'test-realm',
                                   port = 80,
                                   host = 'http://localhost/myWebDAV',
                                   path = 'myWebDAV')
        connection_obj = python_webdav.connection.Connection(settings)

        connection_obj.send_get = mock.Mock()
        mock_resp = MockProperty()
        mock_resp.status = 204
        connection_obj.send_get.return_value = (mock_resp, 'Data')
        client = python_webdav.connection.Client()
        requested_value = client.get_file(connection_obj,
                                          'myWebDAV/test_file1.txt',
                                          'local_file.txt')
        self.assertTrue(os.path.exists('local_file.txt'))
        self.assertTrue(os.path.getsize('local_file.txt') > 0)
        file_fd = open('local_file.txt', 'r')
        file_data = file_fd.read()
        file_fd.close()
        os.remove('local_file.txt')
        self.assertEquals(file_data, 'Data')

    def test_send_file(self):
        settings = settings = dict(username='wibble',
                                   password = 'fish',
                                   realm = 'test-realm',
                                   port = 80,
                                   host = 'http://localhost/myWebDAV',
                                   path = 'myWebDAV')
        connection_obj = python_webdav.connection.Connection(settings)
        connection_obj.send_put = mock.Mock()
        mock_resp = MockProperty()
        mock_resp.status = 204
        connection_obj.send_put.return_value = (mock_resp, '')
        client = python_webdav.connection.Client()
        local_file = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                                  'test_data', 'test_file_post.txt')
        resp, contents = client.send_file(connection_obj,
                                          'myWebDAV/test_file_post.txt',
                                          local_file)
        self.assertEquals(resp.status, 204)

    def test_copy_resource(self):
        settings = settings = dict(username='wibble',
                                   password = 'fish',
                                   realm = 'test-realm',
                                   port = 80,
                                   host = 'http://localhost/myWebDAV',
                                   path = 'myWebDAV')
        connection_obj = python_webdav.connection.Connection(settings)
        connection_obj.send_copy = mock.Mock()
        mock_resp = MockProperty()
        mock_resp.status = 204
        connection_obj.send_copy.return_value = (mock_resp, '')
        client = python_webdav.connection.Client()
        resource_uri = 'myWebDAV/test_file1.txt'
        resource_destination = 'myWebDAV/test_file1_copy.txt'
        resp, contents = client.copy_resource(connection_obj, resource_uri,
                                              resource_destination)
        self.assertTrue(resp.status > 200)

    def test_delete_resource(self):
        settings = settings = dict(username='wibble',
                                   password = 'fish',
                                   realm = 'test-realm',
                                   port = 80,
                                   host = 'http://localhost/myWebDAV',
                                   path = 'myWebDAV')
        connection_obj = python_webdav.connection.Connection(settings)
        connection_obj.send_delete = mock.Mock()
        mock_resp = MockProperty()
        mock_resp.status = 204
        connection_obj.send_delete.return_value = (mock_resp, '')
        client = python_webdav.connection.Client()
        resource_uri = 'myWebDAV/test_file1_copy.txt'
        resp, contents = client.delete_resource(connection_obj, resource_uri)
        self.assertTrue(resp.status > 200)

    def test_lock(self):
        settings = settings = dict(username='wibble',
                                   password = 'fish',
                                   realm = 'test-realm',
                                   port = 80,
                                   host = 'http://localhost/myWebDAV',
                                   path = 'myWebDAV')
        connection_obj = python_webdav.connection.Connection(settings)
        connection_obj.send_lock = mock.Mock()
        connection_obj.send_lock.return_value = "lock string"
        client = python_webdav.connection.Client()
        resource_uri = 'myWebDAV/test_file1_copy.txt'
        result = client.get_lock(resource_uri, connection_obj)
        self.assertEquals(result, "lock string")
        self.assertEquals(connection_obj.locks[resource_uri].token, "lock string")

    def test_unlock(self):
        settings = settings = dict(username='wibble',
                                   password = 'fish',
                                   realm = 'test-realm',
                                   port = 80,
                                   host = 'http://localhost/myWebDAV',
                                   path = 'myWebDAV')
        connection_obj = python_webdav.connection.Connection(settings)
        connection_obj.send_unlock = mock.Mock()
        connection_obj.send_unlock.return_value = 200, "OK"
        client = python_webdav.connection.Client()
        resource_uri = 'myWebDAV/test_file1_copy.txt'
        connection_obj.locks[resource_uri] = 'thisisalock'
        result = client.release_lock(resource_uri, connection_obj)
        self.assertFalse(connection_obj.locks.get(resource_uri))
        self.assertEquals(result, 200)

    def test_unlock_returns_false(self):
        settings = settings = dict(username='wibble',
                                   password = 'fish',
                                   realm = 'test-realm',
                                   port = 80,
                                   host = 'http://localhost/myWebDAV',
                                   path = 'myWebDAV')
        connection_obj = python_webdav.connection.Connection(settings)
        connection_obj.send_unlock = mock.Mock()
        connection_obj.send_unlock.return_value = 200, "OK"
        client = python_webdav.connection.Client()
        resource_uri = 'myWebDAV/test_file1_copy.txt'
        result = client.release_lock(resource_uri, connection_obj)
        self.assertFalse(connection_obj.locks.get(resource_uri))
        self.assertEquals(result, False)

#def test_lock(self):
    #connection_obj = python_webdav.connection.Connection(settings)
    #connection_obj.send_lock = mock.Mock()
    #connection_obj.send_lock.return_value = "lock string"
    #client = python_webdav.connection.Client()
    #resource_uri = 'myWebDAV/test_file1_copy.txt'
    #result = client.get_lock(resource_uri
    #assert result == "lock string"
    #assert client.locks == {resource_uri: "lock string"}
    #assert 1 == 2


class MockProperty(object):
    def __init__(self):
        pass


if __name__ == '__main__':
    print "*** Finished Tests ***"