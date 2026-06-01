# cython: language_level=3
# -----------------------------------------------------------------------------
# Compilation instructions are the same as 11_cython_hello_world.pyx
# -----------------------------------------------------------------------------

from pyberry.core.rsgi cimport router as _router
import json

cdef object json_response_cython(object scope, object proto):
    # Create the JSON payload
    # Note: using Python's json.dumps inside Cython is still fast, 
    # but the real speedup comes from skipping Request/Response object creation.
    response_body = json.dumps({
        "status": "success",
        "message": "This is a lightning fast JSON response",
        "data": {
            "items": [1, 2, 3],
            "active": True
        }
    })
    
    # Must use strings ('content-type') for Granian headers, NOT bytes (b'content-type')
    proto.response_str(
        status=200, 
        headers=[('content-type', 'application/json')], 
        body=response_body
    )
    
    return 200

# Register directly into the Radix Tree
_router.add_route("GET", "/json-cython", json_response_cython)
