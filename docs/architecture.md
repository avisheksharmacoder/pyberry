# Architecture Overview

PyBerry achieves unprecedented speed by bypassing the traditional Python WSGI/ASGI stack and running native C code as much as possible, driven by a Rust networking layer.

## Request Lifecycle

1. **Client Request**: A client sends an HTTP request.
2. **Rust Layer (Granian)**: The Granian HTTP server, written in Rust, accepts the TCP connection and parses the HTTP request.
3. **RSGI Interface**: Granian hands the request over to Python using the **RSGI** protocol, which passes minimal metadata (scope) to the `app()` coroutine in `pyberry.core.rsgi`.
4. **Security Middleware**: Before routing, `validate_request` (`security.pyx`) performs fast C-level validation (e.g., CORS checks).
5. **C-Level Routing (`router.pyx`)**:
   - The Radix Tree router looks up the path in `O(K)` time.
   - If it maps to a direct C-function pointer, it executes it with zero Python overhead.
   - If it maps to a Python route, it uses regular expressions to extract path parameters (`{user_id}`), applies automatic type casting, and invokes the Python function.
6. **Execution**: The user's handler executes. Because the user's code was compiled via `pyberry build`, it runs natively as a Cython C-extension.
7. **Response**: The `Response` object is returned and serialized directly back into Granian's response stream.

## Why Free-Threaded Python?
Traditional Python uses the Global Interpreter Lock (GIL), meaning only one thread can execute Python bytecode at a time. This severely bottlenecks multi-core Rust web servers (like Granian) when they try to hand off thousands of concurrent requests to Python workers.

By targeting **Python 3.13/3.14+ (Free-Threaded)**, PyBerry runs with `PYTHON_GIL=0`. This allows multiple requests to be processed truly concurrently within the *same* worker process, allowing a single worker to hit 100k+ RPS.

## The AOT Compiler (`pyberry/compiler/`)
The Ahead-Of-Time transpiler takes standard Python files and supercharges them.

- **AST Parsing**: Reads standard Python syntax (`ast.parse()`).
- **Transformation**: Uses `ast.NodeTransformer` to rewrite AST nodes.
- **Compilation**: Outputs modified Python code and uses Cython (`cythonize`) and GCC to build a `.so` library.

### Example Transformation:
**User writes:**
```python
@dataclass
class User:
    id: int
```

**PyBerry transpiles to:**
```python
import cython

@cython.cclass
@dataclass
class User:
    id: cython.int
```
This forces the Python object to be represented as a C-struct in memory.
