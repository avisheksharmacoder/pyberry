import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

class MockRSGIScope:
    def __init__(self, method="GET", path="/", query_string="", proto="http", headers=None, client=None):
        self.method = method
        self.path = path
        self.query_string = query_string
        self.proto = proto
        self.headers = headers or {}
        self.client = client or ["127.0.0.1", 12345]

class MockRSGIStream:
    def __init__(self):
        self.chunks = []
    
    async def send_bytes(self, data):
        self.chunks.append(data)

class MockRSGIProtocol:
    def __init__(self, body=b""):
        self.body = body
        self.response_status = None
        self.response_headers = None
        self.response_body = None
        self.response_called = False
        self.stream = None

    async def __call__(self):
        return self.body
        
    def response_str(self, status, headers, body):
        self.response_status = status
        self.response_headers = headers
        self.response_body = body
        self.response_called = True

    def response_bytes(self, status, headers, body):
        self.response_status = status
        self.response_headers = headers
        self.response_body = body
        self.response_called = True

    def response_stream(self, status, headers):
        self.response_status = status
        self.response_headers = headers
        self.response_called = True
        self.stream = MockRSGIStream()
        return self.stream

@pytest.fixture
def mock_scope():
    return MockRSGIScope()

@pytest.fixture
def mock_proto():
    return MockRSGIProtocol()
