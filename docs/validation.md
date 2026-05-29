# Validation & Data Models

PyBerry ships with an ultra-fast, pure Cython C-level validation engine. It natively supports both standard Python `@dataclass`es and its own `BaseModel` to securely and optimally parse and validate incoming JSON request bodies.

Unlike traditional frameworks, PyBerry's validation is **Zero-Penalty**. The routing engine evaluates if an endpoint requires a validated model, and *lazily* awaits the HTTP request body only when absolutely necessary, completely preserving microsecond speeds for standard `GET` requests.

---

## 1. Using `@dataclass`

You can use standard Python dataclasses for data modeling. During route registration, PyBerry inspects the signature, detects the dataclass, and pre-compiles a Cython schema for maximum runtime speed.

```python
from dataclasses import dataclass
from pyberry.app import post
from pyberry.core.request import Request
from pyberry.core.responses import JSONResponse

@dataclass
class UserCreate:
    username: str
    age: int
    is_active: bool = True

@post("/users")
def create_user(req: Request, user: UserCreate):
    # 'user' is fully validated and typed as a UserCreate instance!
    return JSONResponse({
        "status": "success",
        "username": user.username,
        "age": user.age,
        "is_active": user.is_active
    })
```

---

## 2. Using `BaseModel`

If you prefer an approach similar to Pydantic, PyBerry offers a built-in `BaseModel`. 
The `BaseModel` utilizes `__init_subclass__` to compile its Cython validation schema directly at the time the class is defined (startup), ensuring absolutely zero schema-compilation latency during HTTP requests.

```python
from pyberry import BaseModel
from pyberry.app import post
from pyberry.core.request import Request
from pyberry.core.responses import JSONResponse

class ProductCreate(BaseModel):
    name: str
    price: float
    in_stock: bool

@post("/products")
def create_product(req: Request, product: ProductCreate):
    return JSONResponse({
        "status": "success",
        "product_name": product.name,
        "price": product.price
    })
```

---

## 3. How It Works (422 Unprocessable Entity)

When a JSON payload is sent to an endpoint requiring a model (either `@dataclass` or `BaseModel`), PyBerry's C-level engine intercepts it. 
It strictly casts JSON strings to their respective types (e.g., converting `"42"` to an `int`). 

If a required field is missing, or if a type cannot be safely cast, the engine immediately halts execution and returns a `422 Unprocessable Entity` JSON response to the client.

**Example Client Failure:**
If a client sends `{"username": "Alice"}` to the `/users` endpoint (missing the required `age` field), they will receive:
```http
HTTP/1.1 422 Unprocessable Entity
Content-Type: text/plain

Field 'age' is required
```
