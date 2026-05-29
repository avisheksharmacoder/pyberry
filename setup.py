import os
from setuptools import setup, Extension
from Cython.Build import cythonize

# Read the README for the PyPI long description
long_description = ""
if os.path.exists("docs/README.md"):
    with open("docs/README.md", "r", encoding="utf-8") as fh:
        long_description = fh.read()

extensions = [
    Extension("pyberry.core.request", ["src/pyberry/core/request.pyx"]),
    Extension("pyberry.core.response", ["src/pyberry/core/response.pyx"]),
    Extension("pyberry.core.router", ["src/pyberry/core/router.pyx"]),
    Extension("pyberry.core.security", ["src/pyberry/core/security.pyx"]),
    Extension("pyberry.core.future", ["src/pyberry/core/future.pyx"]),
    Extension("pyberry.core.rsgi", ["src/pyberry/core/rsgi.pyx"]),
    Extension("pyberry.core.logger", ["src/pyberry/core/logger.pyx"]),
]

setup(
    name="pyberry-framework",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A fast, compiled async web framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    package_dir={"": "src"},
    ext_modules=cythonize(
        extensions,
        compiler_directives={"language_level": "3"}
    ),
    entry_points={
        'console_scripts': [
            'pyberry=pyberry.cli:main',
        ],
    },
)
