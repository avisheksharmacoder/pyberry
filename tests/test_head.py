import pytest
from pyberry.app import head
from pyberry.core.rsgi import router

def test_head_decorator_basic():
    @head("/test_head_basic")
    def handler_head(req):
        return "head_basic"

    handler, path_params, param_meta, needs_req = router.match_python_route("HEAD", "/test_head_basic")
    assert handler is not None
    assert handler(None) == "head_basic"

@pytest.mark.xfail(reason="Radix router lacks a head_tree for parameterized routes")
def test_head_decorator_with_params():
    @head("/test_head/{info}")
    def handler_head_param(req, info: str):
        return f"head_{info}"

    handler, path_params, param_meta, needs_req = router.match_python_route("HEAD", "/test_head/data")
    assert handler is not None
    assert path_params == {"info": "data"}
    assert handler(None, info="data") == "head_data"

def test_head_decorator_mismatch_method():
    @head("/test_head_mismatch")
    def handler_head_mismatch(req):
        return "mismatch"

    handler, path_params, param_meta, needs_req = router.match_python_route("GET", "/test_head_mismatch")
    assert handler is None
