import python_webdav
import optparse
import sys

class DebugWebdav(object):
    def __init__(self, server, path, username, password):
        self.server = server
        self.path = path

        settings = {'host': server,
                    'path': path,
                    'username': username,
                    'password': password,
                    'port':80,
                    'realm': ''}


    def put_test(self):
        python_webdav.connection.Connection()


if __name__ == '__main__':
    op = optparse.OptionParser()
    op.add_option('-s', '--server')
    op.add_option('-p', '--path')


    opts, args = op.parse_args(sys.argv)
    path = opts.path
    server = opts.server

    debugger = DebugWebdav(server, path)