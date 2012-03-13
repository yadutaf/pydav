import unittest
import os
import mock
import python_webdav.client as webdav_client

class TestClient(unittest.TestCase):
    """ Test case for the client
    """
    def setUp(self):
        """ setUp
        """
        self.client = webdav_client.Client('http://localhost/myWebDAV',
                                           webdav_path = '.',
                                           realm = 'test-realm',
                                           port = 80)
        self.client.set_connection(username='wibble', password='fish')

    def tearDown(self):
        """ tearDown
        """
        pass

    def test_download_file(self):
        """ Download a simple file
        """
        file_path = 'myWebDAV/test_file1.txt'
        dest_path = os.path.join(os.path.dirname(__file__), 'test_data')
        resp, content = self.client.download_file(file_path,
                                                  dest_path=dest_path)
        written_file = os.path.join(dest_path, 'test_file1.txt')
        self.assertTrue(os.path.exists(written_file))
        file_fd = open(written_file, 'r')
        data = file_fd.read()
        file_fd.close
        os.remove(written_file)
        self.assertEquals(data, 'Test file\n')

    def test_chdir(self):
        """ test_chdir
        """
        path1 = ''
        path2 = '/'
        path3 = '/hello'
        path4 = 'hello/'

        self.client.connection.path = path1
        self.client.chdir('..')
        self.assertEquals(self.client.connection.path, '/')

        self.client.connection.path = path2
        self.client.chdir('..')
        self.assertEquals(self.client.connection.path, '/')

        self.client.connection.path = path3
        self.client.chdir('..')
        self.assertEquals(self.client.connection.path, '/')

        self.client.connection.path = path4
        self.client.chdir('..')
        self.assertEquals(self.client.connection.path, '/')

        self.client.connection.path = path1
        self.client.chdir('wibble')
        self.assertEquals(self.client.connection.path, '/wibble')

        self.client.chdir('wibble')
        self.assertEquals(self.client.connection.path, '/wibble/wibble')

        self.client.chdir('/foo/bar')
        self.assertEquals(self.client.connection.path, '/foo/bar')

    def test_ls(self):
        self.client.connection.path = 'myWebDAV'
        self.client.connection.host = 'http://localhost/'
        result = self.client.ls()

        expected_result = [['/mywebDAV/','httpd/unix-directory','Wed, 21 Jul 2010 11:21:49 GMT'],
                           ['/mywebDAV/newpath/','httpd/unix-directory',''],
                           ['/myWebDAV/test_dir1/','httpd/unix-directory',''],
                           ['/myWebDAV/test_file1.txt','text/plain','Thu, 03 Sep 2009 18:57:25 GMT'],
                           ['/myWebDAV/test_file2.txt','text/plain',''],
                           ['/myWebDAV/test_file_post.txt','text/plain','']]
        self.assertAlmostEquals(1, 2)


    def test_mkdir(self):
        """ test_mkdir

            Test for making directories (collections)
        """
        self.client.connection.send_mkcol = mock.Mock()
        self.client.connection.path = 'myWebDAV'
        self.client.mkdir('newpath')
        self.assertEquals(self.client.connection.send_mkcol.call_args_list,
                          [(('myWebDAV/newpath',), {})])

    def test_rmdir(self):
        """ test_rmdir

            Test for removing directories
        """
        self.assertTrue(False)

    def test_pwd(self):
        """ test_pwd

            Test that the pwd method returns the current path stored in the
            connection object
        """
        self.client.connection.path = "/myWebDAV/monty"
        result = self.client.pwd()
        self.assertEquals(result, "/myWebDAV/monty")

    def test_pwd_none(self):
        """ test_pwd

            Test that the pwd method returns None when a connection has not been
            set up yet.
        """
        self.client.connection= None
        result = self.client.pwd()
        self.assertEquals(result, None)