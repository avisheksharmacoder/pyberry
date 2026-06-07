# PyBerry Usage Guide

Welcome to the comprehensive usage guide for **PyBerry**, the ultra-fast Python web framework. This guide will teach you how to build applications from scratch using every feature available in the framework.

---

## 1. Getting Started

To create a new PyBerry application from scratch, use the built-in CLI command:

```bash
pyberry create app my_app
cd my_app
```

This will generate a `main.py` entrypoint. Let's look at how to build upon this.

---

## 2. Routing (`@get`, `@post`, `@put`, `@patch`, `@delete`, `@options`, `@head`)

PyBerry routes requests using simple decorators imported from `pyberry.app`. The framework supports a full suite of standard RESTful HTTP methods.

### Basic Routing (`GET` and `POST`)

```python
from pyberry.app import get, post
from pyberry.core.request import Request
from pyberry.core.responses import PlainTextResponse

@get("/")
def home(req: Request):
    return PlainTextResponse("Welcome to the homepage!")

@post("/submit")
def submit_data(req: Request):
    return PlainTextResponse("Data submitted successfully!")
```

### Advanced Routing (`PUT`, `PATCH`, `DELETE`)

PyBerry supports full resource modifications using `PUT`, partial updates with `PATCH`, and removals using `DELETE`. You can also easily parse dynamic path parameters by wrapping them in curly braces `{}`.

```python
from pyberry.app import put, patch, delete
from pyberry.core.request import Request
from pyberry.core.responses import JSONResponse

# PUT is typically used for fully replacing a resource
@put("/users/{user_id}")
async def update_user_fully(req: Request, user_id: int):
    data = await req.json()
    return JSONResponse({"status": "updated", "id": user_id, "data": data})

# PATCH is typically used for partial updates
@patch("/users/{user_id}")
async def update_user_partially(req: Request, user_id: int):
    partial_data = await req.json()
    return JSONResponse({"status": "patched", "id": user_id, "changes": partial_data})

# DELETE is used for resource removal
@delete("/users/{user_id}")
def remove_user(req: Request, user_id: int):
    return JSONResponse({"status": "deleted", "id": user_id})
```

### Utility Routing (`OPTIONS`, `HEAD`)

For advanced API capabilities and CORS preflighting, you can explicitly handle `OPTIONS` and `HEAD` requests.

```python
from pyberry.app import options, head
from pyberry.core.request import Request
from pyberry.core.responses import PlainTextResponse

# OPTIONS is often used by browsers for CORS preflight checks
@options("/api/resource")
def resource_options(req: Request):
    headers = [
        ("Allow", "GET, POST, OPTIONS"),
        ("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    ]
    return PlainTextResponse("", headers=headers)

# HEAD is identical to GET, but without returning the response body
@head("/api/resource")
def resource_head(req: Request):
    headers = [("Content-Length", "1024"), ("X-Resource-Version", "v1.2")]
    return PlainTextResponse("", headers=headers)
```

---

## 3. The `Request` Object

Every route handler receives a `Request` object as its first argument. The `Request` object provides access to the incoming HTTP request data.

Available properties on the `Request` object:
- `req.method` (str): The HTTP method used (e.g., `"GET"`, `"POST"`).
- `req.path` (str): The path of the request (e.g., `"/submit"`).
- `req.query_string` (str): The raw query string from the URL.
- `req.headers` (dict): A dictionary containing all HTTP request headers.

Available **asynchronous** methods:
- `await req.body()`: Lazily reads and returns the raw HTTP request body as bytes.
- `await req.json()`: Lazily reads the body and parses it as a JSON dictionary.

**Example usage:**
```python
from pyberry.app import post
from pyberry.core.request import Request
from pyberry.core.responses import JSONResponse

@post("/info")
async def request_info(req: Request):
    # Lazily await the body
    data = await req.json()
    
    return JSONResponse({
        "method": req.method,
        "path": req.path,
        "body_data": data
    })
```

> **Note on Data Validation**: PyBerry natively supports Cython-optimized validation using `@dataclass` and `BaseModel`. Instead of calling `await req.json()` manually, you can have PyBerry automatically validate and inject models directly into your route functions! [Read the Validation Guide here](./validation.md).

---

## 4. Responses

PyBerry provides several built-in response classes in `pyberry.core.responses` to easily return different types of content. Every response allows you to set the HTTP status code and custom headers.

To make setting status codes easier, PyBerry provides a `status` module containing all standard HTTP status constants.

### `PlainTextResponse`
Used for returning simple, unformatted text.

```python
from pyberry.core.responses import PlainTextResponse
from pyberry import status

@get("/hello")
def hello_text(req: Request):
    return PlainTextResponse("Hello, World!", status=status.HTTP_200_OK)
```

### `JSONResponse`
Automatically serializes Python dictionaries or lists into JSON and sets the appropriate `application/json` content type.

```python
from pyberry.core.responses import JSONResponse

@get("/api/data")
def api_data(req: Request):
    data = {"users": ["Alice", "Bob"], "active": True}
    return JSONResponse(data, status=200)
```

### `HTMLResponse`
Used for returning raw HTML strings. It automatically sets the `text/html` content type.

```python
from pyberry.core.responses import HTMLResponse

@get("/web")
def web_page(req: Request):
    html_content = "<h1>Welcome to PyBerry</h1><p>The fastest framework.</p>"
    return HTMLResponse(html_content, status=200)
```

### `SSEResponse`
Used for streaming Server-Sent Events natively via asynchronous generators. It automatically serializes yielded dictionaries and formats multi-line strings, managing the connection correctly across the Granian boundary.

