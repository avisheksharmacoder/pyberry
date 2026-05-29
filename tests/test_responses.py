import pytest
import json
from pyberry.core.responses import JSONResponse, HTMLResponse, PlainTextResponse, HTTPException

def test_json_response():
    resp = JSONResponse({"test": "ok"}, status=201, headers=[('x-custom', 'test')])
    assert resp.status == 201
    assert resp.body == json.dumps({"test": "ok"}).encode('utf-8')
    assert ('content-type', 'application/json') in resp.headers
    assert ('x-custom', 'test') in resp.headers

def test_html_response():
    resp = HTMLResponse("<h1>Hi</h1>")
    assert resp.status == 200
    assert resp.body == b"<h1>Hi</h1>"
    assert ('content-type', 'text/html') in resp.headers

def test_plaintext_response():
    resp = PlainTextResponse("Hello")
    assert resp.status == 200
    assert resp.body == b"Hello"
    assert ('content-type', 'text/plain') in resp.headers

def test_http_exception():
    exc = HTTPException(404, "Not Found")
    assert exc.status_code == 404
    assert exc.detail == "Not Found"
    assert str(exc) == "404: Not Found"
