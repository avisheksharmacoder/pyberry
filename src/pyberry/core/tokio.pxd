# cython: language_level=3

cdef extern from *:
    ctypedef void (*rust_waker_cb)(void* task_ctx)
    void submit_tokio_io(void* io_payload, rust_waker_cb cb, void* task_ctx)
