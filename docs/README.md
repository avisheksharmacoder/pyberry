# PyBerry Technical Documentation

Welcome to the [PyBerry](https://pypi.org/project/pyberry-framework/) technical documentation. PyBerry is an experimental, ultra-high-performance web framework built specifically for that missing speed of Cython in popular Python web frameworks. 

By combining the **Rust Server Gateway Interface (RSGI)** via Granian, **Cython Ahead-Of-Time (AOT) compilation**, and a custom **C-based Radix Tree Router**, PyBerry regularly exceeds 30,000 Requests/sec on a single worker process locally, sometimes more. 


### Pyberry is in active port to Rust. 
- I'm exploring removing cython for a simpler and more maintainable core implementation in pure python and rust only. This is in accordance to use LorealDB as the default integrated database for Pyberry Framework, while both using a pure 100% rust core. This repo will be archived soon and a new one will be created for hosting the framework. 

## Key Features

- **Ultra-Fast Performance**: Built on top of the Granian server utilizing the RSGI interface and `uvloop`, providing unmatched speed and concurrency, achieving a modest 30,000+ RPS with a single worker. 
- **Cython-Optimized Core**: Almost the entire core engine (routing, request/response handling, validation, and security) is written in Cython (`.pyx`), compiling down to C-extensions for zero-overhead execution.
- **[Built-in Security](security.md)**: Good security configured out-of-the-box, including CORS, Host Header Validation, automatic Security Headers (HSTS, CSP, X-Frame-Options), Rate Limiting, and Path Traversal Protection.
- **Production Transpilation**: Includes a built-in CLI compiler (`pyberry build`) that automatically transpiles your application code into Cython extensions for maximum production performance.
- **Seamless Database Integration**: First-class asynchronous support for `libsql` (Turso) with built-in schema migration tools (`pyberry migrate`).
- **[Zero-Latency Logging](logging.md)**: Highly optimized background logger written in Cython ensuring that application telemetry doesn't impact request response times.
- **Developer Friendly CLI**: Includes an intuitive command-line interface with commands to bootstrap projects (`pyberry create`), run in hot-reloading dev mode (`pyberry dev`), and check system readiness (`pyberry check`).
- **High-Speed JSON Serialization**: Integrates a custom `fastjson` module implemented in Cython to rapidly handle JSON parsing and responses.
- **Native Server-Sent Events (SSE)**: Zero-overhead streaming responses via `SSEResponse` with automatic JSON serialization natively integrated into Granian's RSGI stream handler.
- **[Simple & Intuitive API](high_performance_routes.md)**: Lightweight decorator-based routing syntax (e.g., `@get`, `@post`) making it incredibly easy to define endpoints without boilerplate.


## Table of Contents
1. [Architecture Overview](architecture.md)
2. [Command Line Interface (CLI)](cli.md)
3. [Modular Project Design](modular.md)
4. [Fast HTTP Responses & Exceptions](responses.md)
5. [Database (LibSQL) Integration](database.md)
6. [High Performance Routing](high_performance_routes.md)
7. [Data Validation](validation.md)
8. [Security Guide](security.md)
9. [Zero-Latency Logging](logging.md)
10. [Tokio Rust Backend](tokio_backend.md)
11. [General Usage](pyberry_usage.md)
12. [Examples](examples.md)
13. [The Core Runtime](#the-core-runtime)
14. [AOT Transpiler Engine](#aot-transpiler-engine)

## Quick Start
```bash
# Build the application for production (transpiles and Cythonizes)
pyberry build user_app.py

# Run in production mode with Granian RSGI
pyberry run --workers 1
```

## The Core Runtime
The core of PyBerry is written entirely in Cython (`.pyx`) to bypass standard Python interpreter overhead during request handling.

- **`pyberry.core.rsgi`**: The main entry point for the Granian RSGI protocol. It bridges the Rust network stack to our C-level route handlers, ensuring minimal object allocation.
- **`pyberry.core.router`**: A fully C-implemented Radix Tree (Trie) router. It can instantly match static routes with `O(K)` complexity (where K is the path length) and supports dynamic `{parameter}` injection via named regex groups for Python handlers.
- **`pyberry.core.future`**: Provides `FastFuture`, a lightweight awaitable wrapper that bypasses traditional `asyncio.Future` overhead to maximize async throughput.

## AOT Transpiler Engine
PyBerry doesn't just run Python; it compiles it.

Using Python's built-in `ast` module (`pyberry.compiler.transformer`), PyBerry reads your standard Python application and injects Cython optimizations before compilation:
1. **Type Mapping:** Python type hints (`int`, `str`) are mapped to Cython equivalents.
2. **Dataclass Optimization:** Automatically injects `@cython.cclass` into your Pydantic/Dataclass models to convert them into C-structs.
3. **Await Wrapping:** Overrides the `await` keyword to wrap coroutines in our custom `FastFuture`.

The transpiled `.py` file is then compiled by GCC into a shared object (`.so`) during the `pyberry build` step, running your business logic as native C code.
