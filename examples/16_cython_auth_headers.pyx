# cython: language_level=3
# -----------------------------------------------------------------------------
# Compilation instructions are the same as 11_cython_hello_world.pyx
# -----------------------------------------------------------------------------

from pyberry.core.rsgi cimport router as _router

cdef object auth_headers_cython(object scope, object proto):
    # scope.headers in Granian RSGI is a dictionary of {str: str}
    # Note: keys are always lowercase!
    cdef dict headers = scope.headers
    
    cdef str auth_header = headers.get("authorization", "")
    
    # Ultra-fast authorization check
    if auth_header != "Bearer secret-token-123":
        proto.response_str(
            status=401, 
            headers=[('content-type', 'text/plain')], 
            body="Unauthorized: Invalid or missing Bearer token"
        )
        return 401
        
    proto.response_str(
        status=200, 
        headers=[('content-type', 'text/plain')], 
        body="Access Granted! Welcome to the secure endpoint."
    )
    
    return 200

_router.add_route("GET", "/secure-cython", auth_headers_cython)
