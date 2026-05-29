import json
from pyberry.core.response import Response

class JSONResponse(Response):
    def __init__(self, content, status: int = 200, headers: list = None):
        body = json.dumps(content).encode('utf-8')
        _headers = [('content-type', 'application/json')]
        if headers:
            _headers.extend(headers)
        super().__init__(body=body, status=status, headers=_headers)

class HTMLResponse(Response):
    def __init__(self, content: str, status: int = 200, headers: list = None):
        body = content.encode('utf-8')
        _headers = [('content-type', 'text/html')]
        if headers:
            _headers.extend(headers)
        super().__init__(body=body, status=status, headers=_headers)

class PlainTextResponse(Response):
    def __init__(self, content: str, status: int = 200, headers: list = None):
        body = content.encode('utf-8')
        _headers = [('content-type', 'text/plain')]
        if headers:
            _headers.extend(headers)
        super().__init__(body=body, status=status, headers=_headers)

class HTTPException(Exception):
    def __init__(self, status_code: int, detail: str = None):
        self.status_code = status_code
        self.detail = detail or "HTTP Error"
        super().__init__(f"{self.status_code}: {self.detail}")
