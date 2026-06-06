import pytest
from pyberry.app import get
from pyberry.core.rsgi import router

def test_get_decorator_basic():
    @get("/test_get_basic")
    def handler_get(req):
        return "get_basic"

    handler, path_params, param_meta, needs_req = router.match_python_route("GET", "/test_get_basic")
    assert handler is not None
    assert handler(None) == "get_basic"

def test_get_decorator_with_params():
    @get("/test_get/{id}")
    def handler_get_param(req, id: int):
        return f"get_{id}"

    handler, path_params, param_meta, needs_req = router.match_python_route("GET", "/test_get/123")
    assert handler is not None
    assert path_params == {"id": "123"}
    # The parsing of types is handled in `rsgi.pyx` so calling handler directly with params is fine
    assert handler(None, id=123) == "get_123"

def test_get_decorator_mismatch_method():
    @get("/test_get_mismatch")
    def handler_get_mismatch(req):
        return "mismatch"

    handler, path_params, param_meta, needs_req = router.match_python_route("POST", "/test_get_mismatch")
    # If the method doesn't match, it should not return the handler
    assert handler is None
