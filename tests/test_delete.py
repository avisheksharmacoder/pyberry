import pytest
from pyberry.app import delete
from pyberry.core.rsgi import router

def test_delete_decorator_basic():
    @delete("/test_delete_basic")
    def handler_delete(req):
        return "delete_basic"

    handler, path_params, param_meta, needs_req = router.match_python_route("DELETE", "/test_delete_basic")
    assert handler is not None
    assert handler(None) == "delete_basic"

def test_delete_decorator_with_params():
    @delete("/test_delete/{item_id}")
    def handler_delete_param(req, item_id: str):
        return f"delete_{item_id}"

    handler, path_params, param_meta, needs_req = router.match_python_route("DELETE", "/test_delete/abc-123")
    assert handler is not None
    assert path_params == {"item_id": "abc-123"}
    assert handler(None, item_id="abc-123") == "delete_abc-123"

def test_delete_decorator_mismatch_method():
    @delete("/test_delete_mismatch")
    def handler_delete_mismatch(req):
        return "mismatch"

    handler, path_params, param_meta, needs_req = router.match_python_route("GET", "/test_delete_mismatch")
    assert handler is None
