import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

class MockRSGIScope:
    def __init__(self, method="GET", path="/", query_string="", proto="http", headers=None):
        self.method = method
        self.path = path
        self.query_string = query_string
        self.proto = proto
        self.headers = headers or {}

class MockRSGIProtocol:
    def __init__(self, body=b""):
        self.body = body
        self.response_status = None
        self.response_headers = None
        self.response_body = None
        self.response_called = False

    async def __call__(self):
        return self.body
        
    def response_str(self, status, headers, body):
        self.response_status = status
        self.response_headers = headers
        self.response_body = body
        self.response_called = True

@pytest.fixture
def mock_scope():
    return MockRSGIScope()

@pytest.fixture
def mock_proto():
    return MockRSGIProtocol()
