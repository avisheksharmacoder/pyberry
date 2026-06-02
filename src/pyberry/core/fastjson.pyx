# cython: language_level=3
import cython
from cpython.unicode cimport PyUnicode_DecodeUTF8
from pyberry.core.fastjson cimport *
from pyberry.core.validation cimport TYPE_INT, TYPE_FLOAT, TYPE_BOOL, TYPE_STR, TYPE_LIST, TYPE_DICT, TYPE_ANY

cdef extern from "stdlib.h":
    void free(void *ptr)

cdef extern from "Python.h":
    void* PyDict_GetItemString(object p, const char *key)
    object _PyDict_NewPresized(Py_ssize_t minused)
    int PyObject_SetAttrString(object o, const char *attr_name, object v)
    const char* PyUnicode_AsUTF8AndSize(object unicode, Py_ssize_t *size)

cdef object _parse_val(yyjson_val *val):
    cdef yyjson_arr_iter arr_iter
    cdef yyjson_obj_iter obj_iter
    cdef yyjson_val *item
    cdef yyjson_val *key
    cdef yyjson_val *v
    cdef object py_key
    
    if val == NULL:
        return None
    if yyjson_is_null(val):
        return None
    if yyjson_is_bool(val):
        return True if yyjson_get_bool(val) else False
    if yyjson_is_int(val):
        return yyjson_get_sint(val)
    if yyjson_is_real(val):
        return yyjson_get_real(val)
    if yyjson_is_str(val):
        return PyUnicode_DecodeUTF8(yyjson_get_str(val), yyjson_get_len(val), "strict")
        
    if yyjson_is_arr(val):
        res_list = []
        yyjson_arr_iter_init(val, &arr_iter)
        item = yyjson_arr_iter_next(&arr_iter)
        while item != NULL:
            res_list.append(_parse_val(item))
            item = yyjson_arr_iter_next(&arr_iter)
        return res_list
        
    if yyjson_is_obj(val):
        res_dict = _PyDict_NewPresized(yyjson_obj_size(val))
        yyjson_obj_iter_init(val, &obj_iter)
        key = yyjson_obj_iter_next(&obj_iter)
        while key != NULL:
            v = yyjson_obj_iter_get_val(key)
            py_key = PyUnicode_DecodeUTF8(yyjson_get_str(key), yyjson_get_len(key), "strict")
            res_dict[py_key] = _parse_val(v)
            key = yyjson_obj_iter_next(&obj_iter)
        return res_dict
        
    return None

cpdef object loads(bytes data):
    cdef size_t length = len(data)
    cdef const char* c_data = data
    cdef yyjson_doc *doc = yyjson_read(c_data, length, 0)
    if doc == NULL:
        raise ValueError("Invalid JSON payload")
    
    cdef yyjson_val *root = yyjson_doc_get_root(doc)
    cdef object result = _parse_val(root)
    
    yyjson_doc_free(doc)
    return result

