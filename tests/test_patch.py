import pytest
from pyberry.app import patch
from pyberry.core.rsgi import router

def test_patch_decorator_basic():
    @patch("/test_patch_basic")
    def handler_patch(req):
        return "patch_basic"

    handler, path_params, param_meta, needs_req = router.match_python_route("PATCH", "/test_patch_basic")
    assert handler is not None
    assert handler(None) == "patch_basic"

def test_patch_decorator_with_params():
    @patch("/test_patch/{user_id}")
    def handler_patch_param(req, user_id: int):
        return f"patch_{user_id}"

    handler, path_params, param_meta, needs_req = router.match_python_route("PATCH", "/test_patch/99")
    assert handler is not None
    assert path_params == {"user_id": "99"}
    assert handler(None, user_id=99) == "patch_99"

def test_patch_decorator_mismatch_method():
    @patch("/test_patch_mismatch")
    def handler_patch_mismatch(req):
        return "mismatch"

    handler, path_params, param_meta, needs_req = router.match_python_route("PUT", "/test_patch_mismatch")
    assert handler is None
