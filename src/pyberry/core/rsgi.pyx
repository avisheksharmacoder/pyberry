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
from pyberry.core.responses import HTTPException, SSEResponse
from pyberry.core.logger cimport push_log
from pyberry.core.logger import start_logger
from pyberry.core.validation import BaseModel
from pyberry.core import fastjson
from libc.stdlib cimport malloc, free

_loop_configured = False

cdef Router _router = Router()
router = _router

cdef extern from "Python.h":
    const char* PyUnicode_AsUTF8(object unicode)

cdef dict _method_cache = {
    "GET": b"GET",
    "POST": b"POST",
    "PUT": b"PUT",
    "DELETE": b"DELETE",
    "PATCH": b"PATCH",
    "OPTIONS": b"OPTIONS",
    "HEAD": b"HEAD"
}

cdef void _rsgi_push_log(str method, str path, int status):
    cdef const char* c_method
    cdef bytes b_method = _method_cache.get(method)
    if b_method is not None:
        c_method = b_method
    else:
        c_method = PyUnicode_AsUTF8(method)
        
    cdef const char* c_path = PyUnicode_AsUTF8(path)
    push_log(c_method, c_path, status)

cdef str _unquote_plus_c(str s):
    cdef bytes b = s.encode('utf-8')
    cdef int length = len(b)
    cdef const char* buf = b
    cdef char* out = <char*>malloc(length + 1)
    if out == NULL:
        raise MemoryError()
    cdef int i = 0
    cdef int j = 0
    cdef char c
    cdef int v
    while i < length:
        c = buf[i]
        if c == b'+':
            out[j] = b' '
            j += 1
            i += 1
        elif c == b'%' and i + 2 < length:
            if buf[i+1] >= b'0' and buf[i+1] <= b'9':
                v = (buf[i+1] - b'0') << 4
            elif buf[i+1] >= b'A' and buf[i+1] <= b'F':
                v = (buf[i+1] - b'A' + 10) << 4
            elif buf[i+1] >= b'a' and buf[i+1] <= b'f':
                v = (buf[i+1] - b'a' + 10) << 4
            else:
                out[j] = c
                j += 1
                i += 1
                continue
                
            if buf[i+2] >= b'0' and buf[i+2] <= b'9':
                v |= (buf[i+2] - b'0')
            elif buf[i+2] >= b'A' and buf[i+2] <= b'F':
                v |= (buf[i+2] - b'A' + 10)
            elif buf[i+2] >= b'a' and buf[i+2] <= b'f':
                v |= (buf[i+2] - b'a' + 10)
            else:
                out[j] = c
                j += 1
                i += 1
                continue
                
            out[j] = v
            j += 1
            i += 3
        else:
            out[j] = c
            j += 1
            i += 1
            
    cdef bytes result = out[:j]
    free(out)
    return result.decode('utf-8', 'replace')

cdef dict parse_qs_c(str qs):
    cdef dict res = {}
    cdef list pairs = qs.split('&')
    cdef str pair, k, v
    cdef int idx
    for pair in pairs:
        if not pair: continue
        idx = pair.find('=')
        if idx == -1:
            k = _unquote_plus_c(pair) if '%' in pair or '+' in pair else pair
            v = ""
        else:
            k = _unquote_plus_c(pair[:idx]) if '%' in pair[:idx] or '+' in pair[:idx] else pair[:idx]
            v = _unquote_plus_c(pair[idx+1:]) if '%' in pair[idx+1:] or '+' in pair[idx+1:] else pair[idx+1:]
        
        if k in res:
            res[k].append(v)
        else:
            res[k] = [v]
    return res

cdef list _inject_security_headers(list headers, list security_headers):
    if not security_headers:
        return headers
        
    cdef list final_headers = list(headers)
    cdef set existing_keys = {k.lower() if isinstance(k, str) else k for k, v in headers}
    
    for k, v in security_headers:
        if k not in existing_keys:
            final_headers.append((k, v))
            
    return final_headers

