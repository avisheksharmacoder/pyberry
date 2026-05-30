# cython: language_level=3
cdef enum FieldType:
    TYPE_INT = 1
    TYPE_FLOAT = 2
    TYPE_BOOL = 3
    TYPE_STR = 4
    TYPE_LIST = 5
    TYPE_DICT = 6
    TYPE_ANY = 7

cpdef dict compile_schema(object cls)
cpdef dict validate_data(dict schema, dict data)
