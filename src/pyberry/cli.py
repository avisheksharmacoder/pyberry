import argparse
import subprocess
import sys
import os

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

# The Granian entrypoint
# Run with: pyberry dev main.py
"""
    with open(os.path.join(base_dir, "main.py"), "w") as f:
        f.write(main_code)
        
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

# -------------------------------------------------------------------------
# Deep Level Security Options
# -------------------------------------------------------------------------

# Automatically injects HSTS, X-Frame-Options, Content-Security-Policy, etc.
SECURITY_HEADERS_ENABLED = True
HSTS_MAX_AGE = 31536000
X_FRAME_OPTIONS = "DENY"
CONTENT_SECURITY_POLICY = "default-src 'self'"

# Maximum allowed payload size (in bytes) to prevent Memory Exhaustion/DoS.
MAX_BODY_SIZE = 1048576  # 1MB

# Protect against directory traversal attacks in URLs (e.g., %2e%2e%2f)
PATH_TRAVERSAL_PROTECTION = True

# Rate Limiting (In-Memory).
# NOTE: Rate limiting is DISABLED by default so it doesn't affect benchmarking.
# Be sure to enable this in Production to protect your endpoints.
RATE_LIMIT_ENABLED = False
RATE_LIMIT_REQUESTS = 100
RATE_LIMIT_WINDOW = 60

# -------------------------------------------------------------------------
# Database Options (libsql)
# -------------------------------------------------------------------------
# Default to local db for development.
# For production, you can replace this with your Turso DB URL (e.g., libsql://my-db-user.turso.io)
LIBSQL_URL = "file:db/local.db"
# Provide the auth token here if using a remote Turso DB.
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

## CLI Commands

Here are the main commands you can use with your PyBerry project:

- **`pyberry dev main.py`**: Start the development server with hot-reloading (if supported by your Python version).
- **`pyberry build main.py`**: Transpile your application using Cython for production (maximum performance).
- **`pyberry run`**: Run the production build of your application (requires `pyberry build` to be run first).
- **`pyberry migrate`**: Run the `db/initial_schema.sql` file to setup your database.
- **`pyberry check`**: Verify that your system meets all requirements for optimal PyBerry performance (Python 3.13+, Cython, C compiler).
"""
    with open(os.path.join(base_dir, "docs.md"), "w") as f:
        f.write(docs_code)
        
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
    print(f"{GREEN}  - Server:      Granian{RESET}")
    print(f"{GREEN}  - Workers:     {args.workers}{RESET}")
    print(f"{GREEN}  - Event Loop:  uvloop{RESET}")
    print(f"{GREEN}  - Interface:   RSGI{RESET}")
    env = os.environ.copy()
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
        
    subprocess.run(["granian", "--interface", "rsgi", "--workers", str(args.workers), "--loop", "uvloop", "run_wrapper:app"], env=env, check=True)

def dev(args):
    print(f"{RED}[pyberry] Starting in DEV mode (Hot Reloading)...{RESET}")
    print(f"{RED}  - Server:      Granian{RESET}")
    print(f"{RED}  - Workers:     1{RESET}")
    print(f"{RED}  - Event Loop:  uvloop{RESET}")
    print(f"{RED}  - Interface:   RSGI{RESET}")
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
    # Initialize config to load security settings like LIBSQL_URL
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
            # Split and execute each statement for better compatibility with libsql driver 
            # if multiple statements are provided.
            # Using execute() might only run the first statement or block of statements.
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
    
    build_parser = subparsers.add_parser("build")
    build_parser.add_argument("app", help="Path to your app file (e.g., user_app.py)")
    
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--workers", type=int, default=1, help="Number of worker processes")
    
    dev_parser = subparsers.add_parser("dev")
    dev_parser.add_argument("app", help="Path to your app file")
    
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
    elif args.command == "dev":
        dev(args)
    elif args.command == "migrate":
        migrate(args)
    elif args.command == "check":
        check(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
