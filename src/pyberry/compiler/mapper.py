# Type Mapping Engine for Python to Cython Pure Python Mode

TYPE_MAPPING = {
    "int": "cython.int",
    "float": "cython.double",
    "bool": "cython.bint",
    "str": "str",  # Cython handles str as python string or unicode
}
