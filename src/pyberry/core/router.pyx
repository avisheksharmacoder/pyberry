# cython: language_level=3
import inspect
from libc.stdlib cimport malloc, free, realloc
from libc.string cimport strdup, strcmp, strncmp, strlen
from cpython.ref cimport PyObject, Py_INCREF, Py_DECREF

cdef extern from "Python.h":
    const char* PyUnicode_AsUTF8(object unicode)
    object PyUnicode_FromStringAndSize(const char *u, Py_ssize_t size)

cdef RadixNode* create_node(const char* path, bint is_param):
    cdef int i, length
    cdef RadixNode* node = <RadixNode*>malloc(sizeof(RadixNode))
    if node == NULL:
        raise MemoryError()
    node.path = strdup(path)
    node.handler = NULL
    node.route_id = 0
    node.children = NULL
    node.num_children = 0
    node.is_param = is_param
    node.param_name = NULL
    node.py_param_name = NULL

    if is_param:
        length = strlen(path)
        if length > 2 and path[0] == b'{' and path[length-1] == b'}':
            node.param_name = <char*>malloc(length - 1)
            for i in range(length - 2):
                node.param_name[i] = path[i+1]
            node.param_name[length-2] = b'\0'
        else:
            node.param_name = strdup(path)
            
        py_name = node.param_name.decode('utf-8')
        node.py_param_name = <PyObject*>py_name
        Py_INCREF(<object>node.py_param_name)
            
    return node

cdef void free_node(RadixNode* node):
    if node == NULL:
        return
    free(node.path)
    if node.param_name != NULL:
        free(node.param_name)
    if node.py_param_name != NULL:
        Py_DECREF(<object>node.py_param_name)
    cdef int i
    for i in range(node.num_children):
        free_node(node.children[i])
    if node.children != NULL:
        free(node.children)
    free(node)

cdef RadixNode* _insert_node(RadixNode* root, const char* path):
    cdef RadixNode* current = root
    cdef const char* p = path
    if strcmp(path, "/") == 0:
        return root

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

    return current

cdef void insert(RadixNode* root, const char* path, EndpointFunc handler):
    cdef RadixNode* node = _insert_node(root, path)
    node.handler = handler

cdef void insert_python_route(RadixNode* root, const char* path, int route_id):
    cdef RadixNode* node = _insert_node(root, path)
    node.route_id = route_id

cdef EndpointFunc search(RadixNode* root, const char* path):
    cdef RadixNode* current = root
    cdef const char* p = path
    if strcmp(path, "/") == 0:
        return root.handler

    if p[0] == b'/':
        p += 1

    cdef const char* next_slash
    cdef int segment_len
    cdef int i
    cdef bint found_child

    while p[0] != b'\0':
        next_slash = p
        while next_slash[0] != b'\0' and next_slash[0] != b'/':
            next_slash += 1
            
        segment_len = next_slash - p

        found_child = 0
        for i in range(current.num_children):
            if current.children[i].is_param or (strncmp(current.children[i].path, p, segment_len) == 0 and current.children[i].path[segment_len] == b'\0'):
                current = current.children[i]
                found_child = 1
                break
        
        if not found_child:
            return NULL
            
        if next_slash[0] == b'\0':
            break
        p = next_slash + 1

    return current.handler

cdef int search_python_route(RadixNode* root, const char* path, dict out_params):
    cdef RadixNode* current = root
    cdef const char* p = path
    if strcmp(path, "/") == 0:
        return root.route_id

    if p[0] == b'/':
        p += 1

    cdef const char* next_slash
    cdef int segment_len
    cdef int i
    cdef bint found_child
    cdef object decoded_val

    while p[0] != b'\0':
        next_slash = p
        while next_slash[0] != b'\0' and next_slash[0] != b'/':
            next_slash += 1
            
        segment_len = next_slash - p

        found_child = 0
        for i in range(current.num_children):
            if current.children[i].is_param or (strncmp(current.children[i].path, p, segment_len) == 0 and current.children[i].path[segment_len] == b'\0'):
                if current.children[i].is_param and current.children[i].param_name != NULL:
                    decoded_val = PyUnicode_FromStringAndSize(p, segment_len)
                    out_params[<object>current.children[i].py_param_name] = decoded_val
                current = current.children[i]
                found_child = 1
                break
        
        if not found_child:
            return 0
            
        if next_slash[0] == b'\0':
            break
        p = next_slash + 1

    return current.route_id

