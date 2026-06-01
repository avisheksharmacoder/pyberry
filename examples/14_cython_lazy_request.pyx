# cython: language_level=3
# -----------------------------------------------------------------------------
# Compilation instructions are the same as 11_cython_hello_world.pyx
# -----------------------------------------------------------------------------

from pyberry.core.rsgi cimport router as _router
from pyberry.core.request import Request as PyRequest

cdef object lazy_request_cython(object scope, object proto):
    # Sometimes you want the speed of a zero-allocation response, 
    # but you need the convenience of PyBerry's Request object to parse headers, 
    # client IPs, or complex payloads.
    
    # Lazily instantiate the Request object (adds a slight overhead but provides convenience)
    cdef object req = PyRequest(scope, proto)
    
    cdef str client_ip = req.client_ip
    cdef str user_agent = req.headers.get("user-agent", "Unknown")
    
    cdef str body = f"Hello {client_ip}! You are using: {user_agent}"
    
    # We STILL get the benefit of a zero-allocation Response!
    proto.response_str(
        status=200, 
        headers=[('content-type', 'text/plain')], 
        body=body
    )
    
    return 200

_router.add_route("GET", "/lazy-request", lazy_request_cython)
