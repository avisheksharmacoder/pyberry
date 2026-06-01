# cython: language_level=3

import time
from libc.string cimport strncasecmp, strchr

cdef class RateLimitState:
    cdef public int count
    cdef public double first_req
    
    def __cinit__(self, double now):
        self.count = 1
        self.first_req = now

cdef dict _rate_limit_store = {}

cdef int check_rate_limit(str ip, int max_req, int window) except *:
    cdef double now = time.time()
    cdef RateLimitState state = _rate_limit_store.get(ip)
    
    if state is None:
        _rate_limit_store[ip] = RateLimitState(now)
        return 0
        
    if now - state.first_req > window:
        # Reset window
        state.count = 1
        state.first_req = now
        return 0
        
    if state.count >= max_req:
        return 429
        
    state.count += 1
    return 0

cdef int validate_request(object scope, bint cors_enabled, list allowed_hosts, bint path_traversal_protection) except *:
    """
    Validates a request for Path Traversal, Host Header Injection and CORS/CSRF issues.
    Returns 0 if valid, 400 for Bad Request, 403 for Forbidden.
    """
    if path_traversal_protection:
        if ".." in scope.path or "%2e%2e" in scope.path or "%2E%2E" in scope.path:
            return 400

    cdef str origin = None
    cdef str host = None
    cdef str host_no_port = None
    
    cdef object headers_items
    try:
        headers_items = scope.headers.items()
    except AttributeError:
        headers_items = scope.headers
        
    cdef bytes k_bytes, v_bytes
    cdef const char* c_key
    cdef const char* c_host
    cdef char* colon_ptr
    cdef int host_len
    
    for k, v in headers_items:
        # RSGI headers can be bytes or strings
        if isinstance(k, bytes):
            c_key = <const char*>k
        else:
            k_bytes = str(k).encode('latin-1')
            c_key = <const char*>k_bytes
            
        if strncasecmp(c_key, b"origin", 6) == 0:
            if isinstance(v, bytes):
                origin = v.decode('latin-1')
            elif isinstance(v, list) and len(v) > 0:
                origin = v[0].decode('latin-1') if isinstance(v[0], bytes) else str(v[0])
            else:
                origin = str(v)
        elif strncasecmp(c_key, b"host", 4) == 0:
            if isinstance(v, bytes):
                v_bytes = v
            elif isinstance(v, list) and len(v) > 0:
                v_bytes = v[0] if isinstance(v[0], bytes) else str(v[0]).encode('latin-1')
            else:
                v_bytes = str(v).encode('latin-1')
            
            c_host = <const char*>v_bytes
            colon_ptr = strchr(c_host, b':')
            
            if colon_ptr != NULL:
                host_len = colon_ptr - c_host
                host_no_port = v_bytes[:host_len].decode('latin-1')
            else:
                host_no_port = v_bytes.decode('latin-1')
            
            host = v_bytes.decode('latin-1')
            
    # Host header validation
    if "*" not in allowed_hosts:
        # If host is missing (HTTP/1.0), or host isn't in allowed list (ignoring port for now)
        if host is None:
            return 400
        
        if host_no_port not in allowed_hosts and host not in allowed_hosts:
            return 400

    # CORS Validation
    if cors_enabled and origin is not None and host is not None:
        # Extremely strict block of cross-origin requests
        if not origin.endswith(host_no_port if host_no_port is not None else host):
            return 403
            
    return 0
