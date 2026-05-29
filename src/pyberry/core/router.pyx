# cython: language_level=3
import re
import inspect
from libc.stdlib cimport malloc, free, realloc
from libc.string cimport strdup, strcmp, strncmp, strlen

cdef RadixNode* create_node(const char* path, bint is_param):
    cdef RadixNode* node = <RadixNode*>malloc(sizeof(RadixNode))
    if node == NULL:
        raise MemoryError()
    node.path = strdup(path)
    node.handler = NULL
    node.children = NULL
    node.num_children = 0
    node.is_param = is_param
    return node

cdef void free_node(RadixNode* node):
    if node == NULL:
        return
    free(node.path)
    cdef int i
    for i in range(node.num_children):
        free_node(node.children[i])
    if node.children != NULL:
        free(node.children)
    free(node)

# Simple Segment-based Trie (often called a Radix tree in routers)
cdef void insert(RadixNode* root, const char* path, EndpointFunc handler):
    cdef RadixNode* current = root
    cdef const char* p = path
    # If path is "/", handle it directly on root
    if strcmp(path, "/") == 0:
        root.handler = handler
        return

    # Skip first slash
    if p[0] == b'/':
        p += 1

    cdef const char* next_slash
    cdef int segment_len
    cdef char* segment
    cdef bint is_param
    cdef int i
    cdef bint found_child

    while p[0] != b'\0':
        next_slash = p
        while next_slash[0] != b'\0' and next_slash[0] != b'/':
            next_slash += 1
            
        segment_len = next_slash - p
        segment = <char*>malloc(segment_len + 1)
        for i in range(segment_len):
            segment[i] = p[i]
        segment[segment_len] = b'\0'
        
        is_param = 0
        if segment_len > 0 and segment[0] == b'{':
            is_param = 1

        found_child = 0
        for i in range(current.num_children):
            if current.children[i].is_param == is_param:
                if is_param or strcmp(current.children[i].path, segment) == 0:
                    current = current.children[i]
                    found_child = 1
                    free(segment)
                    break
        
        if not found_child:
            # Add new child
            if current.num_children == 0:
                current.children = <RadixNode**>malloc(sizeof(RadixNode*))
            else:
                current.children = <RadixNode**>realloc(current.children, (current.num_children + 1) * sizeof(RadixNode*))
            
            current.children[current.num_children] = create_node(segment, is_param)
            current.num_children += 1
            current = current.children[current.num_children - 1]
            free(segment)
            
        if next_slash[0] == b'\0':
            break
        p = next_slash + 1

    current.handler = handler

cdef EndpointFunc search(RadixNode* root, const char* path):
    cdef RadixNode* current = root
    cdef const char* p = path
    if strcmp(path, "/") == 0:
        return root.handler

    if p[0] == b'/':
        p += 1

    cdef const char* next_slash
    cdef int segment_len
    cdef char* segment
    cdef int i
    cdef bint found_child

    while p[0] != b'\0':
        next_slash = p
        while next_slash[0] != b'\0' and next_slash[0] != b'/':
            next_slash += 1
            
        segment_len = next_slash - p
        segment = <char*>malloc(segment_len + 1)
        for i in range(segment_len):
            segment[i] = p[i]
        segment[segment_len] = b'\0'

        found_child = 0
        for i in range(current.num_children):
            if current.children[i].is_param or strcmp(current.children[i].path, segment) == 0:
                current = current.children[i]
                found_child = 1
                break
        
        free(segment)
        
        if not found_child:
            return NULL
            
        if next_slash[0] == b'\0':
            break
        p = next_slash + 1

    return current.handler

cdef class Router:
    def __cinit__(self):
        self.get_tree = create_node("/", 0)
        self.post_tree = create_node("/", 0)
        self.put_tree = create_node("/", 0)
        self.delete_tree = create_node(b"/", 0)
        self.patch_tree = create_node(b"/", 0)
        self.python_routes = {}
        self.exact_routes = {}

    def add_python_route(self, method, path, handler):
        import dataclasses
        from pyberry.core.validation import compile_schema
            
        # Extract parameter metadata
        sig = inspect.signature(handler)
        param_meta = {}
        for name, param in sig.parameters.items():
            if name != "req":
                p_type = param.annotation
                schema = None
                if dataclasses.is_dataclass(p_type):
                    schema = compile_schema(p_type)
                param_meta[name] = (p_type, schema)
                
        # Optimize exact routes (O(1) lookup)
        if "{" not in path:
            self.exact_routes[(method, path)] = (handler, {}, param_meta)
            return
            
        if method not in self.python_routes:
            self.python_routes[method] = []
            
        # Convert path variables like {user_id} into regex named capture groups
        # e.g. "/user/{user_id}" -> "^/user/(?P<user_id>[^/]+)$"
        pattern_str = "^" + re.sub(r"\{([^}]+)\}", r"(?P<\1>[^/]+)", path) + "$"
        pattern = re.compile(pattern_str)
        
        self.python_routes[method].append((pattern, handler, param_meta))

    def match_python_route(self, method, path):
        exact = self.exact_routes.get((method, path))
        if exact is not None:
            return exact[0], exact[1], exact[2]
            
        routes = self.python_routes.get(method, [])
        for pattern, handler, param_meta in routes:
            match = pattern.match(path)
            if match:
                return handler, match.groupdict(), param_meta
        return None, None, None

    def __dealloc__(self):
        free_node(self.get_tree)
        free_node(self.post_tree)
        free_node(self.put_tree)
        free_node(self.delete_tree)
        free_node(self.patch_tree)

    cdef void add_route(self, str method, str path, EndpointFunc handler):
        cdef bytes b_path = path.encode('utf-8')
        cdef const char* c_path = b_path
        if method == "GET":
            insert(self.get_tree, c_path, handler)
        elif method == "POST":
            insert(self.post_tree, c_path, handler)
        elif method == "PUT":
            insert(self.put_tree, c_path, handler)
        elif method == "DELETE":
            insert(self.delete_tree, c_path, handler)
        elif method == "PATCH":
            insert(self.patch_tree, c_path, handler)

    cdef EndpointFunc get_route(self, str method, str path):
        cdef bytes b_path = path.encode('utf-8')
        cdef const char* c_path = b_path
        if method == "GET":
            return search(self.get_tree, c_path)
        elif method == "POST":
            return search(self.post_tree, c_path)
        elif method == "PUT":
            return search(self.put_tree, c_path)
        elif method == "DELETE":
            return search(self.delete_tree, c_path)
        elif method == "PATCH":
            return search(self.patch_tree, c_path)
        return NULL
