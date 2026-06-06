import argparse
import subprocess
import sys
import os
import shutil

RED = "\033[91m"
GREEN = "\033[92m"
RESET = "\033[0m"

def create_app(args):
    app_dir = args.app
    if app_dir == ".":
        base_dir = os.getcwd()
    else:
        base_dir = os.path.join(os.getcwd(), app_dir)
        os.makedirs(base_dir, exist_ok=True)
        
    # Create db folder
    os.makedirs(os.path.join(base_dir, "db"), exist_ok=True)
    os.makedirs(os.path.join(base_dir, "tests"), exist_ok=True) # Create tests folder by default
    
    print(f"{GREEN}[pyberry] Initializing project in {base_dir}...{RESET}")
    
    # main.py
    main_code = """import sys
import os

from pyberry.core.rsgi import app
from pyberry.core.responses import JSONResponse
from pyberry.app import get
from pyberry.core.request import Request
from pyberry.db import db

@get("/")
def index(req: Request):
    return JSONResponse({"status": "ok", "message": "Welcome to PyBerry!"})

@get("/users")
async def get_users(req: Request):
    # Example database query using the global db connection pool
    try:
        # Assuming you've run `pyberry migrate` to create the users table
        users = await db.query("SELECT * FROM users")
        return JSONResponse({"status": "ok", "users": users})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status=500)
"""
    with open(os.path.join(base_dir, "main.py"), "w") as f:
        f.write(main_code)

    # tests/test_app.py
    test_code = """def test_example():
    assert True
"""
    with open(os.path.join(base_dir, "tests", "test_app.py"), "w") as f:
        f.write(test_code)
        
    # security.py
    security_code = """# security.py
# High-grade security configurations for PyBerry

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
CORS_ENABLED = True
CORS_ALLOWED_ORIGINS = []
LOGGING_ENABLED = True
SECURITY_HEADERS_ENABLED = True
HSTS_MAX_AGE = 31536000
X_FRAME_OPTIONS = "DENY"
CONTENT_SECURITY_POLICY = "default-src 'self'"
MAX_BODY_SIZE = 1048576  # 1MB
PATH_TRAVERSAL_PROTECTION = True
RATE_LIMIT_ENABLED = False
RATE_LIMIT_REQUESTS = 100
RATE_LIMIT_WINDOW = 60
LIBSQL_URL = "file:db/local.db"
LIBSQL_AUTH_TOKEN = None
"""
    with open(os.path.join(base_dir, "security.py"), "w") as f:
        f.write(security_code)
        
    # db/initial_schema.sql
    schema_code = """-- Example schema for pyberry migrate
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL
);

INSERT INTO users (name, email) VALUES ('Alice', 'alice@example.com') ON CONFLICT DO NOTHING;
"""
    with open(os.path.join(base_dir, "db", "initial_schema.sql"), "w") as f:
        f.write(schema_code)
        
    # docs.md
    docs_code = """# PyBerry Project Documentation

Welcome to your new PyBerry application!

## The 3-Tier CLI Lifecycle

Here are the main commands you must use with your PyBerry project to guarantee memory safety:

- **`pyberry run main.py --dev`**: The Playground. Start the development server with hot-reloading. The GIL handles Python memory safety.
- **`pyberry build main.py --audit`**: The Crucible. Mandatory before deployment. Transpiles your code and runs ThreadSanitizer (TSan) against your `tests/` folder. Generates a `build.lock` on success.
- **`pyberry start --prod`**: The Rocket. Deploys the optimized server, but ONLY if the `build.lock` audit tag exists.
- **`pyberry migrate`**: Run the `db/initial_schema.sql` file to setup your database.
"""
    with open(os.path.join(base_dir, "docs.md"), "w") as f:
        f.write(docs_code)
        
    # Create empty log file
    with open(os.path.join(base_dir, "berrypy.log"), "w") as f:
        pass
        
    print(f"{GREEN}[pyberry] Project initialized successfully!{RESET}")


def run(args):
    if not getattr(args, "dev", False):
        print(f"{RED}[ERROR] Please use `pyberry run <app> --dev` for the Playground mode, or `pyberry start --prod` for deployment.{RESET}")
        sys.exit(1)
        
    print(f"{GREEN}[pyberry] Starting in DEV mode (The Playground)...{RESET}")
    print(f"{GREEN}  - Server:      Granian{RESET}")
    print(f"{GREEN}  - Workers:     1{RESET}")
    print(f"{GREEN}  - Event Loop:  uvloop{RESET}")
    print(f"{GREEN}  - Interface:   RSGI{RESET}")
    env = os.environ.copy()
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
    is_free_threaded = bool(sysconfig.get_config_var("Py_GIL_DISABLED"))
    
    cmd = ["granian", "--interface", "rsgi", "--workers", "1", "--loop", "uvloop"]
    if not is_free_threaded:
        cmd.append("--reload")
    else:
        print(f"{RED}[WARNING] Hot reloading (--reload) is disabled on free-threaded Python builds.{RESET}")
    
    cmd.append("dev_wrapper:app")
    
    subprocess.run(cmd, env=env, check=True)


