# cython: language_level=3
import cython
from pyberry.core.router cimport Router, EndpointFunc
from pyberry.core.security cimport validate_request, check_rate_limit
from pyberry.config import config
from pyberry.core.request cimport Request
from pyberry.core.response cimport Response
from pyberry.core.request import Request as PyRequest
from pyberry.core.response import Response as PyResponse
import asyncio
import inspect
from urllib.parse import parse_qs
from pyberry.core.responses import HTTPException
from pyberry.core.logger cimport push_log
from pyberry.core.logger import start_logger
from pyberry.core.validation import validate_data, BaseModel

_loop_configured = False

cdef Router _router = Router()
router = _router

cdef extern from "Python.h":
    const char* PyUnicode_AsUTF8(object unicode)

cdef void _rsgi_push_log(str method, str path, int status):
    cdef const char* c_method = PyUnicode_AsUTF8(method)
    cdef const char* c_path = PyUnicode_AsUTF8(path)
    push_log(c_method, c_path, status)

# ---------------------------------------------------------
# Step 2.2: Compiled Endpoint Registration
# ---------------------------------------------------------
# A compiled C-function endpoint to demonstrate Phase 2
# It acts as the "compiled user endpoint" holding a C-function pointer.
cdef object hello_endpoint(Request req):
    # Returns a Response object directly. 
    # When transpiled later, this could be a coroutine.
    return PyResponse(body="Hello from compiled C-endpoint via Radix Tree!", status=200)

cdef object users_endpoint(Request req):
    return PyResponse(body="Users endpoint hit!", status=200)

# Register routes directly to C-function pointers
_router.add_route("GET", "/", hello_endpoint)
_router.add_route("GET", "/users", users_endpoint)


