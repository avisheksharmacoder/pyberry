import os
import sys
import shutil

# =============================================================================
# ENVIRONMENT CHECKS
# =============================================================================
if sys.platform == "win32":
    has_cargo = shutil.which("cargo") is not None
    has_c_compiler = any(shutil.which(c) for c in ["cl", "gcc", "clang", "cc"])
    
    if not has_cargo or not has_c_compiler:
        missing_tools = []
        if not has_cargo:
            missing_tools.append("Rust Toolchain")
        if not has_c_compiler:
            missing_tools.append("Microsoft Visual C++ Build Tools")
            
        print("\n" + "="*80)
        print(f"WINDOWS INSTALLATION PREREQUISITES MISSING: {', '.join(missing_tools)}")
        print("PyBerry requires the following tools to compile its extensions from source:")
        print("")
        if not has_cargo:
            print("1. Rust Toolchain: Download from https://rustup.rs/")
            print("   - Run rustup-init.exe and proceed with the default installation.")
            print("")
        if not has_c_compiler:
            print("2. Microsoft Visual C++ Build Tools:")
            print("   - Download from https://visualstudio.microsoft.com/visual-cpp-build-tools/")
            print("   - Run the installer and select 'Desktop development with C++'.")
            print("")
        print("After installing the required tools, you MUST RESTART YOUR TERMINAL before retrying.")
        print("="*80 + "\n")
        sys.exit(1)
else:
    # Check if Cargo (Rust) is installed (Linux/macOS)
    if not shutil.which("cargo"):
        print("\n" + "="*80)
        print("ERROR: Rust/Cargo is not installed or not in PATH.")
        print("PyBerry-framework requires Rust to compile its high-performance extensions.")
        print("To install Rust, run:")
        print("    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh")
        print("="*80 + "\n")
        sys.exit(1)

    # Check if a C compiler is installed (Linux/macOS)
    compilers = ["gcc", "clang", "cc"]
    if not any(shutil.which(c) for c in compilers):
        print("\n" + "="*80)
        print("WARNING: No C compiler found in PATH.")
        print("PyBerry-framework requires a C compiler to build its Cython extensions.")
        print("Depending on your OS, please install:")
        print("  - Linux:   `build-essential` (e.g., sudo apt install build-essential)")
        print("  - macOS:   Xcode Command Line Tools (run: xcode-select --install)")
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


# Base compiler flags for extreme performance
if sys.platform == "win32":
    compile_flags = ["/std:c11", "/experimental:c11atomics"]
else:
    compile_flags = ["-O3", "-march=native", "-ffast-math"]
link_flags = []

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
    version="0.1.8",
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
            "boundscheck": True,
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
