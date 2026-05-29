# Command Line Interface (CLI)

The `pyberry` CLI is the control center for transpiling, building, and running your web applications.

## `pyberry build <app_file.py>`
Prepares your application for production by compiling it.

**Under the hood:**
1. Triggers `pyberry.compiler.transpile` to parse the Python AST of your app.
2. Injects Cython optimizations (like `FastFuture` wrappers and `@cython.cclass`).
3. Outputs a `.berry_build/app_compiled.py` file.
4. Generates a `setup.py` file and invokes `gcc` to Cythonize the code into a native shared object (`.so`).

**Usage:**
```bash
pyberry build user_app.py
```

## `pyberry run`
Starts the production server using Granian.

**Under the hood:**
1. Automatically sets `PYTHON_GIL=0` in the environment to enable Free-Threaded processing.
2. Sets the `PYTHONPATH` to include the `.berry_build` directory.
3. Creates a `run_wrapper.py` that imports your compiled application.
4. Spawns `granian` using the `rsgi` interface.

**Options:**
- `--workers <N>`: Sets the number of worker processes. Default is `1`. Due to the GIL-less architecture, a single worker is often capable of saturating local hardware limits.

**Usage:**
```bash
pyberry run --workers 1
```

## `pyberry dev <app_file.py>`
Starts the server in development mode.

**Under the hood:**
1. Skips the AOT compilation step for faster startup.
2. Runs the code using the standard Python interpreter instead of the compiled `.so` extension.
3. Attempts to enable hot-reloading (Note: Granian currently disables hot-reloading when free-threaded Python is active).

**Usage:**
```bash
pyberry dev user_app.py
```

## `pyberry migrate`
Runs the `db/initial_schema.sql` file to setup or update your local or edge database.

**Under the hood:**
1. Connects to the database specified by `LIBSQL_URL` (defaults to `file:db/local.db`) in `security.py`.
2. Reads the schema file and executes the raw SQL using the asynchronous `db.execute()` method.

**Options:**
- `--file <path>`: Specifies a custom path to a SQL schema file. Defaults to `db/initial_schema.sql`.

**Usage:**
```bash
pyberry migrate
pyberry migrate --file custom_schema.sql
```

## `pyberry check`
Performs a comprehensive system check to ensure all dependencies for PyBerry's maximum performance are met across Linux, macOS, and Windows.

**What it checks:**
1. **Python version:** Checks if you're on Python 3.13+ for free-threading support.
2. **Free-threading / GIL status:** Verifies that your Python executable is actually running with the GIL disabled.
3. **Granian:** Ensures the Granian RSGI web server is installed.
4. **Cython:** Confirms Cython is available in your environment for AOT transpilation.
5. **C Compiler:** Checks for `gcc`/`clang` on Linux/macOS, or `cl.exe` (MSVC) on Windows to ensure C extensions can be successfully compiled.

**Usage:**
```bash
pyberry check
```