def build(args):
    if not getattr(args, "audit", False):
        print(f"{RED}[ERROR] You must pass the --audit flag (`pyberry build <app> --audit`) to run the mandatory TSan Crucible Audit.{RESET}")
        sys.exit(1)
        
    base_dir = os.path.dirname(os.path.abspath(args.app))
    if not base_dir:
        base_dir = "."
        
    tests_dir = os.path.join(base_dir, "tests")
    if not os.path.exists(tests_dir) or not os.path.isdir(tests_dir):
        print(f"{RED}[ERROR] A 'tests/' directory is required in your project root to run the TSan audit.{RESET}")
        print(f"{RED}Please create a 'tests/' folder with your pytest code and try again.{RESET}")
        sys.exit(1)

    print(f"{GREEN}[pyberry] Building {args.app} for AUDIT (The Crucible)...{RESET}")
    from pyberry.compiler.transpile import transpile_file
    
    ignore_dirs = {".git", ".berry_build", "__pycache__", "venv", ".venv", "env", ".env", "src", "lib", "bin", "include", "share", ".pytest_cache", "tests"}
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
            module_name = rel_path.replace(".py", "").replace(os.sep, ".")
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
import os

compile_flags = ["-fsanitize=thread", "-g", "-O1", "-fPIC"] if os.environ.get("PYBERRY_TSAN", "0") == "1" else ["-O3", "-march=native", "-ffast-math"]
link_flags = ["-fsanitize=thread"] if os.environ.get("PYBERRY_TSAN", "0") == "1" else []

extensions = {ext_list_str}
for ext in extensions:
    ext.extra_compile_args = compile_flags
    ext.extra_link_args = link_flags

setup(
    ext_modules=cythonize(
        extensions,
        compiler_directives={{"language_level": "3"}},
        force=True
    ),
    script_args=["build_ext", "--inplace"]
)
"""
    with open(os.path.join(base_dir, ".berry_build", "setup.py"), "w") as f:
        f.write(setup_code)
        
    print(f"{GREEN}[pyberry] Compiling with ThreadSanitizer enabled...{RESET}")
    env = os.environ.copy()
    env["PYBERRY_TSAN"] = "1"
    subprocess.run([sys.executable, "setup.py", "build_ext", "--inplace"], cwd=os.path.join(base_dir, ".berry_build"), env=env, check=True)
    
    print(f"{GREEN}[pyberry] Running TSan Crucible Audit on test suite...{RESET}")
    pytest_env = os.environ.copy()
    pytest_env["PYTHONPATH"] = f"{os.path.join(base_dir, '.berry_build')}:{base_dir}"
    
    cli_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(os.path.dirname(cli_dir)) 
    supp_path = os.path.join(root_dir, "tsan_suppressions.txt")
    
    tsan_opts = "halt_on_error=1 history_size=7"
    if os.path.exists(supp_path):
        tsan_opts = f"suppressions={supp_path} " + tsan_opts
        
    pytest_env["TSAN_OPTIONS"] = tsan_opts
    
    result = subprocess.run([sys.executable, "-m", "pytest", "tests/"], cwd=base_dir, env=pytest_env)
    
    if result.returncode == 0:
        print(f"{GREEN}[pyberry] Audit passed! Zero data races detected. Generating build.lock...{RESET}")
        with open(os.path.join(base_dir, ".berry_build", "build.lock"), "w") as f:
            f.write("PASSED_TSAN_AUDIT")
    else:
        print(f"{RED}[ERROR] TSan Audit failed! Data races detected in the application.{RESET}")
        sys.exit(1)


def start(args):
    if not getattr(args, "prod", False):
        print(f"{RED}[ERROR] Please use `pyberry start --prod` to deploy.{RESET}")
        sys.exit(1)
        
    print(f"{GREEN}[pyberry] Starting in PRODUCTION mode (The Rocket)...{RESET}")
    
    if not os.path.exists(".berry_build/build.lock"):
        print(f"{RED}[PyBerry] FATAL: Cannot start in production mode. TSan audit has not been passed. (Missing .berry_build/build.lock){RESET}")
        sys.exit(1)
        
    print(f"{GREEN}[pyberry] Recompiling with maximum optimizations (-O3, No TSan)...{RESET}")
    env = os.environ.copy()
    env["PYBERRY_TSAN"] = "0"
    subprocess.run([sys.executable, "setup.py", "build_ext", "--inplace", "--force"], cwd=".berry_build", env=env, check=True)

    print(f"{GREEN}  - Server:      Granian{RESET}")
    print(f"{GREEN}  - Workers:     {args.workers}{RESET}")
    print(f"{GREEN}  - Event Loop:  uvloop{RESET}")
    print(f"{GREEN}  - Interface:   RSGI{RESET}")
    
    env["PYTHONPATH"] = "src:.:.berry_build"
    
    try:
        with open(".berry_build/entrypoint.txt", "r") as f:
            entry_module = f.read().strip()
    except FileNotFoundError:
        print(f"{RED}[ERROR] Could not find .berry_build/entrypoint.txt.{RESET}")
        sys.exit(1)
    
    wrapper_code = f"""
