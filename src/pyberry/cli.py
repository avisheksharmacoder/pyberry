import argparse
import subprocess
import sys
import os

RED = "\033[91m"
GREEN = "\033[92m"
RESET = "\033[0m"

def init(args):
    app_dir = args.app
    if app_dir == ".":
        base_dir = os.getcwd()
    else:
        base_dir = os.path.join(os.getcwd(), app_dir)
        os.makedirs(base_dir, exist_ok=True)
    
    print(f"{GREEN}[pyberry] Initializing project in {base_dir}...{RESET}")
    
    # main.py
    main_code = """import sys
import os

from pyberry.core.rsgi import app

# The Granian entrypoint
# Run with: pyberry dev user_app.py
"""
    with open(os.path.join(base_dir, "main.py"), "w") as f:
        f.write(main_code)
        
    # user_app.py
    user_app_code = """from pyberry.core.responses import JSONResponse
from pyberry.app import get
from pyberry.core.request import Request

@get("/")
def index(req: Request):
    return JSONResponse({"status": "ok", "message": "Welcome to PyBerry!"})
"""
    with open(os.path.join(base_dir, "user_app.py"), "w") as f:
        f.write(user_app_code)
        
    # security.py
    security_code = """# security.py
# High-grade security configurations for PyBerry

# Allowed Hosts prevents Host Header Injection attacks (BadHost vulnerabilities).
# Only requests with a matching Host header will be processed.
# In production, replace "localhost" and "127.0.0.1" with your actual domain names.
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# Strict CORS policy
CORS_ENABLED = True

# Turn off for peak benchmarking (RPS)
LOGGING_ENABLED = True
"""
    with open(os.path.join(base_dir, "security.py"), "w") as f:
        f.write(security_code)
        
    # Create empty log file
    with open(os.path.join(base_dir, "berrypy.log"), "w") as f:
        pass
        
    print(f"{GREEN}[pyberry] Project initialized successfully!{RESET}")

def build(args):
    print(f"{GREEN}[pyberry] Building {args.app} for PRODUCTION...{RESET}")
    from pyberry.compiler.transpile import transpile_file
    
    base_dir = os.path.dirname(os.path.abspath(args.app))
    if not base_dir:
        base_dir = "."
    
    ignore_dirs = {".git", ".berry_build", "__pycache__", "venv", ".venv", "env", ".env", "src", "lib", "bin", "include", "share", ".pytest_cache"}
    py_files = []
    
    for root, dirs, files in os.walk(base_dir):
        dirs[:] = [d for d in dirs if d not in ignore_dirs and not d.startswith('.')]
        for file in files:
            if file.endswith(".py") and file != "setup.py":
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, base_dir)
                if "pyberry" in rel_path.split(os.sep):
                    continue
                py_files.append(rel_path)
                
    compiled_modules = []
    for rel_path in py_files:
        in_path = os.path.join(base_dir, rel_path)
        out_path = os.path.join(base_dir, ".berry_build", rel_path)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        try:
            transpile_file(in_path, out_path)
            # module name for Cython extension
            module_name = rel_path.replace(".py", "").replace(os.sep, ".")
            # Cython uses posix paths even on windows inside setup.py usually, but let's be safe
            compiled_modules.append((module_name, rel_path.replace("\\", "/")))
        except Exception as e:
            print(f"{RED}[WARNING] Failed to transpile {rel_path}: {e}{RESET}")
            
    # Save the entrypoint module name
    entry_module = os.path.relpath(os.path.abspath(args.app), base_dir).replace(".py", "").replace(os.sep, ".")
    with open(os.path.join(base_dir, ".berry_build", "entrypoint.txt"), "w") as f:
        f.write(entry_module)
    
    ext_list_str = "[\n"
    for mod_name, rel_path in compiled_modules:
        ext_list_str += f'        Extension("{mod_name}", ["{rel_path}"]),\n'
    ext_list_str += "    ]"
    
    setup_code = f"""
from setuptools import setup, Extension
from Cython.Build import cythonize

setup(
    ext_modules=cythonize(
{ext_list_str},
        compiler_directives={{"language_level": "3"}}
    ),
    script_args=["build_ext", "--inplace"]
)
"""
    with open(os.path.join(base_dir, ".berry_build", "setup.py"), "w") as f:
        f.write(setup_code)
        
    subprocess.run([sys.executable, "setup.py", "build_ext", "--inplace"], cwd=os.path.join(base_dir, ".berry_build"), check=True)
    print(f"{GREEN}[pyberry] Build complete! You can now run `pyberry run`{RESET}")