# ---------------------------------------------------------
# Step 2.2: Compiled Endpoint Registration
# ---------------------------------------------------------
# A compiled C-function endpoint to demonstrate Phase 2
# It acts as the "compiled user endpoint" holding a C-function pointer.
cdef object hello_endpoint(object scope, object proto):
    # Write directly to Granian's Rust proto, zero allocations!
    proto.response_str(status=200, headers=[], body="Hello from compiled C-endpoint via Radix Tree!")
    return 200

cdef object users_endpoint(object scope, object proto):
    proto.response_str(status=200, headers=[], body="Users endpoint hit!")
    return 200

# Register routes directly to C-function pointers
_router.add_route("GET", "/", hello_endpoint)
_router.add_route("GET", "/users", users_endpoint)

cdef bytes _format_sse_chunk_c(object chunk):
    cdef bytes payload
    
    # Fast-path for dict (already flat JSON bytes)
    if type(chunk) is dict:
        payload = fastjson.dumps(chunk)
    elif isinstance(chunk, bytes):
        payload = <bytes>chunk
    elif isinstance(chunk, str):
        payload = chunk.encode('utf-8')
    else:
        payload = str(chunk).encode('utf-8')
        
    # Multi-line string spec fix using optimized bytes.replace
    # If there are internal newlines, turn them into 'data: ' prefixes
    if b"\n" in payload:
        payload = payload.replace(b"\n", b"\ndata: ")
        
    return b"data: " + payload + b"\n\n"

