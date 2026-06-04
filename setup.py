import os
import sys
import shutil

# =============================================================================
# ENVIRONMENT CHECKS
# =============================================================================
# Check if Cargo (Rust) is installed
if not shutil.which("cargo"):
    print("\n" + "="*80)
    print("❌ ERROR: Rust/Cargo is not installed or not in PATH.")
    print("PyBerry-framework requires Rust to compile its high-performance extensions.")
    print("To install Rust, run:")
    print("    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh")
    print("Or visit: https://rustup.rs/")
    print("="*80 + "\n")
    sys.exit(1)

# Check if a C compiler is installed
compilers = ["gcc", "clang", "cc"]
if sys.platform == "win32":
    compilers.append("cl")

if not any(shutil.which(c) for c in compilers):
    print("\n" + "="*80)
    print("⚠️  WARNING: No C compiler found in PATH.")
    print("PyBerry-framework requires a C compiler to build its Cython extensions.")
    print("Depending on your OS, please install:")
    print("  - Linux:   `build-essential` (e.g., sudo apt install build-essential)")
    print("  - macOS:   Xcode Command Line Tools (run: xcode-select --install)")
    print("  - Windows: Microsoft Visual C++ Build Tools")
    print("="*80 + "\n")

# Allow PyO3 to build on Python 3.14 by suppressing the version check
os.environ["PYO3_USE_ABI3_FORWARD_COMPATIBILITY"] = "1"

from setuptools import setup, Extension
from setuptools_rust import RustExtension, Binding
from Cython.Build import cythonize

# Read the README for the PyPI long description
long_description = ""
if os.path.exists("docs/README.md"):
    with open("docs/README.md", "r", encoding="utf-8") as fh:
        long_description = fh.read()

# =============================================================================
# THREAD SANITIZER (TSan) INTEGRATION
# =============================================================================
# Detect if the developer or CI/CD is requesting a TSan build.
#
# IMPORTANT: TSan requires specific versions of GCC or Clang and WILL cause
# significant performance degradation when enabled. It should be used
# EXCLUSIVELY for testing and debugging, NEVER in production builds.
#
# How TSan applies to PyBerry:
# 1. Cython/C Files (.pyx, .c): 100% Fully Monitored
#    Any file compiled here with -fsanitize=thread is instrumented by TSan.
#    TSan injects checks around every memory read/write at the machine-code level.
#    This is critical for safety when the GIL is released (nogil), such as in
#    lock-free ring buffers (future.pyx) or background thread writes (logger.pyx).
#
# 2. Pure Python Files (.py): Monitored via the Interpreter Loop
#    Pure .py files are not compiled into machine code here. They are executed by
#    the CPython interpreter which (usually) is not compiled with TSan. Thus, TSan
#    cannot look inside pure Python objects to track individual object mutations.
#    However, they are naturally protected from low-level data races by the GIL.
#    When Python code calls into our instrumented Cython modules (e.g. passing a
#    payload to fastjson), TSan immediately takes control at that boundary.
# =============================================================================
USE_TSAN = os.environ.get("PYBERRY_TSAN", "0") == "1"

# Base compiler flags for extreme performance
compile_flags = ["-O3", "-march=native", "-ffast-math"]
link_flags = []

# If TSan is enabled, drop optimizations and inject sanitizers
if USE_TSAN:
    print("[PyBerry Build] WARNING: Compiling with ThreadSanitizer enabled. Performance will be degraded.")
    compile_flags = [
        "-fsanitize=thread", 
        "-g",                # Debug symbols for exact line numbers
        "-O1",               # Low optimization so the compiler doesn't hide the data race
        "-fPIC"
    ]
    link_flags = ["-fsanitize=thread"]

extensions = [
    Extension("pyberry.core.request", ["src/pyberry/core/request.pyx"]),
    Extension("pyberry.core.response", ["src/pyberry/core/response.pyx"]),
    Extension("pyberry.core.validation", ["src/pyberry/core/validation.pyx"]),
    Extension("pyberry.core.router", ["src/pyberry/core/router.pyx"]),
    Extension("pyberry.core.security", ["src/pyberry/core/security.pyx"]),
    Extension("pyberry.core.future", ["src/pyberry/core/future.pyx"]),
    Extension("pyberry.core.rsgi", ["src/pyberry/core/rsgi.pyx"]),
    Extension("pyberry.core.logger", ["src/pyberry/core/logger.pyx"]),
    Extension("pyberry.core.responses", ["src/pyberry/core/responses.pyx"]),
    Extension("pyberry.core.fastjson", ["src/pyberry/core/fastjson.pyx", "src/pyberry/core/vendor/yyjson/yyjson.c"]),
]

for ext in extensions:
    ext.extra_compile_args = compile_flags
    ext.extra_link_args = link_flags

setup(
    name="pyberry-framework",
    version="0.1.3",
    author="Avishek Sharma",
    author_email="avisheksharmacoder@gmail.com",
    description="A fast, Cython compiled async web framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    package_dir={"": "src"},
    packages=["pyberry", "pyberry.compiler", "pyberry.core"],
    ext_modules=cythonize(
        extensions,
        compiler_directives={
            "language_level": "3", 
            "boundscheck": not USE_TSAN, # Keep bounds checking if NOT using TSAN for safety, disable for pure speed
            "wraparound": False
        },
        force=True
    ),
    rust_extensions=[
        RustExtension("pyberry_rust", path="src/pyberry_rust/Cargo.toml", binding=Binding.PyO3)
    ],
    entry_points={
        'console_scripts': [
            'pyberry=pyberry.cli:main',
        ],
    },
)
