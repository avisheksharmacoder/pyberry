# cython: language_level=3
import cython
import json

cdef class Request:

    def __init__(self, scope, proto=None):
        self.scope = scope
        self.proto = proto
        self._body = None

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

    async def body(self):
        if self._body is None:
            if self.proto is not None:
                self._body = await self.proto()
            else:
                self._body = b""
        return self._body

    async def json(self):
        body_bytes = await self.body()
        if not body_bytes:
            return {}
        return json.loads(body_bytes)
