# cython: language_level=3
import cython

from pyberry.config import config

cdef class Response:

    def __cinit__(self, body=b"", int status=200, list headers=None):
        self.body = body
        self.status = status
        if headers is None:
            self.headers = [('content-type', 'text/plain')]
        else:
            self.headers = headers
            
        if config.security_headers:
            self.headers.extend(config.security_headers)
