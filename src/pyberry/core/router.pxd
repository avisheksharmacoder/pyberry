# cython: language_level=3
from pyberry.core.request cimport Request

ctypedef object (*EndpointFunc)(Request req)

cdef struct RadixNode:
    char* path
    EndpointFunc handler
    RadixNode** children
    int num_children
    bint is_param

cdef RadixNode* create_node(const char* path, bint is_param)
cdef void free_node(RadixNode* node)
cdef void insert(RadixNode* root, const char* path, EndpointFunc handler)
cdef EndpointFunc search(RadixNode* root, const char* path)

cdef class Router:
    cdef RadixNode* get_tree
    cdef RadixNode* post_tree
    cdef RadixNode* put_tree
    cdef RadixNode* delete_tree
    cdef RadixNode* patch_tree
    cdef public dict python_routes
    cdef public dict exact_routes
    
    cdef void add_route(self, str method, str path, EndpointFunc handler)
    cdef EndpointFunc get_route(self, str method, str path)
