# cython: language_level=3
# -----------------------------------------------------------------------------
# Compilation instructions are the same as 11_cython_hello_world.pyx
# -----------------------------------------------------------------------------

from pyberry.core.rsgi cimport router as _router
from pyberry.core.fastjson import loads as fast_loads
import json

# When handling POST bodies, the endpoint must be async to await the proto body
cdef object post_json_cython(object scope, object proto):
    return _post_json_impl(scope, proto)

async def _post_json_impl(scope, proto):
    # Read the raw byte stream from the Rust server
    msg = await proto()
    
    try:
        # Parse using PyBerry's ultra-fast C JSON parser (yyjson)
        data = fast_loads(msg)
        
        # Access the parsed dictionary directly
        item_id = data.get("id", "unknown")
        
        response_body = json.dumps({
            "status": "created",
            "received_id": item_id
        }).encode('utf-8')
        
        # Use response_bytes because we encoded the JSON string to bytes above
        proto.response_bytes(
            status=201, 
            headers=[('content-type', 'application/json')], 
            body=response_body
        )
        return 201
        
    except Exception as e:
        # Always wrap in try/except to prevent silent 500s from Granian!
        import traceback
        traceback.print_exc()
        proto.response_str(status=500, headers=[('content-type', 'text/plain')], body="Internal Server Error")
        return 500

_router.add_route("POST", "/post-cython", post_json_cython)
