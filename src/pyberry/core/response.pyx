# cython: language_level=3
import cython

cdef class Response:

    def __init__(self, body=b"", status=200, headers=None):
        self.body = body
        self.status = status
        if headers is None:
            self.headers = [('content-type', 'text/plain')]
        else:
            self.headers = headers
