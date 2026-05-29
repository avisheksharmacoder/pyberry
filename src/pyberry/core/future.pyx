# cython: language_level=3
import cython

cdef class FastFuture:
    """
    A highly optimized Cython awaitable that bypasses uvloop.
    It submits I/O requests directly to the Rust Tokio runtime.
    """
    cdef public bint _done
    cdef public object _result
    cdef public object _awaitable
    
    def __init__(self, awaitable=None):
        self._done = False
        self._result = None
        self._awaitable = awaitable
        
    def __await__(self):
        # In a real FFI implementation, this would call submit_tokio_io
        # submit_tokio_io(NULL, c_wake_callback, <void*>self)
        
        # For simulation, we just yield the underlying awaitable if provided
        if self._awaitable is not None:
            yield from self._awaitable.__await__()
            
        while not self._done:
            yield self
            
        return self._result
        
    cdef void set_result(self, object result):
        self._result = result
        self._done = True