```python
import asyncio
from pyberry.core.responses import SSEResponse

async def stream_tokens():
    tokens = ["Hello", " ", "World", "!"]
    for token in tokens:
        yield {"token": token}
        await asyncio.sleep(0.5)

@get("/stream")
def ai_stream(req: Request):
    return SSEResponse(stream_tokens())
```

### Custom Headers
You can pass custom headers to any of the response classes using a list of tuples:

```python
@get("/custom")
def custom_headers(req: Request):
    headers = [("x-custom-header", "pyberry-is-fast")]
    return PlainTextResponse("Look at the headers!", headers=headers)
```

---

## 5. Error Handling (`HTTPException` and Specific Exceptions)

To easily return HTTP errors (like 404 Not Found or 500 Internal Server Error), you can raise an `HTTPException` or any of its specific subclasses (e.g., `NotFoundException`, `BadRequestException`, etc.).

```python
from pyberry.app import get
from pyberry.core.request import Request
from pyberry.core.responses import JSONResponse
from pyberry import BadRequestException

@get("/items")
def get_item(req: Request):
    item_id = req.query_string
    if not item_id:
        # This will automatically return a 400 Bad Request
        raise BadRequestException("Missing item_id in query string")
        
    return JSONResponse({"item": item_id})
```

---

## 6. The `app` Entrypoint

Under the hood, your application handlers are registered to the PyBerry routing engine, which uses Granian as its ASGI/RSGI server.

To connect your routes to the server, you must import `app` from `pyberry.core.rsgi` in your main file. This `app` object is what the Granian server interacts with.

```python
# main.py
from pyberry.core.rsgi import app  # <--- CRITICAL for the server to run
from pyberry.app import get
from pyberry.core.responses import PlainTextResponse
from pyberry.core.request import Request

@get("/")
def index(req: Request):
    return PlainTextResponse("Server is running!")
```

To start the development server, run:
```bash
pyberry dev main.py
```

---

## 7. World-Class Security Defaults

PyBerry aims to be the most secure Python framework by default. When you run `pyberry create app`, it automatically generates a `security.py` file alongside your `main.py`. This file contains the framework's core security constants.

### 7.1 Security Headers Injection
By default (`SECURITY_HEADERS_ENABLED = True`), PyBerry injects the following security headers into **every** outgoing response directly from the C-level event loop with zero latency:
- **HSTS (Strict-Transport-Security)**: Enforces HTTPS.
- **Content-Security-Policy (CSP)**: Mitigates XSS attacks (`default-src 'self'`).
- **X-Frame-Options**: Prevents clickjacking (`DENY`).
- **X-Content-Type-Options**: Prevents MIME-sniffing (`nosniff`).
- **Referrer-Policy**: Controls referring URL leaks.
- **Permissions-Policy**: Locks down powerful browser APIs (camera, geolocation, etc.).

### 7.2 Path Traversal Protection
Enabled by default (`PATH_TRAVERSAL_PROTECTION = True`).
The framework natively intercepts any requests attempting to use directory traversal sequences (`../`, `%2e%2e`) in the path and instantly drops them with a `400 Bad Request` before they even reach the router.

### 7.3 Payload Size Limiting
Enabled by default (`MAX_BODY_SIZE = 1048576`).
To prevent memory exhaustion and Denial of Service (DoS) attacks, PyBerry will instantly reject any incoming HTTP request whose body size exceeds the configured max limit (default 1MB) with a `413 Payload Too Large` error.

### 7.4 In-Memory Rate Limiting
PyBerry ships with a blazingly fast, Cython-powered in-memory rate limiter. 
> [!WARNING]
> By default, `RATE_LIMIT_ENABLED` is set to `False` in your `security.py` so it does not interfere with development or local benchmarking (e.g. hitting 100,000+ RPS). You should turn this on in **Production**.

When enabled, you can configure:
- `RATE_LIMIT_REQUESTS = 100`
- `RATE_LIMIT_WINDOW = 60` (in seconds)

If an IP exceeds this threshold, the framework intercepts the request and safely returns a `429 Too Many Requests`.

---

## 8. Database (LibSQL)

PyBerry ships with native, high-performance integration for **LibSQL** (the database behind Turso). It provides an asynchronous, raw SQL execution wrapper optimized for speed.

### Configuration
In your generated `security.py`, you will find:
```python
LIBSQL_URL = "file:db/local.db"
LIBSQL_AUTH_TOKEN = None
```
For local development, it defaults to a local SQLite file inside the `db` directory. For production, simply change `LIBSQL_URL` to your Turso edge URL and provide your `LIBSQL_AUTH_TOKEN`.

### Migrations
You can easily scaffold a database using the built-in CLI command. PyBerry generates a `db/initial_schema.sql` file when you create an app.
To run the migration:
```bash
pyberry migrate
```
*You can also specify a custom file: `pyberry migrate --file db/custom_schema.sql`*

### Usage
The `db` object is a global connection pool that is automatically initialized when the Granian server starts.

```python
from pyberry.app import get, post
from pyberry.core.request import Request
from pyberry.core.responses import JSONResponse
from pyberry.db import db

@get("/users")
async def get_users(req: Request):
    # Retrieve all users
    users = await db.query("SELECT * FROM users")
    return JSONResponse({"users": users})

@post("/users")
async def add_user(req: Request):
    # Example raw execution with parameterized queries
    await db.execute(
        "INSERT INTO users (name, email) VALUES (?, ?)", 
        ["Bob", "bob@example.com"]
    )
    return JSONResponse({"status": "success"})
```
