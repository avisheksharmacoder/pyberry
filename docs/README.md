# PyBerry Technical Documentation

Welcome to the [PyBerry](https://pypi.org/project/pyberry-framework/) technical documentation. PyBerry is an experimental, ultra-high-performance web framework built specifically for **Free-Threaded Python 3.14+ (No GIL)**. 

By combining the **Rust Server Gateway Interface (RSGI)** via Granian, **Cython Ahead-Of-Time (AOT) compilation**, and a custom **C-based Radix Tree Router**, PyBerry regularly exceeds 100,000 Requests/sec on a single worker process locally.

## Key Features
- **Free-Threaded Architecture (No GIL):** Utilizes Python 3.13/3.14+ free-threading for massive concurrent performance within a single worker process.
- **AOT Compilation (Cython):** Transpiles Python dataclasses and logic directly into C extensions (`@cython.cclass`), compiling the entire application ahead-of-time for maximum speed.
- **Rust-Powered Networking (Granian & RSGI):** Uses Granian's RSGI server interface to bypass slow WSGI/ASGI translation and directly feed memory views from Rust to Python.
- **C-Implemented Radix Router:** High-performance, O(K) complexity routing engine written in native C for instant path resolution, complete with dynamic path variables (e.g. `/users/{id}`) support.
- **Automatic Type Casting:** Path parameters and query string variables are automatically cast into their respective Python types (e.g. `int`, `bool`) based on your function's type hints.
- **Smart Asynchronous Execution (`FastFuture`):** Custom C-level wrappers around awaitables that heavily reduce `asyncio` overhead when calling async Python functions.
- **Built-in Developer CLI:** `pyberry run`, `pyberry dev`, `pyberry build`, and `pyberry check` provide a seamless Developer Experience (DX) out of the box.

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
