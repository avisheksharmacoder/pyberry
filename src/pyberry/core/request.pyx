# cython: language_level=3
import cython

cdef class Request:

    def __init__(self, scope):
        self.scope = scope

    @property
    def method(self) -> str:
        return self.scope.method

    @property
    def path(self) -> str:
        return self.scope.path

    @property
    def query_string(self) -> str:
        return self.scope.query_string
        
    @property
    def headers(self) -> dict:
        return self.scope.headers