import sys
import {entry_module}
from pyberry.core.rsgi import app
"""
    with open(".berry_build/run_wrapper.py", "w") as f:
        f.write(wrapper_code)
        
    subprocess.run(["granian", "--interface", "rsgi", "--workers", str(args.workers), "--loop", "uvloop", "run_wrapper:app"], env=env, check=True)


def check(args):
    import platform
    import shutil
    
    print(f"{GREEN}[pyberry] Checking system requirements...{RESET}")
    all_good = True
    
    # 1. Python version
    py_version = sys.version_info
    print(f"Python Version: {py_version.major}.{py_version.minor}.{py_version.micro}", end="")
    if py_version.major == 3 and py_version.minor >= 13:
        print(f" {GREEN}[OK]{RESET}")
    else:
        print(f" {RED}[WARNING] Python 3.13+ recommended{RESET}")
        all_good = False
        
    # 2. Granian
    print("Granian installed:", end="")
    if shutil.which("granian"):
        print(f" {GREEN}[OK]{RESET}")
    else:
        print(f" {RED}[MISSING] Please run: pip install granian{RESET}")
        all_good = False
        
    # 3. Cython
    print("Cython installed:", end="")
    try:
        import cython
        print(f" {GREEN}[OK]{RESET}")
    except ImportError:
        print(f" {RED}[MISSING] Please run: pip install cython{RESET}")
        all_good = False
        
    # 4. C Compiler
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

def migrate(args):
    print(f"{GREEN}[pyberry] Running database migration...{RESET}")
    from pyberry.config import config
    from pyberry.db import db
    import asyncio
    
    schema_path = os.path.join(os.getcwd(), args.file)
    if not os.path.exists(schema_path):
        print(f"{RED}[ERROR] Schema file '{args.file}' not found.{RESET}")
        return
        
    with open(schema_path, "r") as f:
        sql = f.read()
        
    if getattr(config, 'libsql_url', None) is None:
        print(f"{RED}[ERROR] LIBSQL_URL not found in configuration.{RESET}")
        return
        
    print(f"Connecting to database at {config.libsql_url}...")
    db.init_db(config.libsql_url, getattr(config, 'libsql_auth_token', None))
    
    async def run_migration():
        try:
            await db.execute(sql)
            print(f"{GREEN}[pyberry] Migration successful!{RESET}")
        except Exception as e:
            print(f"{RED}[ERROR] Migration failed: {e}{RESET}")
        finally:
            await db.close_db()
            
    asyncio.run(run_migration())

def main():
    parser = argparse.ArgumentParser(description="PyBerry CLI")
    subparsers = parser.add_subparsers(dest="command")
    
    create_parser = subparsers.add_parser("create")
    create_subparsers = create_parser.add_subparsers(dest="create_command")
    create_app_parser = create_subparsers.add_parser("app")
    create_app_parser.add_argument("app", help="Path to create the app in (e.g., . for current directory, or myapp)")
    
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("app", help="Path to your app file (e.g., main.py)")
    run_parser.add_argument("--dev", action="store_true", help="Run in Playground mode (hot-reloading, no TSan)")
    
    build_parser = subparsers.add_parser("build")
    build_parser.add_argument("app", help="Path to your app file (e.g., main.py)")
    build_parser.add_argument("--audit", action="store_true", help="Mandatory TSan audit mode")
    
    start_parser = subparsers.add_parser("start")
    start_parser.add_argument("--prod", action="store_true", help="Run in Rocket mode (requires build.lock)")
    start_parser.add_argument("--workers", type=int, default=1, help="Number of worker processes")
    
    migrate_parser = subparsers.add_parser("migrate")
    migrate_parser.add_argument("--file", default="db/initial_schema.sql", help="Path to the SQL schema file")
    
    check_parser = subparsers.add_parser("check")
    check_parser.description = "Check system requirements for PyBerry"
    
    args = parser.parse_args()
    
    if args.command == "create":
        if getattr(args, "create_command", None) == "app":
            create_app(args)
        else:
            print("Usage: pyberry create app <app_name>")
    elif args.command == "build":
        build(args)
    elif args.command == "run":
        run(args)
    elif args.command == "start":
        start(args)
    elif args.command == "migrate":
        migrate(args)
    elif args.command == "check":
        check(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
