# Writing High-Performance Cython Routes

PyBerry features a **dual-engine routing system**. For 99% of your endpoints, writing standard Python routes using decorators like `@app.get(...)` is highly recommended. It is fast, developer-friendly, and handles type-hinting, JSON parsing, and validation automatically.

However, if you have an ultra-high-throughput microservice or a critical hot-path endpoint that requires maximum performance, PyBerry allows you to bypass the Python VM object overhead entirely and write your routes directly in Cython.

## The Zero-Allocation Fast Path

By writing a compiled Cython route, you can receive the raw Request/Response objects (`scope` and `proto`) directly from our underlying Rust server (Granian). This means:
- No `kwargs` dictionary allocation
- No `PyRequest` object instantiation
- No `PyResponse` object instantiation
- Execution in single-digit microseconds

### The Endpoint Signature

To hook into the fast path, your Cython (`.pyx`) function must use the following `cdef` signature:

```cython
cdef object my_fast_endpoint(object scope, object proto):
    ...
```

1. **`scope`**: A dictionary containing all the RSGI request metadata (e.g., `scope.method`, `scope.path`, `scope.headers`).
2. **`proto`**: The Rust interface object used to stream bytes back to the client.

### Writing the Response

Instead of returning a Python `Response` object (which costs memory allocation), you trigger Granian directly using the `proto` object. 

After writing your response, **you must return the HTTP status code as an integer** so that the PyBerry router can log the request correctly.

```cython
cdef object hello_cython(object scope, object proto):
    # Do some incredibly fast C-level work here...
    cdef str my_body = "Hello from Cython!"
    
    # 1. Write the response directly to the Rust TCP buffer
    proto.response_str(
        status=200, 
        headers=[('content-type', 'text/plain')], 
        body=my_body
    )
    
    # 2. Return the status code for PyBerry's access logger
    return 200
```

### Registering the Route

Since this is a `cdef` function pointer, you cannot use the standard `@app.get` decorators. Instead, you register it directly into the PyBerry Radix Tree using the internal `_router`:

```cython
from pyberry.core.rsgi cimport _router

# Register method, path, and the C-function pointer
_router.add_route("GET", "/cython-fast", hello_cython)
```

## Lazy Request Instantiation

If your Cython endpoint suddenly requires complex framework features (like reading the full HTTP body stream), you can still fall back to manually instantiating a `PyRequest` object inside your handler. This gives you the best of both worlds.

```cython
from pyberry.core.request import Request as PyRequest

cdef object complex_cython_endpoint(object scope, object proto):
    # Lazily instantiate the Request object only when needed
    cdef object req = PyRequest(scope, proto)
    
    # Use standard request methods
    cdef str client_ip = req.client_ip
    
    # Still use the zero-allocation response path!
    proto.response_str(
        status=200, 
        headers=[], 
        body=f"Hello {client_ip}"
    )
    return 200
```
