import pytest
import asyncio
from unittest.mock import Mock, patch
import inspect
from pyberry.core.rsgi import app, router
from pyberry.core.responses import JSONResponse, HTTPException
from conftest import MockRSGIScope, MockRSGIProtocol

@pytest.mark.asyncio
async def test_rsgi_successful_request(mock_proto):
    # Setup route
    def handler(req):
        return JSONResponse({"ok": True})
    
    router.add_python_route("GET", "/rsgi_test", handler)
        
    scope = MockRSGIScope(method="GET", path="/rsgi_test", proto="http")
    
    await app(scope, mock_proto)
    
    assert mock_proto.response_called
    assert mock_proto.response_status == 200
    assert ('content-type', 'application/json') in mock_proto.response_headers
    assert mock_proto.response_body == b'{"ok": true}'

@pytest.mark.asyncio
async def test_rsgi_not_found(mock_proto):
    scope = MockRSGIScope(method="GET", path="/not_found_route", proto="http")
    await app(scope, mock_proto)
    
    assert mock_proto.response_called
    assert mock_proto.response_status == 404
    assert mock_proto.response_body == "Not Found"

@pytest.mark.asyncio
async def test_rsgi_parameter_injection(mock_proto):
    def handler(req, user_id: int):
        assert isinstance(user_id, int)
        return JSONResponse({"id": user_id})
        
    router.add_python_route("GET", "/users/{user_id}", handler)
        
    scope = MockRSGIScope(method="GET", path="/users/42", proto="http")
    await app(scope, mock_proto)
    
    assert mock_proto.response_called
    assert mock_proto.response_status == 200
    assert mock_proto.response_body == b'{"id": 42}'

@pytest.mark.asyncio
async def test_rsgi_http_exception(mock_proto):
    def handler(req):
        raise HTTPException(status_code=403, detail="Forbidden Area")
        
    router.add_python_route("GET", "/error", handler)
        
    scope = MockRSGIScope(method="GET", path="/error", proto="http")
    await app(scope, mock_proto)
    
    assert mock_proto.response_called
    assert mock_proto.response_status == 403
    assert mock_proto.response_body == "Forbidden Area"

@pytest.mark.asyncio
async def test_rsgi_unhandled_exception(mock_proto):
    def handler(req):
        raise ValueError("Oops")
        
    router.add_python_route("GET", "/crash", handler)
        
    scope = MockRSGIScope(method="GET", path="/crash", proto="http")
    await app(scope, mock_proto)
    
    assert mock_proto.response_called
    assert mock_proto.response_status == 500
    assert mock_proto.response_body == "Internal Server Error"
