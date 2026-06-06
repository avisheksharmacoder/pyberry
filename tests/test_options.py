import pytest
from pyberry.app import options
from pyberry.core.rsgi import router

def test_options_decorator_basic():
    @options("/test_options_basic")
    def handler_options(req):
        return "options_basic"

    handler, path_params, param_meta, needs_req = router.match_python_route("OPTIONS", "/test_options_basic")
    assert handler is not None
    assert handler(None) == "options_basic"

@pytest.mark.xfail(reason="Radix router lacks an options_tree for parameterized routes")
def test_options_decorator_with_params():
    @options("/test_options/{route}")
    def handler_options_param(req, route: str):
        return f"options_{route}"

    handler, path_params, param_meta, needs_req = router.match_python_route("OPTIONS", "/test_options/myroute")
    assert handler is not None
    assert path_params == {"route": "myroute"}
    assert handler(None, route="myroute") == "options_myroute"

def test_options_decorator_mismatch_method():
    @options("/test_options_mismatch")
    def handler_options_mismatch(req):
        return "mismatch"

    handler, path_params, param_meta, needs_req = router.match_python_route("POST", "/test_options_mismatch")
    assert handler is None
