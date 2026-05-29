# cython: language_level=3

cdef class Response:
    cdef public int status
    cdef public list headers
    cdef public object body
