# cython: language_level=3

cdef int validate_request(object scope, bint cors_enabled, list allowed_hosts, bint path_traversal_protection) except *
cdef int check_rate_limit(str ip, int max_req, int window) except *
