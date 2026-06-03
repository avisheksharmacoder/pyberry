# PyBerry Technical Documentation

Welcome to the [PyBerry](https://pypi.org/project/pyberry-framework/) technical documentation. PyBerry is an experimental, ultra-high-performance web framework built specifically for that missing speed of Cython in popular Python web frameworks. 

By combining the **Rust Server Gateway Interface (RSGI)** via Granian, **Cython Ahead-Of-Time (AOT) compilation**, and a custom **C-based Radix Tree Router**, PyBerry regularly exceeds 30,000 Requests/sec on a single worker process locally, sometimes more. 

## Key Features

- **Ultra-Fast Performance**: Built on top of the Granian server utilizing the RSGI interface and `uvloop`, providing unmatched speed and concurrency, achieving a modest 30,000+ RPS with a single worker. 
- **Cython-Optimized Core**: Almost the entire core engine (routing, request/response handling, validation, and security) is written in Cython (`.pyx`), compiling down to C-extensions for zero-overhead execution.
- **Built-in Security**: Good security configured out-of-the-box, including CORS, Host Header Validation, automatic Security Headers (HSTS, CSP, X-Frame-Options), Rate Limiting, and Path Traversal Protection.
- **Production Transpilation**: Includes a built-in CLI compiler (`pyberry build`) that automatically transpiles your application code into Cython extensions for maximum production performance.
- **Seamless Database Integration**: First-class asynchronous support for `libsql` (Turso) with built-in schema migration tools (`pyberry migrate`).
- **Zero-Latency Logging**: Highly optimized background logger written in Cython ensuring that application telemetry doesn't impact request response times.
- **Developer Friendly CLI**: Includes an intuitive command-line interface with commands to bootstrap projects (`pyberry create`), run in hot-reloading dev mode (`pyberry dev`), and check system readiness (`pyberry check`).
- **High-Speed JSON Serialization**: Integrates a custom `fastjson` module implemented in Cython to rapidly handle JSON parsing and responses.
- **Simple & Intuitive API**: Lightweight decorator-based routing syntax (e.g., `@get`, `@post`) making it incredibly easy to define endpoints without boilerplate.

### Out-of-the-Box Memory Safety: Beating the Rust Workflow
When architecting high-performance backend systems, developers usually face a harsh trade-off: use Python for rapid prototyping but risk 3 AM memory crashes, or use Rust for perfect memory safety but suffer through a brutal, slow development cycle fighting the "borrow checker."

PyBerry solves this by giving you the ultimate hybrid experience. It provides **100% of Rust’s memory safety** with none of the daily frustration. 

It achieves this through an automated **ThreadSanitizer (TSan) Shield** built directly into the CLI:
- **Where PyBerry Beats Rust (The Playground):** Instead of a compiler screaming at you about lifetime bounds while you are just trying to mock out a JSON schema or test routing logic, PyBerry lets you write pure Python. You prototype at the speed of thought, and the Python GIL keeps you safe while you experiment.
- **Equivalent Safety to Rust (The Crucible):** Before you can deploy, you must run the PyBerry build command. The framework dynamically injects ThreadSanitizer into your code. While Rust uses mathematical proofs to prevent threading bugs at compile-time, TSan hooks directly into the CPU to track every single memory read and write at run-time during your test suite. If a single data race exists in your high-speed C extensions, TSan catches it with absolute microscopic precision.
- **Bulletproof Deployments (The Rocket):** PyBerry acts as a strict gatekeeper. If your code has a threading bug, the framework refuses to let you launch it. If your code is perfectly safe—proving it has the same thread-safety guarantees as a Rust binary—PyBerry strips away the safety checks and launches your server at maximum, unthrottled speed.

## Table of Contents
1. [Architecture Overview](architecture.md)
2. [Command Line Interface (CLI)](cli.md)
3. [Modular Project Design](modular.md)
4. [Fast HTTP Responses & Exceptions](responses.md)
5. [Database (LibSQL) Integration](database.md)
6. [The Core Runtime](#the-core-runtime)
7. [AOT Transpiler Engine](#aot-transpiler-engine)

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
