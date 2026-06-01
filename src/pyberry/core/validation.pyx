# cython: language_level=3
import cython
from pyberry.exceptions import UnprocessableEntityException
import dataclasses



cdef int _get_type_enum(object type_hint):
    if type_hint is int:
        return TYPE_INT
    elif type_hint is float:
        return TYPE_FLOAT
    elif type_hint is bool:
        return TYPE_BOOL
    elif type_hint is str:
        return TYPE_STR
    elif type_hint is list or getattr(type_hint, '__origin__', None) is list:
        return TYPE_LIST
    elif type_hint is dict or getattr(type_hint, '__origin__', None) is dict:
        return TYPE_DICT
    else:
        return TYPE_ANY

cpdef dict compile_schema(object cls):
    cdef dict schema = {}
    cdef object type_hints = getattr(cls, '__annotations__', {})
    
    if dataclasses.is_dataclass(cls):
        for field in dataclasses.fields(cls):
            name = field.name
            type_enum = _get_type_enum(field.type)
            has_default = field.default is not dataclasses.MISSING or field.default_factory is not dataclasses.MISSING
            # Dataclass instances handle their own defaults correctly at instantiation, 
            # so we just mark required=True/False and let Dataclass assign defaults.
            schema[name] = (type_enum, None, not has_default)
    else:
        for name, type_hint in type_hints.items():
            type_enum = _get_type_enum(type_hint)
            has_default = hasattr(cls, name)
            default_val = getattr(cls, name, None) if has_default else None
            schema[name] = (type_enum, default_val, not has_default)
            
    cdef list req_fields = []
    cdef list def_fields = []
    for schema_name, meta in schema.items():
        if meta[2]:
            req_fields.append(schema_name)
        else:
            def_fields.append((schema_name, meta[1]))
            
    cls._required_fields = tuple(req_fields)
    cls._default_fields = tuple(def_fields)
    return schema

cpdef dict validate_data(dict schema, dict data):
    cdef dict validated = {}
    cdef str name
    cdef tuple meta
    cdef int type_enum
    cdef object default_val
    cdef bint is_required
    cdef object val
    
    for name, meta in schema.items():
        type_enum = meta[0]
        default_val = meta[1]
        is_required = meta[2]
        
        if name in data:
            val = data[name]
            
            if type_enum == TYPE_INT:
                try:
                    val = int(val)
                except (ValueError, TypeError):
                    raise UnprocessableEntityException(f"Field '{name}' must be an integer")
            elif type_enum == TYPE_FLOAT:
                try:
                    val = float(val)
                except (ValueError, TypeError):
                    raise UnprocessableEntityException(f"Field '{name}' must be a float")
            elif type_enum == TYPE_BOOL:
                val = str(val).lower() in ('true', '1', 'yes', 't', 'y')
            elif type_enum == TYPE_STR:
                if type(val) is not str:
                    val = str(val)
            elif type_enum == TYPE_LIST:
                if type(val) is not list:
                    raise UnprocessableEntityException(f"Field '{name}' must be a list")
            elif type_enum == TYPE_DICT:
                if type(val) is not dict:
                    raise UnprocessableEntityException(f"Field '{name}' must be a dict")
                    
            validated[name] = val
        elif is_required:
            raise UnprocessableEntityException(f"Field '{name}' is required")
        else:
            if default_val is not None:
                validated[name] = default_val
                
    return validated

cdef dict _schema_cache = {}

cdef class BaseModel:
    def __init__(self, **kwargs):
        cdef dict schema
        if self.__class__ not in _schema_cache:
            _schema_cache[self.__class__] = compile_schema(self.__class__)
            
        schema = _schema_cache[self.__class__]
        validated = validate_data(schema, kwargs)
        for k, v in validated.items():
            setattr(self, k, v)
