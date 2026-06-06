# cython: language_level=3

import time
import threading
from urllib.parse import urlparse, unquote
from libc.string cimport strncasecmp, strchr

cdef extern from *:
    """
    #ifdef _MSC_VER
    #define strncasecmp _strnicmp
    #define strcasecmp _stricmp
    #endif
    """

cdef class PyberryRateLimiter:
    cdef dict _store
    cdef object _lock
    cdef int _max_ips
    
    def __init__(self, int max_ips=10000):
        # Limit to 10,000 unique IPs to prevent memory exhaustion
        self._store = {}
        self._lock = threading.Lock()
        self._max_ips = max_ips

    cdef int check_rate_limit(self, str ip, int max_req, int window) except *:
        cdef double now = time.time()
        cdef list state
        
        with self._lock:
            state = self._store.get(ip)
            
            if state is None:
                # Lazy cleanup: If we hit the memory limit, purge expired IPs
                if len(self._store) >= self._max_ips:
                    self._cleanup(now, window)
                    
                    # If still full after cleanup (extreme attack), clear everything 
                    # or drop the request. Clearing is safer for uptime.
                    if len(self._store) >= self._max_ips:
                        self._store.clear()

                # state is [count, first_request_time]
                self._store[ip] = [1, now]
                return 0
                
            # Check if window expired
            if now - state[1] > window:
                state[0] = 1
                state[1] = now
                return 0
                
            # Check if limit exceeded
            if state[0] >= max_req:
                return 429
                
            state[0] += 1
            return 0

    cdef void _cleanup(self, double now, int window):
        """Removes expired IPs from the dictionary"""
        cdef list to_delete = []
        for ip, state in self._store.items():
            if now - state[1] > window:
                to_delete.append(ip)
                
        for ip in to_delete:
            del self._store[ip]

cdef PyberryRateLimiter _global_rate_limiter = PyberryRateLimiter()

cdef int check_rate_limit(str ip, int max_req, int window) except *:
    return _global_rate_limiter.check_rate_limit(ip, max_req, window)

cdef bint is_cors_origin_allowed(str request_origin, list allowed_origins):
    """
    Validates the request origin against a list of allowed origins.
    allowed_origins can contain:
    - "*" (allow all)
    - "https://example.com" (exact match)
    - "https://*.example.com" (subdomain wildcard)
    """
    if "*" in allowed_origins:
        return True
        
    if request_origin in allowed_origins:
        return True

    # Parse the request origin to isolate the scheme and hostname
    try:
        parsed_req = urlparse(request_origin)
        req_scheme = parsed_req.scheme
        req_host = parsed_req.hostname
    except Exception:
        return False

    if not req_host:
        return False

    for allowed in allowed_origins:
        if "*." in allowed:
            try:
                parsed_allowed = urlparse(allowed)
                allowed_scheme = parsed_allowed.scheme
                allowed_host = parsed_allowed.hostname # e.g., *.example.com
            except Exception:
                continue
            
            # Ensure HTTP/HTTPS schemes match
            if req_scheme != allowed_scheme:
                continue
                
            # Safely check subdomain: strip the '*' and check suffix
            # E.g., allowed_host = "*.example.com" -> base_domain = ".example.com"
            base_domain = allowed_host[1:] 
            
            if req_host.endswith(base_domain):
                return True

    return False

cdef int validate_request(object scope, bint cors_enabled, list allowed_hosts, list allowed_origins, bint path_traversal_protection, int max_body_size) except *:
    """
    Validates a request for Path Traversal, Host Header Injection, CORS/CSRF, and Payload limits.
    Returns 0 if valid, 400 for Bad Request, 403 for Forbidden, 413 for Payload Too Large.
    """
    if path_traversal_protection:
        decoded_path = unquote(scope.path)
        if ".." in decoded_path:
            return 400
        if "\x00" in decoded_path:
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
    cdef int content_length = 0
    
    for k, v in headers_items:
        # RSGI headers can be bytes or strings
        if isinstance(k, bytes):
            c_key = <const char*>k
        else:
            k_bytes = str(k).encode('latin-1')
            c_key = <const char*>k_bytes
            
        if max_body_size > 0 and strncasecmp(c_key, b"content-length", 14) == 0:
            try:
                if isinstance(v, bytes):
                    content_length = int(v)
                elif isinstance(v, list) and len(v) > 0:
                    content_length = int(v[0])
                else:
                    content_length = int(v)
            except ValueError:
                pass
                
            if content_length > max_body_size:
                return 413
        elif strncasecmp(c_key, b"origin", 6) == 0:
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
            
            host = v_bytes.decode('latin-1')
            
            if host.startswith("["): # IPv6 with port like [::1]:8080
                parts = host.rsplit("]", 1)
                host_no_port = parts[0] + "]"
            elif ":" in host:
                host_no_port = host.rsplit(":", 1)[0]
            else:
                host_no_port = host
            
    # Host header validation
    if "*" not in allowed_hosts:
        # If host is missing (HTTP/1.0), or host isn't in allowed list (ignoring port for now)
        if host is None:
            return 400
        
        if host_no_port not in allowed_hosts and host not in allowed_hosts:
            return 400

    # CORS Validation
    if cors_enabled and origin is not None and host is not None:
        try:
            parsed_origin = urlparse(origin)
            origin_domain = parsed_origin.hostname
            is_same_origin = (origin_domain == host_no_port)
        except Exception:
            is_same_origin = False
            
        if not is_same_origin and not is_cors_origin_allowed(origin, allowed_origins):
            return 403
            
    return 0
