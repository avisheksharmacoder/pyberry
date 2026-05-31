# cython: language_level=3
from pyberry.core import fastjson
from pyberry.core.response cimport Response

cdef class JSONResponse(Response):
    def __cinit__(self, content, int status = 200, list headers = None):
        cdef bytes body = fastjson.dumps(content)
            
        cdef list _headers = [('content-type', 'application/json')]
        if headers is not None:
            _headers.extend(headers)
            
        self.body = body
        self.status = status
        self.headers = _headers

cdef class HTMLResponse(Response):
    def __cinit__(self, str content, int status = 200, list headers = None):
        cdef bytes body = content.encode('utf-8')
        cdef list _headers = [('content-type', 'text/html')]
        if headers is not None:
            _headers.extend(headers)
            
        self.body = body
        self.status = status
        self.headers = _headers

cdef class PlainTextResponse(Response):
    def __cinit__(self, str content, int status = 200, list headers = None):
        cdef bytes body = content.encode('utf-8')
        cdef list _headers = [('content-type', 'text/plain')]
        if headers is not None:
            _headers.extend(headers)
            
        self.body = body
        self.status = status
        self.headers = _headers

class HTTPException(Exception):
    def __init__(self, int status_code, str detail = None):
        self.status_code = status_code
        self.detail = detail or "HTTP Error"
        super().__init__(f"{self.status_code}: {self.detail}")
