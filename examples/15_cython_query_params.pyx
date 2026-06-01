# cython: language_level=3
# -----------------------------------------------------------------------------
# Compilation instructions are the same as 11_cython_hello_world.pyx
# -----------------------------------------------------------------------------

from pyberry.core.rsgi cimport router as _router
from urllib.parse import parse_qs

cdef object query_params_cython(object scope, object proto):
    # Read the raw query string from the RSGI scope
    # Example: "name=Alice&age=30"
    cdef str qs = scope.query_string
    
    # Parse the query string manually
    # Note: Using urllib.parse is standard, but you can also use 
    # PyBerry's internal `parse_qs_c` from rsgi for more speed if accessible.
    cdef dict parsed = parse_qs(qs) if qs else {}
    
    # parse_qs returns lists for values: {'name': ['Alice']}
    cdef str name = parsed.get("name", ["Guest"])[0]
    
    cdef str response_body = f"Hello, {name}!"
    
    proto.response_str(
        status=200, 
        headers=[('content-type', 'text/plain')], 
        body=response_body
    )
    
    return 200

_router.add_route("GET", "/query-cython", query_params_cython)
