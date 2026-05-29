# High-Performance Logging in PyBerry

PyBerry features a highly optimized, zero-latency background logging system built natively in Cython. It is designed to provide beautiful, colorized terminal output and persistent file logging without hindering the framework's extreme Requests-Per-Second (RPS) throughput.

## Zero-Dependency, Lock-Free C Architecture

Traditional logging (such as `print` statements or synchronous file I/O) blocks the asynchronous event loop and severely degrades framework performance under load.

Initially, PyBerry attempted to solve this using Python's `queue.SimpleQueue`. However, at an extreme scale of 60,000+ RPS, three major bottlenecks emerged:
1. **Hidden Locks**: `queue.SimpleQueue` relies on a C-level mutex. Acquiring and releasing this lock 60,000 times per second created massive contention between the main event loop and the logging thread.
2. **Python Object Allocation**: The old architecture required encoding strings into new Python `bytes` objects and creating `tuple` wrappers for every log entry. This meant allocating over 100,000 temporary objects per second, thrashing the CPython memory allocator and requiring the Global Interpreter Lock (GIL).
3. **CPU False Sharing**: Thread read/write indices shared the same CPU cache line, causing processor cores to constantly invalidate each other's cache.

To achieve true zero-latency, PyBerry's logging has been completely rewritten in Cython with a **Lock-Free SPSC (Single-Producer, Single-Consumer) Ring Buffer**:

1. **The Hot Path (`push_log`)**: 
   When a request completes, PyBerry extracts the raw C string pointers from the Python strings in O(1) time using `PyUnicode_AsUTF8()`, avoiding all memory allocation. It then copies these C strings directly into a statically allocated C struct array. We intentionally **do not drop the GIL** during this step (`nogil`), because the lock-free C copy takes just a few nanoseconds, whereas a Python context switch to release/acquire the GIL takes ~50-100ns. By staying within the GIL for this microsecond operation, we save massive context-switching overhead.
   
2. **Lock-Free Atomics**: 
   The C ring buffer uses C11 atomic operations (`stdatomic.h`) to update the read/write indices. Because it's an SPSC queue, the main thread never blocks waiting for a lock. Additionally, the indices are padded with 64 empty bytes to prevent CPU false sharing across cores.

3. **The Pure C Background Worker (`pthread`)**: 
   The most critical optimization was moving the background worker entirely out of Python. Previously, the background thread was a Python daemon that woke up and acquired the GIL to format strings and execute `sys.stdout.write`. This created severe **GIL Contention**, artificially capping throughput at ~35K RPS. Now, PyBerry spawns a pure C thread (`pthread_create`) that operates 100% independently of the Python Interpreter. It formats strings and performs standard C I/O (`fprintf`) without ever requesting the GIL.

This strict C-level separation guarantees that your async event loop hands off log data in mere nanoseconds, allowing the framework to operate at maximum speed (60K+ RPS) even while logging everything.

## Output Targets

The background logger pushes logs to two destinations simultaneously:

1. **Terminal (sys.stdout)**: Colorized output where the HTTP method changes color based on type (GET is Green, POST is Blue, DELETE is Red) and the status codes indicate success or failure.
2. **File (`berrypy.log`)**: A plain-text version of the log is appended to `berrypy.log`, which is generated automatically in your project's root directory when you run `pyberry init`.

*Example Output:*
```text
[2026-05-29 08:24:47] GET /users/42 - 200
[2026-05-29 08:24:47] POST /auth/login - 403
```

## Toggling Logging for Peak Benchmarking

While the hot path enqueue operation takes less than a microsecond, executing the background thread does consume some CPU cycles at extreme scale (e.g., 100,000+ RPS).

If you are running load tests or benchmarking the absolute maximum capability of the framework, you should disable logging entirely. When disabled, the logger returns instantaneously without even pushing to the queue.

### How to Disable Logging

Open the generated `security.py` file in your PyBerry project root, and set `LOGGING_ENABLED` to `False`:

```python
# security.py

# Turn off for peak benchmarking (RPS)
LOGGING_ENABLED = False
```

When you are finished benchmarking, you can switch it back to `True` for development or standard production usage.
