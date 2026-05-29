import pytest
from pyberry.core.router import Router

def test_router_add_and_match():
    router = Router()
    
    def sample_handler(req):
        pass
        
    router.add_python_route("GET", "/test", sample_handler)
    
    handler, path_params, param_meta = router.match_python_route("GET", "/test")
    assert handler is sample_handler
    assert path_params == {}

def test_router_path_parameters():
    router = Router()
    
    def user_handler(req, user_id: int):
        pass
        
    router.add_python_route("GET", "/users/{user_id}", user_handler)
    
    handler, path_params, param_meta = router.match_python_route("GET", "/users/123")
    assert handler is user_handler
    assert path_params == {"user_id": "123"}
    assert param_meta["user_id"] == int

def test_router_not_found():
    router = Router()
    
    handler, path_params, param_meta = router.match_python_route("GET", "/missing")
    assert handler is None

def test_router_method_mismatch():
    router = Router()
    
    def sample_handler(req):
        pass
        
    router.add_python_route("POST", "/test", sample_handler)
    
    handler, path_params, param_meta = router.match_python_route("GET", "/test")
    assert handler is None
