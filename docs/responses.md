# Fast HTTP Responses & Exceptions

PyBerry provides native, highly-optimized response classes that seamlessly integrate with Granian's RSGI server interface.

## Standard Responses
All response objects can be imported from `pyberry.core.responses`. They automatically handle serialization and `Content-Type` headers for you.

- `JSONResponse(content: dict, status: int = 200, headers: list = None)`
- `HTMLResponse(content: str, status: int = 200, headers: list = None)`
- `PlainTextResponse(content: str, status: int = 200, headers: list = None)`

### Example Usage:
```python
from pyberry.core.rsgi import router
from pyberry.core.responses import JSONResponse

@router.add_python_route("GET", "/")
def index(req):
    return JSONResponse({"status": "ok", "message": "Welcome to PyBerry!"})
```

## Status Codes
PyBerry provides a `status` module containing readable constants for all standard HTTP status codes.

```python
from pyberry import status
from pyberry.core.responses import JSONResponse

@router.add_python_route("GET", "/created")
def created(req):
    return JSONResponse({"msg": "created"}, status=status.HTTP_201_CREATED)
```

## Error Handling
For fast, short-circuit error handling, PyBerry provides an `HTTPException` base class and specific error exceptions (e.g., `NotFoundException`, `BadRequestException`, etc.).

When you raise an exception inside a route, it is caught directly at the Rust-to-Cython boundary (`rsgi.pyx`). This completely bypasses the normal Python response allocation cycle and instantly passes the error back to Granian in C, ensuring minimal overhead during error states.

### Example Usage:
```python
from pyberry.core.rsgi import router
from pyberry.core.responses import JSONResponse
from pyberry import BadRequestException

@router.add_python_route("GET", "/user/{user_id}")
def get_user(req, user_id: int):
    if user_id <= 0:
        # Instantly breaks execution and returns 400 Bad Request
        raise BadRequestException("Invalid user ID")
    
    return JSONResponse({"id": user_id, "name": "Valid User"})
```