async def app(scope, proto):
    cdef const unsigned char[:] body_view
    cdef EndpointFunc handler
    cdef int sec_status
    global _loop_configured

    if not _loop_configured:
        try:
            loop = asyncio.get_running_loop()
            # Python 3.12+ Eager Task Execution
            loop.set_task_factory(asyncio.eager_task_factory)
        except (RuntimeError, AttributeError):
            pass
        start_logger()
        
        # Initialize Database connection pool
        from pyberry.db import db
        if hasattr(config, 'libsql_url') and config.libsql_url:
            db.init_db(config.libsql_url, getattr(config, 'libsql_auth_token', None))
            
        _loop_configured = True

    if scope.proto == 'http':
        # ---------------------------------------------------------
        # Step 2.3: Security Middleware Layer
        # ---------------------------------------------------------
        sec_status = validate_request(scope, config.cors_enabled, config.allowed_hosts, config.path_traversal_protection)
        if sec_status != 0:
            if sec_status == 400:
                proto.response_str(
                    status=400, 
                    headers=[('content-type', 'text/plain')], 
                    body="Invalid Host header"
                )
            else:
                proto.response_str(
                    status=403, 
                    headers=[('content-type', 'text/plain')], 
                    body="Forbidden by Strict Security Policy"
                )
            _rsgi_push_log(scope.method, scope.path, sec_status)
            return

        if config.rate_limit_enabled:
            client_ip = scope.client[0] if scope.client else "unknown"
            if check_rate_limit(client_ip, config.rate_limit_requests, config.rate_limit_window) == 429:
                proto.response_str(
                    status=429,
                    headers=[('content-type', 'text/plain')] + config.security_headers,
                    body="Too Many Requests"
                )
                _rsgi_push_log(scope.method, scope.path, 429)
                return

        # ---------------------------------------------------------
        # Step 2.1 & 2.2: Radix Tree Router Execution
        # ---------------------------------------------------------
        handler = _router.get_route(scope.method, scope.path)
        if handler == NULL:
            py_handler, path_params, param_meta = _router.match_python_route(scope.method, scope.path)
            
            if py_handler is not None:
                req = PyRequest(scope, proto)
                kwargs = {}
                
                if scope.query_string:
                    query_params = parse_qs(scope.query_string)
                    for k, v in query_params.items():
                        kwargs[k] = v[0]
                        
                if path_params:
                    kwargs.update(path_params)
                    
                try:
                    if param_meta:
                        injected_kwargs = {}
                        for name, meta_tuple in param_meta.items():
                            p_type, schema = meta_tuple
                            
                            if schema is not None:
                                # It's a dataclass!
                                json_data = await req.json()
                                validated = validate_data(schema, json_data)
                                injected_kwargs[name] = p_type(**validated)
                            elif hasattr(p_type, "__bases__") and BaseModel in p_type.__bases__:
                                # It's a BaseModel!
                                json_data = await req.json()
                                injected_kwargs[name] = p_type(**json_data)
                            elif name in kwargs:
                                val = kwargs[name]
                                if p_type is not inspect._empty:
                                    if p_type == 'int' or p_type == int:
                                        try:
                                            val = int(val)
                                        except ValueError:
                                            pass
                                    elif p_type == 'float' or p_type == float:
                                        try:
                                            val = float(val)
                                        except ValueError:
                                            pass
                                    elif p_type == 'bool' or p_type == bool:
                                        val = str(val).lower() in ('true', '1', 'yes', 't', 'y')
                                    elif callable(p_type):
                                        try:
                                            val = p_type(val)
                                        except Exception:
                                            pass
                                injected_kwargs[name] = val
                        res = py_handler(req, **injected_kwargs)
                    else:
                        res = py_handler(req, **kwargs)
                        
                    if hasattr(res, "__await__"):
                        res = await res
                        
                    if req._body is None:
                        msg = await proto()
                        req._body = msg
                    else:
                        msg = req._body
                    
                    if len(msg) > config.max_body_size:
                        proto.response_str(
                            status=413,
                            headers=[('content-type', 'text/plain')] + config.security_headers,
                            body="Payload Too Large"
                        )
                        _rsgi_push_log(scope.method, scope.path, 413)
                        return
                        
                    body_view = msg
                    
                    final_headers = res.headers + config.security_headers if config.security_headers else res.headers
                    
                    proto.response_str(
                        status=res.status, 
                        headers=final_headers, 
                        body=res.body
                    )
                    _rsgi_push_log(scope.method, scope.path, res.status)
                except HTTPException as e:
                    proto.response_str(
                        status=e.status_code, 
                        headers=[('content-type', 'text/plain')] + config.security_headers, 
                        body=e.detail
                    )
                    _rsgi_push_log(scope.method, scope.path, e.status_code)
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    proto.response_str(
                        status=500, 
                        headers=[('content-type', 'text/plain')] + config.security_headers, 
                        body="Internal Server Error"
                    )
                    _rsgi_push_log(scope.method, scope.path, 500)
                return

            proto.response_str(
                status=404, 
                headers=[('content-type', 'text/plain')] + config.security_headers, 
                body="Not Found"
            )
            _rsgi_push_log(scope.method, scope.path, 404)
            return
            
        req = PyRequest(scope, proto)
        
        # Execute the C-function pointer directly (microsecond execution)
        res = handler(req)
        
        # If it returns a coroutine, we await it (future-proofing)
        if hasattr(res, "__await__"):
            res = await res
            
        # Step 1.2: Memory view hand-off (demonstration)
        msg = await req.body()
        if len(msg) > config.max_body_size:
            proto.response_str(
                status=413,
                headers=[('content-type', 'text/plain')] + config.security_headers,
                body="Payload Too Large"
            )
            _rsgi_push_log(scope.method, scope.path, 413)
            return
            
        body_view = msg
            
        final_headers_c = res.headers + config.security_headers if config.security_headers else res.headers
        
        # Send the response back through Granian
        proto.response_str(
            status=res.status, 
            headers=final_headers_c, 
            body=res.body
        )
        _rsgi_push_log(scope.method, scope.path, res.status)
