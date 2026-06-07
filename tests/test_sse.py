import pytest
import asyncio
from unittest.mock import Mock, patch
from pyberry.core.rsgi import app, router
from pyberry.core.responses import SSEResponse
from conftest import MockRSGIScope, MockRSGIProtocol
from pyberry.db import db

@pytest.fixture(autouse=True)
def mock_db_init(monkeypatch):
    monkeypatch.setattr(db, "init_db", Mock())

@pytest.mark.asyncio
async def test_sse_basic_string(mock_proto):
    async def generator():
        yield "hello"
        yield "world"
        
    def handler(req):
        return SSEResponse(generator())
        
    router.add_python_route("GET", "/sse_str", handler)
    scope = MockRSGIScope(method="GET", path="/sse_str", proto="http")
    
    await app(scope, mock_proto)
    
    assert mock_proto.response_called
    assert mock_proto.response_status == 200
    assert ('content-type', 'text/event-stream') in mock_proto.response_headers
    assert ('cache-control', 'no-cache') in mock_proto.response_headers
    assert ('connection', 'keep-alive') in mock_proto.response_headers
    
    assert mock_proto.stream is not None
    assert mock_proto.stream.chunks == [
        b"data: hello\n\n",
        b"data: world\n\n"
    ]

@pytest.mark.asyncio
async def test_sse_dictionary_json(mock_proto):
    async def generator():
        yield {"id": 1, "status": "ok"}
        
    def handler(req):
        return SSEResponse(generator())
        
    router.add_python_route("GET", "/sse_dict", handler)
    scope = MockRSGIScope(method="GET", path="/sse_dict", proto="http")
    
    await app(scope, mock_proto)
    
    assert mock_proto.stream.chunks == [
        b'data: {"id":1,"status":"ok"}\n\n'
    ]

@pytest.mark.asyncio
async def test_sse_multiline_string(mock_proto):
    async def generator():
        yield "line1\nline2\nline3"
        
    def handler(req):
        return SSEResponse(generator())
        
    router.add_python_route("GET", "/sse_multi", handler)
    scope = MockRSGIScope(method="GET", path="/sse_multi", proto="http")
    
    await app(scope, mock_proto)
    
    assert mock_proto.stream.chunks == [
        b"data: line1\ndata: line2\ndata: line3\n\n"
    ]

@pytest.mark.asyncio
async def test_sse_generator_exception(mock_proto, capsys):
    async def generator():
        yield "ok"
        raise ValueError("App Bug")
        
    def handler(req):
        return SSEResponse(generator())
        
    router.add_python_route("GET", "/sse_error", handler)
    scope = MockRSGIScope(method="GET", path="/sse_error", proto="http")
    
    await app(scope, mock_proto)
    
    # It should have sent the first chunk before crashing
    assert mock_proto.stream.chunks == [b"data: ok\n\n"]
    
    # We should see the traceback in stdout/stderr
    captured = capsys.readouterr()
    assert "ValueError: App Bug" in captured.err

@pytest.mark.asyncio
async def test_sse_client_disconnect(mock_proto):
    class BrokenStream:
        async def send_bytes(self, data):
            raise ConnectionError("Client dropped")
            
    # Mock the protocol to return a broken stream
    def mock_response_stream(status, headers):
        mock_proto.response_called = True
        mock_proto.response_status = status
        mock_proto.response_headers = headers
        mock_proto.stream = BrokenStream()
        return mock_proto.stream
        
    mock_proto.response_stream = mock_response_stream
    
    async def generator():
        yield "test"
        yield "never reached"
        
    def handler(req):
        return SSEResponse(generator())
        
    router.add_python_route("GET", "/sse_drop", handler)
    scope = MockRSGIScope(method="GET", path="/sse_drop", proto="http")
    
    # Should not raise to the top level, should silently catch ConnectionError
    await app(scope, mock_proto)
