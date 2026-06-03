# ThreadSanitizer (TSan) Integration in PyBerry

PyBerry utilizes ThreadSanitizer (TSan) to guarantee memory safety and prevent data races in its high-performance, asynchronous Cython/C core. 

Because PyBerry relies on `nogil` blocks to achieve its lock-free ring buffers and background processing speeds, preventing two threads from colliding on the same memory address is critical. TSan acts as our automated, microscopic shield to ensure developers can write high-performance APIs without fearing a 3 AM segfault.

This document details the exact architecture of our TSan integration.

---

## Phase 1: The Zero-Friction Build Toggle (`setup.py`)

TSan is deeply integrated into the C compiler (GCC/Clang). Because TSan instruments memory checks around every single assembly instruction, it causes significant performance degradation. Therefore, it is used **exclusively for testing and debugging**, and never in production.

To achieve a "zero developer friction" workflow, we implemented an environment toggle in `setup.py` (both for the PyBerry framework itself, and dynamically for end-user applications).

### How the Build Toggle Works
By default, compiling PyBerry utilizes hyper-optimized compiler flags (`-O3`, `-march=native`, `-ffast-math`) for maximum execution speed.

If a developer explicitly sets the environment variable `PYBERRY_TSAN=1` during compilation, the build process intercepts the compiler flags:
1. **Drops Optimizations**: Optimization drops to `-O1` to prevent the compiler from rearranging instructions or hiding the data race.
2. **Injects Instrumentation**: Adds `-fsanitize=thread` to both the compiler and linker.
3. **Adds Debug Symbols**: Adds `-g` to map machine-code memory errors back to exact line numbers in our `.pyx` and `.c` files.
4. **Applies to All Native Code**: These flags are dynamically applied to every single Cython extension within the framework.
5. **Adjusts Directives**: Automatically disables Cython's free threading directives while managing `boundscheck` and `wraparound` for strict safety tracking.

### The Scope of TSan's Audit
PyBerry's hybrid architecture means TSan interacts differently with different file types:

- **Cython/C Files (.pyx, .c) — 100% Monitored**: Any code compiled through `setup.py` with `-fsanitize=thread` is fully tracked at the machine-code level. When execution enters a `nogil` block (like in `future.pyx`), TSan actively monitors the atomic states and raw pointers.
- **Pure Python Files (.py) — Monitored via the Interpreter Loop**: Pure Python files are executed by the standard CPython interpreter. Because CPython itself isn't compiled with TSan flags, TSan cannot look inside pure Python objects to track mutations. However, these pure Python scopes are naturally protected from low-level data races by the **Global Interpreter Lock (GIL)**. The moment Python bytecode calls into one of our Cython APIs, TSan immediately resumes control at that boundary.

---

## Phase 2: The Noise Filter (`tsan_suppressions.txt`)

TSan is notoriously aggressive. Because it monitors raw memory and does not natively understand Python's GIL architecture, it will often flag standard, safe internal CPython API operations as "data races."

To ensure developers are not overwhelmed by false positives and only receive alerts for true bugs in our `nogil` queues, we implemented a noise filter.

### How the Suppressions File Works
Located at the root of the project, `tsan_suppressions.txt` defines explicit rules that tell TSan to ignore specific C/C++ namespaces at runtime. 

Our current suppression architecture explicitly ignores:
1. **CPython Internals**: We filter out `race:^Py*` and `race:^_Py*`. Because the GIL prevents simultaneous execution of Python bytecode, memory mutations internal to the CPython interpreter are guaranteed to be safe from data races.
2. **Granian Rust Core**: We filter out `race:^granian::*`. We assume Granian's internal Rust memory management is memory-safe by design.

By loading this suppressions file, TSan is perfectly tuned to only scream when a genuine threading bug occurs within PyBerry's custom Cython/C structures.

---

## Phase 3: The Framework Developer CLI Wrapper (`Makefile`)

For engineers contributing directly to the PyBerry framework, running TSan manually risks polluting the root workspace with TSan-instrumented shared objects (`.so`), which could accidentally leak into production builds.

To prevent this, the `Makefile` isolates the TSan lifecycle:
- **Isolated `.tsan_env` Sandbox**: The `make test-tsan` command clones the entire source tree into a hidden `.tsan_env` directory, compiles it with `PYBERRY_TSAN=1`, executes the test suite, and then instantly deletes the directory. 
- **Protected `clean` Target**: Ensures core C dependencies (like `vendor/yyjson.c`) are not accidentally deleted during cleanup.

---

## Phase 4: Application Lifecycle Enforcement (The 3 Modes)

To guarantee that end-users building applications with PyBerry never deploy memory-unsafe code, the ThreadSanitizer lifecycle is baked directly into the PyBerry Command-Line Interface (`pyberry`). 

This creates a dynamic, 3-tier lifecycle that gives developers the freedom of Python during prototyping, while ruthlessly enforcing the memory safety of Rust before deployment.

### 1. The Playground (`pyberry run <app> --dev`)
This is the default mode for daily engineering. It launches Granian with hot-reloading and skips ThreadSanitizer compilation entirely. Developers enjoy rapid, lock-free iteration while the Python GIL handles basic safety.

### 2. The Crucible (`pyberry build <app> --audit`)
A mandatory step before production deployment. The CLI automatically transpiles the user's application to Cython and recompiles it with ThreadSanitizer injected (`PYBERRY_TSAN=1`). It then runs the user's `tests/` directory through the TSan interpreter.
- **The Lock**: If the audit passes with zero data races, the CLI generates a cryptographic-style `.berry_build/build.lock` file. If a single race is found, the build immediately aborts.

### 3. The Rocket (`pyberry start --prod`)
The production deployment command. The CLI scans for the presence of the `build.lock` file. 
- **Enforcement**: If the lockfile is missing, the deployment throws a fatal error and refuses to boot (`FATAL: Cannot start in production mode. TSan audit has not been passed.`).
- **Execution**: If the lockfile is present, it silently recompiles the application with maximum optimizations (`-O3 -march=native`), stripping all TSan overhead, and launches Granian for peak performance.

---

## Phase 5: The CI/CD Shield (GitHub Actions)

To guarantee that no developer accidentally merges a data race into the `main` branch, PyBerry employs an automated "Crucible" pipeline in GitHub Actions (`.github/workflows/tsan_audit.yml`). This acts as our final defense layer.

### The Pipeline Architecture
The workflow triggers on pull requests to the `main` branch and executes the following steps:
1. **Environment Setup**: Provisions an Ubuntu runner, Python 3.12, and installs the necessary Clang/GCC compilers.
2. **Strict Compilation**: Compiles all core Cython extensions with `PYBERRY_TSAN="1"` to inject ThreadSanitizer flags.
3. **Audit Execution**: Runs the `pytest` suite. If ThreadSanitizer detects any data races during execution, it immediately crashes the job, marking the pull request as failed and preventing the merge.

### The Controlled Escape Hatch
We recognize that sometimes a known race condition might be intentional (or a false positive that needs temporary bypassing). The pipeline includes an "escape hatch" mechanism:
- If a developer adds the `bypass-tsan` label to the pull request, the pipeline detects this event.
- The pipeline gracefully skips the strict TSan audit and marks the CI check as successful.
- This ensures that any bypass is a conscious, visible, and deliberate action taken by the developer, rather than an accidental merge of memory-unsafe code.
