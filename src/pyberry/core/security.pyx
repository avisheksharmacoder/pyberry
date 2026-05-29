# cython: language_level=3

import time

cdef dict _rate_limit_store = {}

cdef int check_rate_limit(str ip, int max_req, int window) except *:
    cdef double now = time.time()
    cdef tuple data = _rate_limit_store.get(ip)
    
    if data is None:
        _rate_limit_store[ip] = (1, now)
        return 0
        
    cdef int count = data[0]
    cdef double first_req = data[1]
    
    if now - first_req > window:
        # Reset window
        _rate_limit_store[ip] = (1, now)
        return 0
        
    if count >= max_req:
        return 429
        
    _rate_limit_store[ip] = (count + 1, first_req)
    return 0

cdef int validate_request(object scope, bint cors_enabled, list allowed_hosts, bint path_traversal_protection) except *:
    """
    Validates a request for Path Traversal, Host Header Injection and CORS/CSRF issues.
    Returns 0 if valid, 400 for Bad Request, 403 for Forbidden.
    """
    if path_traversal_protection:
        p = scope.path.lower()
        if ".." in p or "%2e%2e" in p:
            return 400

    cdef str origin = None
    cdef str host = None
    
    # Granian passes headers which we can iterate over
    try:
        headers_items = scope.headers.items()
    except AttributeError:
        headers_items = scope.headers
        
    for k, v in headers_items:
        # RSGI headers can be bytes or strings
        if isinstance(k, bytes):
            k_str = k.decode('latin-1').lower()
        else:
            k_str = str(k).lower()
            
        if isinstance(v, bytes):
            v_str = v.decode('latin-1')
        elif isinstance(v, list):
            if len(v) > 0:
                if isinstance(v[0], bytes):
                    v_str = v[0].decode('latin-1')
                else:
                    v_str = str(v[0])
            else:
                v_str = ""
        else:
            v_str = str(v)

        if k_str == "origin":
            origin = v_str
        elif k_str == "host":
            host = v_str
            
    # Host header validation
    if "*" not in allowed_hosts:
        # If host is missing (HTTP/1.0), or host isn't in allowed list (ignoring port for now)
        if host is None:
            return 400
        
        # Some clients send Host: domain:port. Split by colon.
        host_no_port = host.split(":")[0]
        if host_no_port not in allowed_hosts and host not in allowed_hosts:
            return 400

    # CORS Validation
    if cors_enabled and origin is not None and host is not None:
        # Extremely strict block of cross-origin requests
        if not origin.endswith(host_no_port if 'host_no_port' in locals() else host.split(":")[0]):
            return 403
            
    return 0