async def app(scope, proto):
    cdef EndpointFunc handler
    cdef int sec_status
    cdef str req_method = scope.method
    cdef str req_path = scope.path
    cdef list final_headers = None
    cdef list final_headers_c = None
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
        sec_status = validate_request(scope, config.cors_enabled, config.allowed_hosts, config.cors_allowed_origins, config.path_traversal_protection, config.max_body_size)
        if sec_status != 0:
            if sec_status == 413:
                headers_413 = _inject_security_headers([('content-type', 'text/plain')], config.security_headers)
                proto.response_str(
                    status=413, 
                    headers=headers_413, 
                    body="Payload Too Large"
                )
            elif sec_status == 400:
                headers_400 = _inject_security_headers([('content-type', 'text/plain')], config.security_headers)
                proto.response_str(
                    status=400, 
                    headers=headers_400, 
                    body="Invalid Host header"
                )
            else:
                headers_403 = _inject_security_headers([('content-type', 'text/plain')], config.security_headers)
                proto.response_str(
                    status=403, 
                    headers=headers_403, 
                    body="Forbidden by Strict Security Policy"
                )
            _rsgi_push_log(req_method, req_path, sec_status)
            return

        if config.rate_limit_enabled:
            client_ip = scope.client[0] if scope.client else "unknown"
            if check_rate_limit(client_ip, config.rate_limit_requests, config.rate_limit_window) == 429:
                # Optimized header extension
                headers_429 = _inject_security_headers([('content-type', 'text/plain')], config.security_headers)
                    
                proto.response_str(
                    status=429,
                    headers=headers_429,
                    body="Too Many Requests"
                )
                _rsgi_push_log(req_method, req_path, 429)
                return

        # ---------------------------------------------------------
        # Step 2.1 & 2.2: Radix Tree Router Execution
        # ---------------------------------------------------------
        handler = _router.get_route(req_method, req_path)
        if handler == NULL:
            py_handler, path_params, param_meta, needs_req = _router.match_python_route(req_method, req_path)
            
            if py_handler is not None:
                req = None
                if needs_req:
                    req = PyRequest(scope, proto)
                try:
                    if param_meta:
                        args_list = [req] if needs_req else []
                        query_params = None
                        for name, p_type, schema, req_fields, def_fields in param_meta:
                            if schema is not None:
                                msg = await proto()
                                if req is not None:
                                    req._body = msg
                                if msg:
                                    parsed = fastjson.parse_model(p_type, schema, req_fields, def_fields, msg)
                                else:
                                    parsed = None
                                args_list.append(parsed)
                            else:
                                val = None
                                if path_params and name in path_params:
                                    val = path_params[name]
                                elif scope.query_string:
                                    if query_params is None:
                                        query_params = parse_qs_c(scope.query_string)
                                    if name in query_params:
                                        val = query_params[name][0]
                                    
                                if val is not None and p_type is not inspect._empty:
                                    if p_type == 'int' or p_type == int:
                                        try: val = int(val)
                                        except ValueError: pass
                                    elif p_type == 'float' or p_type == float:
                                        try: val = float(val)
                                        except ValueError: pass
                                    elif p_type == 'bool' or p_type == bool:
                                        val = str(val).lower() in ('true', '1', 'yes', 't', 'y')
                                    elif callable(p_type):
                                        try: val = p_type(val)
                                        except Exception: pass
                                args_list.append(val)
                                
                        res = py_handler(*args_list)
                    else:
                        if path_params:
                            if needs_req:
                                res = py_handler(req, **path_params)
                            else:
                                res = py_handler(**path_params)
                        else:
                            if needs_req:
                                res = py_handler(req)
                            else:
                                res = py_handler()
                        
                    if hasattr(res, "__await__"):
                        res = await res
                        
                    final_headers = _inject_security_headers(res.headers, config.security_headers)
                    if type(res) is SSEResponse:
                        stream = proto.response_stream(status=res.status, headers=final_headers)
                        try:
                            async for chunk in res.body:
                                await stream.send_bytes(_format_sse_chunk_c(chunk))
                        except (ConnectionError, BrokenPipeError, ConnectionResetError):
                            # Client disconnected gracefully
                            pass
                        except Exception as e:
                            # Developer generator bug
                            import traceback
                            traceback.print_exc()
                        _rsgi_push_log(req_method, req_path, res.status)
                        return

                    if isinstance(res.body, bytes):
                        proto.response_bytes(
                            status=res.status, 
                            headers=final_headers, 
                            body=res.body
                        )
                    else:
                        proto.response_str(
                            status=res.status, 
                            headers=final_headers, 
                            body=res.body
                        )
                    _rsgi_push_log(req_method, req_path, res.status)
                except HTTPException as e:
                    headers_ex = _inject_security_headers([('content-type', 'text/plain')], config.security_headers)
                    proto.response_str(
                        status=e.status_code, 
                        headers=headers_ex, 
                        body=e.detail
                    )
                    _rsgi_push_log(req_method, req_path, e.status_code)
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    headers_500 = _inject_security_headers([('content-type', 'text/plain')], config.security_headers)
                    proto.response_str(
                        status=500, 
                        headers=headers_500, 
                        body="Internal Server Error"
                    )
                    _rsgi_push_log(req_method, req_path, 500)
                return

            headers_404 = _inject_security_headers([('content-type', 'text/plain')], config.security_headers)
            proto.response_str(
                status=404, 
                headers=headers_404, 
                body="Not Found"
            )
            _rsgi_push_log(req_method, req_path, 404)
            return
            
        # Execute the C-function pointer directly (microsecond execution)
        res = handler(scope, proto)
        
        # If it returns a coroutine, we await it (future-proofing)
        if hasattr(res, "__await__"):
            res = await res
            
        if type(res) is int:
            _rsgi_push_log(req_method, req_path, <int>res)
            return
            
        # Send the response back through Granian
        final_headers_c = _inject_security_headers(res.headers, config.security_headers)
        if type(res) is SSEResponse:
            stream = proto.response_stream(status=res.status, headers=final_headers_c)
            try:
                async for chunk in res.body:
                    await stream.send_bytes(_format_sse_chunk_c(chunk))
            except (ConnectionError, BrokenPipeError, ConnectionResetError):
                # Client disconnected gracefully
                pass
            except Exception as e:
                # Developer generator bug
                import traceback
                traceback.print_exc()
            _rsgi_push_log(req_method, req_path, res.status)
            return

        if isinstance(res.body, bytes):
            proto.response_bytes(
                status=res.status, 
                headers=final_headers_c, 
                body=res.body
            )
        else:
            proto.response_str(
                status=res.status, 
                headers=final_headers_c, 
                body=res.body
            )
        _rsgi_push_log(req_method, req_path, res.status)
