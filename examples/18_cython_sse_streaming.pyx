# cython: language_level=3
"""
Example 18: High-Frequency SSE Streaming in Cython
--------------------------------------------------
For extreme throughput requirements (e.g. high-frequency financial tickers, 
live sensor telemetry, or real-time game state), you can write your SSE 
generator directly in Cython.

When compiled using `pyberry build`, this circumvents standard Python overhead.
"""

import asyncio
import time
from pyberry.core.rsgi cimport router
from pyberry.core.responses import SSEResponse

# 1. The High-Frequency Generator
# Even in Cython, we use an async generator. Cython compiles this into 
# highly optimized C state machines under the hood.
async def stock_ticker_generator():
    """
    Simulates a high-frequency financial data feed streaming prices to the client.
    """
    cdef int i
    cdef double price = 150.00
    
    for i in range(10):
        # We simulate price fluctuations
        price += (i % 3) - 1.5 
        
        # We can yield pure bytes or strings. If we yield a string with newlines,
        # PyBerry's C-layer handles it automatically, replacing '\\n' with '\\ndata: '
        # to strictly adhere to the SSE spec without breaking the stream.
        
        # Here we yield a raw string formatted as JSON to avoid dictionary overhead
        # in an extremely hot loop.
        yield f'{{"symbol": "AAPL", "price": {price:.2f}, "timestamp": {time.time()}}}'
        
        # Yield fast to free the event loop
        await asyncio.sleep(0.1)

# 2. The Cython Route Handler
# We bypass the Python decorators and use the C-level router API directly.
def ticker_stream_handler(req):
    """
    Returns the SSE response wrapping the high-frequency generator.
    If the client drops connection, PyBerry catches the ConnectionError silently 
    so your server doesn't crash or leak memory.
    """
    return SSEResponse(stock_ticker_generator())

# 3. Registering the Route
# We register our C-compiled handler to the /ticker route.
router.add_python_route("GET", "/ticker", ticker_stream_handler)
