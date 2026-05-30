# cython: language_level=3
from libc.stdint cimport uint32_t

cdef extern from "vendor/yyjson/yyjson.h":
    ctypedef struct yyjson_doc:
        pass
    ctypedef struct yyjson_val:
        pass
    ctypedef struct yyjson_mut_doc:
        pass
    ctypedef struct yyjson_mut_val:
        pass
    ctypedef struct yyjson_arr_iter:
        pass
    ctypedef struct yyjson_obj_iter:
        pass

    yyjson_doc *yyjson_read(const char *dat, size_t len, uint32_t flg)
    void yyjson_doc_free(yyjson_doc *doc)
    yyjson_val *yyjson_doc_get_root(yyjson_doc *doc)

    bint yyjson_is_null(yyjson_val *val)
    bint yyjson_is_bool(yyjson_val *val)
    bint yyjson_is_int(yyjson_val *val)
    bint yyjson_is_real(yyjson_val *val)
    bint yyjson_is_str(yyjson_val *val)
    bint yyjson_is_arr(yyjson_val *val)
    bint yyjson_is_obj(yyjson_val *val)

    bint yyjson_get_bool(yyjson_val *val)
    long long yyjson_get_sint(yyjson_val *val)
    double yyjson_get_real(yyjson_val *val)
    const char *yyjson_get_str(yyjson_val *val)
    size_t yyjson_get_len(yyjson_val *val)
    
    bint yyjson_arr_iter_init(yyjson_val *arr, yyjson_arr_iter *iter)
    yyjson_val *yyjson_arr_iter_next(yyjson_arr_iter *iter)

    bint yyjson_obj_iter_init(yyjson_val *obj, yyjson_obj_iter *iter)
    yyjson_val *yyjson_obj_iter_next(yyjson_obj_iter *iter)
    yyjson_val *yyjson_obj_iter_get_val(yyjson_val *key)

    yyjson_mut_doc *yyjson_mut_doc_new(yyjson_mut_doc *parent)
    void yyjson_mut_doc_free(yyjson_mut_doc *doc)

    yyjson_mut_val *yyjson_mut_null(yyjson_mut_doc *doc)
    yyjson_mut_val *yyjson_mut_bool(yyjson_mut_doc *doc, bint val)
    yyjson_mut_val *yyjson_mut_sint(yyjson_mut_doc *doc, long long val)
    yyjson_mut_val *yyjson_mut_real(yyjson_mut_doc *doc, double val)
    yyjson_mut_val *yyjson_mut_strn(yyjson_mut_doc *doc, const char *str, size_t len)
    yyjson_mut_val *yyjson_mut_arr(yyjson_mut_doc *doc)
    yyjson_mut_val *yyjson_mut_obj(yyjson_mut_doc *doc)
    
    bint yyjson_mut_arr_append(yyjson_mut_val *arr, yyjson_mut_val *val)
    bint yyjson_mut_obj_add(yyjson_mut_val *obj, yyjson_mut_val *key, yyjson_mut_val *val)
    void yyjson_mut_doc_set_root(yyjson_mut_doc *doc, yyjson_mut_val *root)
    char *yyjson_mut_write(yyjson_mut_doc *doc, uint32_t flg, size_t *len)
