# Modular Project Design

One of the unique features of PyBerry is how it handles multi-file projects while maintaining maximum Cython compilation performance.

## The Problem
Normally, if you write a single Cython/Python script and compile it, any files it imports are loaded via the standard Python interpreter. This means if you put your models and business logic in a separate file, they lose all the speed benefits of Cython compilation and `@cython.cclass`.

## The PyBerry Solution
When you run `pyberry build user_app.py`, the CLI automatically scans your entire working directory (excluding virtual environments, caches, etc.) and performs full-project transpilation.

**What happens during `build`:**
1. Every local `.py` file is parsed by the AST Transpiler.
2. `@cython.cclass` and other optimizations are injected into all dataclasses across all files.
3. The entire file tree is mirrored into `.berry_build/`.
4. A multi-extension `setup.py` is generated that Cythonizes the entire project simultaneously.

## Example Project Structure
```text
my_project/
├── models.py
└── user_app.py
```

### `models.py`
```python
from dataclasses import dataclass

@dataclass
class User:
    id: int
    name: str
    
    def is_valid(self) -> bool:
        return self.id > 0
```

### `user_app.py`
```python
from pyberry.core.rsgi import router
from pyberry.core.responses import JSONResponse
from models import User # Seamlessly imported!

@router.add_python_route("GET", "/user/{user_id}")
def get_user(req, user_id: int):
    # This instantiation runs in C
    user = User(id=user_id, name="Test User")
    
    return JSONResponse({
        "id": user.id,
        "name": user.name,
        "is_valid": user.is_valid()
    })
```

Because `.berry_build` is added to the `PYTHONPATH` during `pyberry run`, the import `from models import User` natively resolves to the compiled `.so` (or `.pyd`) binary extension, giving your modular code the exact same speed as if it were all written in a single file!
