# cython: language_level=3
import cython
import os
import pyberry_rust

cdef extern from "Python.h":
    ctypedef struct PyObject
    void Py_INCREF(object)
    void Py_DECREF(object)

cdef extern from *:
    """
    #include <stddef.h>
    #include <stdatomic.h>
    #include <unistd.h>
    #include <sys/eventfd.h>
    #include <Python.h>

    #define IO_QUEUE_SIZE 8192

    typedef struct {
        PyObject* future;
        PyObject* result;
    } IORingEntry;

    typedef struct {
        _Atomic size_t head;
        char pad1[64];
        _Atomic size_t tail;
        char pad2[64];
        IORingEntry entries[IO_QUEUE_SIZE];
    } IORingBuffer;

    static IORingBuffer io_buffer = {0};
    static int io_event_fd = -1;

    static inline int push_io_c(PyObject* future, PyObject* result) {
        size_t current_tail = atomic_load_explicit(&io_buffer.tail, memory_order_relaxed);
        size_t next_tail = (current_tail + 1) % IO_QUEUE_SIZE;
        size_t current_head = atomic_load_explicit(&io_buffer.head, memory_order_acquire);
        
        if (next_tail == current_head) {
            return 0; // Full
        }
        
        io_buffer.entries[current_tail].future = future;
        io_buffer.entries[current_tail].result = result;
        
        atomic_store_explicit(&io_buffer.tail, next_tail, memory_order_release);
        
        if (io_event_fd != -1) {
            uint64_t val = 1;
            write(io_event_fd, &val, sizeof(uint64_t));
        }
        
        return 1; // Success
    }

    static inline int pop_io_c(PyObject** out_future, PyObject** out_result) {
        size_t current_head = atomic_load_explicit(&io_buffer.head, memory_order_relaxed);
        size_t current_tail = atomic_load_explicit(&io_buffer.tail, memory_order_acquire);
        
        if (current_head == current_tail) {
            return 0; // Empty
        }
        
        *out_future = io_buffer.entries[current_head].future;
        *out_result = io_buffer.entries[current_head].result;
        
        size_t next_head = (current_head + 1) % IO_QUEUE_SIZE;
        atomic_store_explicit(&io_buffer.head, next_head, memory_order_release);
        return 1;
    }

    static int init_eventfd_c() {
        if (io_event_fd == -1) {
            io_event_fd = eventfd(0, EFD_NONBLOCK | EFD_CLOEXEC);
        }
        return io_event_fd;
    }
    """
    int init_eventfd_c()
    int push_io_c(object future, object result) nogil
    int pop_io_c(PyObject** out_future, PyObject** out_result)
    int io_event_fd

def c_drain_queue_callback():
    """
    Called by the event loop when eventfd fires.
    Drains the lock-free C ring buffer and wakes up suspended FastFutures.
    """
    cdef PyObject* future_ptr
    cdef PyObject* result_ptr
    
    # Clear the eventfd to avoid infinite loop firing
    if io_event_fd != -1:
        try:
            os.read(io_event_fd, 8)
        except BlockingIOError:
            pass
        
    while pop_io_c(&future_ptr, &result_ptr):
        future_obj = <object>future_ptr
        result_obj = <object>result_ptr
        future = <FastFuture>future_obj
        future._result = result_obj
        future._done = True
        
        if future._task_wakeup is not None:
            try:
                # Call task wakeup directly
                future._task_wakeup(future)
            except Exception:
                pass
                
        # Py_DECREF to release ownership from the C queue
        Py_DECREF(future_obj)
        Py_DECREF(result_obj)

def init_io_bridge(loop):
    """
    Initializes the C-level eventfd, hooks it into uvloop, 
    and passes the memory boundaries to Rust.
    """
    fd = init_eventfd_c()
    loop.add_reader(fd, c_drain_queue_callback)
    
    # Cast the C-function push_io_c to a size_t (usize in Rust)
    cdef size_t push_fn_ptr = <size_t>&push_io_c
    
    # Initialize the Rust engine with our C pointers
    pyberry_rust.init_rust_engine(push_fn_ptr, fd)

def execute_rust_io(future, str payload):
    """
    The new hot-path submitter.
    """
    # 1. INCREF the future so it survives until Rust returns it
    Py_INCREF(future)
    
    # 2. Get the raw memory address of the future object
    cdef size_t future_ptr = <size_t><PyObject*>future
    
    # 3. Hand off to Rust (Non-blocking, instant return)
    pyberry_rust.submit_io_task(future_ptr, payload)

cdef class FastFuture:
    """
    A highly optimized Cython awaitable that bypasses uvloop list allocation overhead
    and lock-contended call_soon_threadsafe.
    It submits I/O requests directly to the Rust Tokio runtime.
    """
    cdef public bint _done
    cdef public object _result
    cdef public object _awaitable
    cdef public bint _asyncio_future_blocking
    cdef public object _task_wakeup
    
    def __init__(self, awaitable=None):
        self._done = False
        self._result = None
        self._awaitable = awaitable
        self._asyncio_future_blocking = False
        self._task_wakeup = None
        
    def add_done_callback(self, cb, context=None):
        # We completely bypass list allocation here.
        self._task_wakeup = cb
        
    def remove_done_callback(self, cb):
        if self._task_wakeup == cb:
            self._task_wakeup = None
            
    def cancel(self, msg=None):
        pass
        
    def get_loop(self):
        import asyncio
        return asyncio.get_running_loop()

    def __await__(self):
        if self._awaitable is not None:
            return (yield from self._awaitable.__await__())
            
        if self._done:
            # Python 3.12 Eager fast-path: zero yields, returns immediately
            return self._result
            
        # Instead of while not self._done: yield self, we yield exactly once.
        # When bridging to Rust, we would pass <PyObject*>self into Rust.
        # Rust then pushes self to the ring buffer and writes to eventfd.
        
        self._asyncio_future_blocking = True
        yield self
        
        return self._result
        
    cdef void set_result(self, object result):
        self._result = result
        self._done = True
        if self._task_wakeup is not None:
            self._task_wakeup(self)
