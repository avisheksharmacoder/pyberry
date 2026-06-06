import pytest
from pyberry.app import put
from pyberry.core.rsgi import router

def test_put_decorator_basic():
    @put("/test_put_basic")
    def handler_put(req):
        return "put_basic"

    handler, path_params, param_meta, needs_req = router.match_python_route("PUT", "/test_put_basic")
    assert handler is not None
    assert handler(None) == "put_basic"

def test_put_decorator_with_params():
    @put("/test_put/{resource_id}")
    def handler_put_param(req, resource_id: int):
        return f"put_{resource_id}"

    handler, path_params, param_meta, needs_req = router.match_python_route("PUT", "/test_put/42")
    assert handler is not None
    assert path_params == {"resource_id": "42"}
    assert handler(None, resource_id=42) == "put_42"

def test_put_decorator_mismatch_method():
    @put("/test_put_mismatch")
    def handler_put_mismatch(req):
        return "mismatch"

    handler, path_params, param_meta, needs_req = router.match_python_route("POST", "/test_put_mismatch")
    assert handler is None