cdef class Router:
    def __cinit__(self):
        self.get_tree = create_node("/", 0)
        self.post_tree = create_node("/", 0)
        self.put_tree = create_node("/", 0)
        self.delete_tree = create_node(b"/", 0)
        self.patch_tree = create_node(b"/", 0)
        self.python_routes_map = {}
        self.next_route_id = 1
        self.exact_routes = {"GET": {}, "POST": {}, "PUT": {}, "DELETE": {}, "PATCH": {}}

    def add_python_route(self, method, path, handler):
        import dataclasses
        from pyberry.core.validation import compile_schema
            
        sig = inspect.signature(handler)
        param_meta_list = []
        for name, param in sig.parameters.items():
            if name != "req":
                p_type = param.annotation
                schema = None
                
                if dataclasses.is_dataclass(p_type):
                    schema = compile_schema(p_type)
                elif hasattr(p_type, "_schema") or (hasattr(p_type, "__bases__") and any(b.__name__ == 'BaseModel' for b in getattr(p_type, "__bases__", []))):
                    schema = getattr(p_type, "_schema", None)
                    if schema is None:
                        schema = compile_schema(p_type)
                        
                param_meta_list.append((name, p_type, schema))
                
        param_meta = tuple(param_meta_list)
        needs_req = "req" in sig.parameters
                
        if "{" not in path:
            if method not in self.exact_routes:
                self.exact_routes[method] = {}
            self.exact_routes[method][path] = (handler, {}, param_meta, needs_req)
            return
            
        cdef int route_id = self.next_route_id
        self.next_route_id += 1
        self.python_routes_map[route_id] = (handler, param_meta, needs_req)

        cdef bytes b_path = path.encode('utf-8')
        cdef const char* c_path = b_path
        if method == "GET":
            insert_python_route(self.get_tree, c_path, route_id)
        elif method == "POST":
            insert_python_route(self.post_tree, c_path, route_id)
        elif method == "PUT":
            insert_python_route(self.put_tree, c_path, route_id)
        elif method == "DELETE":
            insert_python_route(self.delete_tree, c_path, route_id)
        elif method == "PATCH":
            insert_python_route(self.patch_tree, c_path, route_id)

    def match_python_route(self, method, path):
        exact_method = self.exact_routes.get(method)
        if exact_method is not None:
            exact = exact_method.get(path)
            if exact is not None:
                return exact[0], exact[1], exact[2], exact[3]
            
        cdef dict out_params = {}
        cdef const char* c_path = PyUnicode_AsUTF8(path)
        cdef int route_id = 0
        if method == "GET":
            route_id = search_python_route(self.get_tree, c_path, out_params)
        elif method == "POST":
            route_id = search_python_route(self.post_tree, c_path, out_params)
        elif method == "PUT":
            route_id = search_python_route(self.put_tree, c_path, out_params)
        elif method == "DELETE":
            route_id = search_python_route(self.delete_tree, c_path, out_params)
        elif method == "PATCH":
            route_id = search_python_route(self.patch_tree, c_path, out_params)
            
        if route_id > 0:
            handler, param_meta, needs_req = self.python_routes_map[route_id]
            return handler, out_params, param_meta, needs_req
            
        return None, None, None, False

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
        cdef const char* c_path = PyUnicode_AsUTF8(path)
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
