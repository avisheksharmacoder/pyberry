# cython: language_level=3
# -----------------------------------------------------------------------------
# Compilation:
# 1. Create a setup.py:
#    from setuptools import setup, Extension
#    from Cython.Build import cythonize
#    setup(ext_modules=cythonize(Extension("11_cython_hello_world", ["11_cython_hello_world.pyx"]), compiler_directives={"language_level": "3", "freethreading_compatible": True}))
# 2. Run: python setup.py build_ext --inplace
# 3. Import in your main.py to register the route.
# -----------------------------------------------------------------------------

from pyberry.core.rsgi cimport router as _router

cdef object hello_world_cython(object scope, object proto):
    # Pure C-speed execution, no python dict allocation
    cdef str my_body = "Hello World from Cython!"
    
    # Write directly to Granian's Rust proto buffer (must use strings for headers)
    proto.response_str(
        status=200, 
        headers=[('content-type', 'text/plain')], 
        body=my_body
    )
    
    # Must return integer status code for PyBerry's access logger
    return 200

# Register directly into the Radix Tree (cdef functions cannot use @app.get)
_router.add_route("GET", "/hello-cython", hello_world_cython)
