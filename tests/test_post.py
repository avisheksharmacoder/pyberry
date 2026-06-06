import pytest
from pyberry.app import post
from pyberry.core.rsgi import router

def test_post_decorator_basic():
    @post("/test_post_basic")
    def handler_post(req):
        return "post_basic"

    handler, path_params, param_meta, needs_req = router.match_python_route("POST", "/test_post_basic")
    assert handler is not None
    assert handler(None) == "post_basic"

def test_post_decorator_with_params():
    @post("/test_post/{action}")
    def handler_post_param(req, action: str):
        return f"post_{action}"

    handler, path_params, param_meta, needs_req = router.match_python_route("POST", "/test_post/submit")
    assert handler is not None
    assert path_params == {"action": "submit"}
    assert handler(None, action="submit") == "post_submit"

def test_post_decorator_mismatch_method():
    @post("/test_post_mismatch")
    def handler_post_mismatch(req):
        return "mismatch"

    handler, path_params, param_meta, needs_req = router.match_python_route("GET", "/test_post_mismatch")
    assert handler is None
