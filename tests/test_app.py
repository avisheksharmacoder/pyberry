import pytest
from pyberry.app import get, post
from pyberry.core.rsgi import router

def test_get_decorator():
    @get("/test_get")
    def my_handler(req):
        return "get"

    handler, path_params, param_meta = router.match_python_route("GET", "/test_get")
    assert handler is not None
    assert handler(None) == "get"
    
def test_post_decorator():
    @post("/test_post")
    def my_handler(req):
        return "post"

    handler, path_params, param_meta = router.match_python_route("POST", "/test_post")
    assert handler is not None
    assert handler(None) == "post"
