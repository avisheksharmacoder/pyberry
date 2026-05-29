# cython: language_level=3

cdef class Request:
    cdef public object scope
    cdef public object proto
    cdef public object _body