def run(args):
    print(f"{GREEN}[pyberry] Starting in PRODUCTION mode...{RESET}")
    env = os.environ.copy()
    env["PYTHON_GIL"] = "0"
    env["PYTHONPATH"] = "src:.:.berry_build"
    
    try:
        with open(".berry_build/entrypoint.txt", "r") as f:
            entry_module = f.read().strip()
    except FileNotFoundError:
        print(f"{RED}[ERROR] Could not find .berry_build/entrypoint.txt. Did you run `pyberry build` first?{RESET}")
        sys.exit(1)
    
    wrapper_code = f"""
import sys
import {entry_module}
from pyberry.core.rsgi import app
"""
    os.makedirs(".berry_build", exist_ok=True)
    with open(".berry_build/run_wrapper.py", "w") as f:
        f.write(wrapper_code)
        
    subprocess.run(["granian", "--interface", "rsgi", "--workers", str(args.workers), "run_wrapper:app"], env=env, check=True)

def dev(args):
    print(f"{RED}[pyberry] Starting in DEV mode (Hot Reloading)...{RESET}")
    env = os.environ.copy()
    env["PYTHON_GIL"] = "0"
    env["PYTHONPATH"] = "src:.:.berry_build"
    
    app_module = args.app.replace(".py", "").replace("/", ".")
    
    wrapper_code = f"""
import sys
import {app_module}
from pyberry.core.rsgi import app
"""
    os.makedirs(".berry_build", exist_ok=True)
    with open(".berry_build/dev_wrapper.py", "w") as f:
        f.write(wrapper_code)
        
    import sysconfig
    
    cmd = ["granian", "--interface", "rsgi", "--workers", "1"]
    if not sysconfig.get_config_var('Py_GIL_DISABLED'):
        cmd.append("--reload")
    else:
        print(f"{RED}[pyberry] Hot Reloading is disabled on free-threaded Python{RESET}")
    
    cmd.append("dev_wrapper:app")
    
    subprocess.run(cmd, env=env, check=True)

def check(args):
    import platform
    import shutil
    import sysconfig
    
    print(f"{GREEN}[pyberry] Checking system requirements...{RESET}")
    all_good = True
    
    # 1. Python version
    py_version = sys.version_info
    print(f"Python Version: {py_version.major}.{py_version.minor}.{py_version.micro}", end="")
    if py_version.major == 3 and py_version.minor >= 13:
        print(f" {GREEN}[OK]{RESET}")
    else:
        print(f" {RED}[WARNING] Python 3.13+ recommended for free-threading{RESET}")
        all_good = False
        
    # 2. Free-threading
    gil_disabled = sysconfig.get_config_var('Py_GIL_DISABLED')
    print("Free-threaded (GIL disabled):", end="")
    if gil_disabled:
        print(f" {GREEN}[OK]{RESET}")
    else:
        print(f" {RED}[WARNING] GIL is not disabled. Performance will be degraded.{RESET}")
        all_good = False
        
    # 3. Granian
    print("Granian installed:", end="")
    if shutil.which("granian"):
        print(f" {GREEN}[OK]{RESET}")
    else:
        print(f" {RED}[MISSING] Please run: pip install granian{RESET}")
        all_good = False
        
    # 4. Cython
    print("Cython installed:", end="")
    try:
        import cython
        print(f" {GREEN}[OK]{RESET}")
    except ImportError:
        print(f" {RED}[MISSING] Please run: pip install cython{RESET}")
        all_good = False
        
    # 5. C Compiler
    system = platform.system()
    if system == "Windows":
        print("C Compiler (MSVC):", end="")
        if shutil.which("cl"):
            print(f" {GREEN}[OK]{RESET}")
        else:
            print(f" {RED}[WARNING] MSVC 'cl.exe' not found in PATH.{RESET}")
            all_good = False
    else:
        print("C Compiler (GCC/Clang):", end="")
        if shutil.which("gcc") or shutil.which("clang"):
            print(f" {GREEN}[OK]{RESET}")
        else:
            print(f" {RED}[MISSING] gcc or clang not found.{RESET}")
            all_good = False
            
    if all_good:
        print(f"\n{GREEN}All systems go! PyBerry is ready to run at maximum speed.{RESET}")
    else:
        print(f"\n{RED}Some checks failed or generated warnings. PyBerry may not run optimally.{RESET}")

def main():
    parser = argparse.ArgumentParser(description="PyBerry CLI")
    subparsers = parser.add_subparsers(dest="command")
    
    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("app", help="Path to create the app in (e.g., . for current directory, or myapp)")
    
    build_parser = subparsers.add_parser("build")
    build_parser.add_argument("app", help="Path to your app file (e.g., user_app.py)")
    
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--workers", type=int, default=1, help="Number of worker processes")
    
    dev_parser = subparsers.add_parser("dev")
    dev_parser.add_argument("app", help="Path to your app file")
    
    check_parser = subparsers.add_parser("check")
    check_parser.description = "Check system requirements for PyBerry"
    
    args = parser.parse_args()
    
    if args.command == "init":
        init(args)
    elif args.command == "build":
        build(args)
    elif args.command == "run":
        run(args)
    elif args.command == "dev":
        dev(args)
    elif args.command == "check":
        check(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