cpdef object parse_model(object p_type, dict schema, tuple req_fields, tuple def_fields, bytes data):
    from pyberry.exceptions import UnprocessableEntityException
    cdef size_t length = len(data)
    cdef const char* c_data = data
    cdef yyjson_doc *doc = yyjson_read(c_data, length, 0)
    if doc == NULL:
        raise UnprocessableEntityException("Invalid JSON payload")
        
    cdef yyjson_val *root = yyjson_doc_get_root(doc)
    if not yyjson_is_obj(root):
        yyjson_doc_free(doc)
        raise UnprocessableEntityException("Payload must be a JSON object")
        
    cdef object instance = p_type.__new__(p_type)
    
    cdef yyjson_obj_iter obj_iter
    yyjson_obj_iter_init(root, &obj_iter)
    cdef yyjson_val *key = yyjson_obj_iter_next(&obj_iter)
    cdef yyjson_val *v
    
    cdef object py_key
    cdef int type_enum
    cdef tuple meta
    cdef bint is_required
    cdef object py_val
    cdef const char* c_key
    cdef void* meta_ptr
    
    while key != NULL:
        v = yyjson_obj_iter_get_val(key)
        c_key = yyjson_get_str(key)
        meta_ptr = PyDict_GetItemString(schema, c_key)
        
        if meta_ptr != NULL:
            meta = <tuple>meta_ptr
            type_enum = meta[0]
            
            if type_enum == TYPE_INT:
                if not yyjson_is_int(v):
                    yyjson_doc_free(doc)
                    py_key = PyUnicode_DecodeUTF8(c_key, yyjson_get_len(key), "strict")
                    raise UnprocessableEntityException(f"Field '{py_key}' must be an integer")
                py_val = yyjson_get_sint(v)
            elif type_enum == TYPE_STR:
                if not yyjson_is_str(v):
                    yyjson_doc_free(doc)
                    py_key = PyUnicode_DecodeUTF8(c_key, yyjson_get_len(key), "strict")
                    raise UnprocessableEntityException(f"Field '{py_key}' must be a string")
                py_val = PyUnicode_DecodeUTF8(yyjson_get_str(v), yyjson_get_len(v), "strict")
            elif type_enum == TYPE_BOOL:
                if not yyjson_is_bool(v):
                    yyjson_doc_free(doc)
                    py_key = PyUnicode_DecodeUTF8(c_key, yyjson_get_len(key), "strict")
                    raise UnprocessableEntityException(f"Field '{py_key}' must be a boolean")
                py_val = True if yyjson_get_bool(v) else False
            elif type_enum == TYPE_FLOAT:
                if yyjson_is_real(v):
                    py_val = yyjson_get_real(v)
                elif yyjson_is_int(v):
                    py_val = <double>yyjson_get_sint(v)
                else:
                    yyjson_doc_free(doc)
                    py_key = PyUnicode_DecodeUTF8(c_key, yyjson_get_len(key), "strict")
                    raise UnprocessableEntityException(f"Field '{py_key}' must be a float")
            else:
                py_val = _parse_val(v)
                
            PyObject_SetAttrString(instance, c_key, py_val)
            
        key = yyjson_obj_iter_next(&obj_iter)
        
    for schema_key in req_fields:
        if not hasattr(instance, schema_key):
            yyjson_doc_free(doc)
            raise UnprocessableEntityException(f"Field '{schema_key}' is required")
            
    for schema_key, default_val in def_fields:
        if default_val is not None and not hasattr(instance, schema_key):
            setattr(instance, schema_key, default_val)
                
    yyjson_doc_free(doc)
    return instance

cdef yyjson_mut_val* _build_mut_val(yyjson_mut_doc *doc, object obj):
    cdef bytes encoded
    cdef bytes encoded_k
    cdef yyjson_mut_val *arr
    cdef yyjson_mut_val *o
    cdef Py_ssize_t str_size
    cdef const char* utf8_str
    
    if obj is None:
        return yyjson_mut_null(doc)
    if isinstance(obj, bool):
        return yyjson_mut_bool(doc, <bint>obj)
    if isinstance(obj, int):
        return yyjson_mut_sint(doc, <long long>obj)
    if isinstance(obj, float):
        return yyjson_mut_real(doc, <double>obj)
    if isinstance(obj, str):
        utf8_str = PyUnicode_AsUTF8AndSize(obj, &str_size)
        return yyjson_mut_strn(doc, utf8_str, str_size)
    if isinstance(obj, list) or isinstance(obj, tuple):
        arr = yyjson_mut_arr(doc)
        for item in obj:
            yyjson_mut_arr_append(arr, _build_mut_val(doc, item))
        return arr
    if isinstance(obj, dict):
        o = yyjson_mut_obj(doc)
        for k, v in obj.items():
            encoded_k = k.encode('utf-8') if isinstance(k, str) else str(k).encode('utf-8')
            yyjson_mut_obj_add(o, yyjson_mut_strn(doc, <const char*>encoded_k, len(encoded_k)), _build_mut_val(doc, v))
        return o
        
    # Fallback for unknown types
    encoded = str(obj).encode('utf-8')
    return yyjson_mut_strn(doc, <const char*>encoded, len(encoded))

cpdef bytes dumps(object obj):
    cdef yyjson_mut_doc *doc = yyjson_mut_doc_new(NULL)
    cdef yyjson_mut_val *root = _build_mut_val(doc, obj)
    yyjson_mut_doc_set_root(doc, root)
    
    cdef size_t out_len = 0
    cdef char* out_c = yyjson_mut_write(doc, 0, &out_len)
    
    cdef bytes result = out_c[:out_len]
    
    free(out_c)
    yyjson_mut_doc_free(doc)
    
    return result
