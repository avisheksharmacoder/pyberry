# cython: language_level=3

cdef int validate_request(object scope, bint cors_enabled, list allowed_hosts) except *
