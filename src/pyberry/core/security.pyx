# cython: language_level=3

cdef int validate_request(object scope, bint cors_enabled, list allowed_hosts) except *:
    """
    Validates a request for Host Header Injection and CORS/CSRF issues.
    Returns 0 if valid, 400 for Bad Host, 403 for Forbidden (CORS).
    """
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
            print("HOST IS NONE")
            return 400
        
        # Some clients send Host: domain:port. Split by colon.
        host_no_port = host.split(":")[0]
        print("HOST:", host, "HOST_NO_PORT:", host_no_port, "ALLOWED:", allowed_hosts)
        if host_no_port not in allowed_hosts and host not in allowed_hosts:
            print("HOST NOT ALLOWED")
            return 400

    # CORS Validation
    if cors_enabled and origin is not None and host is not None:
        # Extremely strict block of cross-origin requests
        if not origin.endswith(host_no_port if 'host_no_port' in locals() else host.split(":")[0]):
            print("CORS FAILED")
            return 403
            
    return 0
