# cython: language_level=3
from pyberry.core.request cimport Request
from cpython.ref cimport PyObject

ctypedef object (*EndpointFunc)(Request req)

cdef struct RadixNode:
    char* path
    EndpointFunc handler
    int route_id
    RadixNode** children
    int num_children
    bint is_param
    char* param_name
    PyObject* py_param_name

cdef struct ExtractedParam:
    PyObject* key
    const char* val_ptr
    int val_len

cdef RadixNode* create_node(const char* path, bint is_param)
cdef void free_node(RadixNode* node)
cdef void insert(RadixNode* root, const char* path, EndpointFunc handler)
cdef void insert_python_route(RadixNode* root, const char* path, int route_id)
cdef EndpointFunc search(RadixNode* root, const char* path)
cdef int search_python_route(RadixNode* root, const char* path, ExtractedParam* params, int* num_params)

cdef class Router:
    cdef RadixNode* get_tree
    cdef RadixNode* post_tree
    cdef RadixNode* put_tree
    cdef RadixNode* delete_tree
    cdef RadixNode* patch_tree
    cdef public dict python_routes_map
    cdef public int next_route_id
    cdef public dict exact_routes
    
    cdef void add_route(self, str method, str path, EndpointFunc handler)
    cdef EndpointFunc get_route(self, str method, str path)
