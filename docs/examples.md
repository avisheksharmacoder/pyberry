# PyBerry Examples

This document provides real-world examples of how to build backend systems using the PyBerry framework. The examples demonstrate how to combine routing, request parsing, database operations, and response generation into cohesive applications.

---

## 1. Simple REST API (Users)

This example demonstrates a simple REST API for managing users, using path parameters and JSON request bodies.

```python
from pyberry.app import get, post
from pyberry.core.request import Request
from pyberry.core.responses import JSONResponse
from pyberry import BadRequestException, NotFoundException

# In-memory database for demonstration purposes
USERS = {
    1: {"id": 1, "name": "Alice", "email": "alice@example.com"},
    2: {"id": 2, "name": "Bob", "email": "bob@example.com"}
}
NEXT_ID = 3

@get("/users")
def list_users(req: Request):
    """Retrieve all users."""
    # Convert dictionary values to a list
    user_list = list(USERS.values())
    return JSONResponse({"users": user_list, "total": len(user_list)})

@get("/users/{user_id}")
def get_user(req: Request, user_id: int):
    """
    Retrieve a specific user by ID.
    PyBerry automatically parses the {user_id} path parameter and 
    casts it to an integer based on the type hint.
    """
    user = USERS.get(user_id)
    if not user:
        raise NotFoundException(f"User with ID {user_id} not found")
        
    return JSONResponse({"user": user})

@post("/users")
async def create_user(req: Request):
    """
    Create a new user from a JSON payload.
    Since we are reading the body asynchronously, the function must be `async`.
    """
    global NEXT_ID
    
    # Parse the incoming JSON body
    data = await req.json()
    
    # Basic validation
    name = data.get("name")
    email = data.get("email")
    if not name or not email:
        raise BadRequestException("Both 'name' and 'email' are required")
        
    # Create the new user
    new_user = {
        "id": NEXT_ID,
        "name": name,
        "email": email
    }
    USERS[NEXT_ID] = new_user
    NEXT_ID += 1
    
    # Return a 201 Created status code
    return JSONResponse({"message": "User created", "user": new_user}, status=201)
```

---

## 2. Database Integration with LibSQL

This example shows how to use PyBerry's native `db` connection pool to execute SQL queries. It assumes you have run `pyberry migrate` to set up your tables.

```python
from pyberry.app import get, post
from pyberry.core.request import Request
from pyberry.core.responses import JSONResponse
from pyberry.db import db
from pyberry import BadRequestException

@post("/posts")
async def create_post(req: Request):
    """Insert a new blog post into the database."""
    data = await req.json()
    title = data.get("title")
    content = data.get("content")
    
    if not title or not content:
        raise BadRequestException("Missing title or content")
        
    # Parameterized query to prevent SQL Injection
    await db.execute(
        "INSERT INTO posts (title, content) VALUES (?, ?)",
        [title, content]
    )
    
    return JSONResponse({"status": "Post created successfully"}, status=201)

@get("/posts")
async def get_all_posts(req: Request):
    """Fetch all posts from the database."""
    # db.query returns a list of dictionaries automatically
    posts = await db.query("SELECT * FROM posts ORDER BY created_at DESC")
    return JSONResponse({"data": posts})

@get("/posts/{post_id}")
async def get_single_post(req: Request, post_id: int):
    """Fetch a single post using db.query_first()."""
    # query_first returns a single dictionary or None if not found
    post = await db.query_first("SELECT * FROM posts WHERE id = ?", [post_id])
    
    if not post:
        return JSONResponse({"error": "Post not found"}, status=404)
        
    return JSONResponse({"data": post})
```

---

## 3. Webhook Receiver / Event Processing

A common backend task is receiving webhooks from third-party services (like Stripe, GitHub, or Discord). Here is an example of verifying a webhook header and processing the event.

```python
from pyberry.app import post
from pyberry.core.request import Request
from pyberry.core.responses import JSONResponse, PlainTextResponse
import hmac
import hashlib

WEBHOOK_SECRET = b"my_super_secret_key"

@post("/webhooks/github")
async def github_webhook(req: Request):
    """Receives and verifies a GitHub webhook."""
    
    # 1. Get the signature from the headers
    signature_header = req.headers.get("x-hub-signature-256")
    if not signature_header:
        return PlainTextResponse("Missing signature", status=401)
        
    # 2. Read the raw request body as bytes for signature verification
    raw_body = await req.body()
    
    # 3. Verify the HMAC signature
    expected_mac = hmac.new(WEBHOOK_SECRET, raw_body, hashlib.sha256).hexdigest()
    expected_signature = f"sha256={expected_mac}"
    
    if not hmac.compare_digest(expected_signature, signature_header):
        return PlainTextResponse("Invalid signature", status=403)
        
    # 4. Parse the body as JSON now that we know it's safe
    # We can use json.loads since we already have the raw_body bytes,
    # or just call await req.json() (PyBerry caches the body internally).
    data = await req.json()
    
    event_type = req.headers.get("x-github-event", "unknown")
    
    if event_type == "push":
        commits = len(data.get("commits", []))
        print(f"Received push event with {commits} commits!")
        
    return JSONResponse({"status": "Webhook processed successfully"})
```

---

## 4. Serving HTML with Custom Headers

Sometimes you need to serve dynamically generated HTML and set custom cookies or cache headers.

```python
from pyberry.app import get
from pyberry.core.request import Request
from pyberry.core.responses import HTMLResponse

@get("/dashboard")
def user_dashboard(req: Request):
    """Returns an HTML dashboard with custom caching headers."""
    
    # Check if user is authenticated via cookie
    auth_cookie = req.headers.get("cookie", "")
    if "session_token" not in auth_cookie:
        # Redirect to login (Setting a 302 status and Location header)
        return HTMLResponse(
            "Redirecting to login...", 
            status=302, 
            headers=[("Location", "/login")]
        )
        
    # Build HTML response
    html = \"\"\"
    <html>
        <head><title>Dashboard</title></head>
        <body>
            <h1>Welcome to your Dashboard</h1>
            <p>Your secure data is loaded.</p>
        </body>
    </html>
    \"\"\"
    
    # Set headers (e.g., preventing caching for sensitive pages)
    custom_headers = [
        ("Cache-Control", "no-store, no-cache, must-revalidate, private"),
        ("Pragma", "no-cache")
    ]
    
    return HTMLResponse(html, headers=custom_headers)
```

---

## 5. LLM Chat Backend with `@dataclass` Validation

This example demonstrates how to build an API for an LLM chatbot using a standard Python `@dataclass`. PyBerry automatically validates the incoming JSON payload against the dataclass with zero compilation penalty.

```python
from dataclasses import dataclass
from typing import List
from pyberry.app import post
from pyberry.core.request import Request
from pyberry.core.responses import JSONResponse

@dataclass
class ChatRequest:
    prompt: str
    model: str = "gpt-4"
    temperature: float = 0.7

@post("/chat/completions")
def chat_completion(req: Request, payload: ChatRequest):
    """
    Handles chat completion requests.
    PyBerry intercepts the JSON body and casts it directly to a `ChatRequest` object.
    If the payload is invalid, a 422 Unprocessable Entity is returned automatically.
    """
    # 1. Access validated properties safely
    print(f"Using model: {payload.model} at temperature: {payload.temperature}")
    
    # 2. Extract the prompt
    user_prompt = payload.prompt
    
    # 3. Simulate calling an LLM (e.g., OpenAI API)
    mock_reply = f"Mock AI response to: '{user_prompt}'"
    
    # 4. Return standard JSON structure
    return JSONResponse({
        "choices": [
            {"message": {"role": "assistant", "content": mock_reply}}
        ],
        "model": payload.model
    })
```

---

## 6. LLM Embeddings Backend with `BaseModel`

For a Pydantic-like experience, you can use PyBerry's native `BaseModel`. This is highly optimized for compiling validation schemas at startup.

```python
from pyberry import BaseModel
from typing import List
from pyberry.app import post
from pyberry.core.request import Request
from pyberry.core.responses import JSONResponse

class EmbeddingRequest(BaseModel):
    input_text: str
    model: str = "text-embedding-ada-002"

@post("/embeddings")
def generate_embeddings(req: Request, payload: EmbeddingRequest):
    """
    Generates vector embeddings for the provided input text.
    The payload is fully validated as an `EmbeddingRequest` instance by PyBerry.
    """
    # 1. Access the validated input
    text = payload.input_text
    
    # 2. Simulate generating embeddings
    # In reality, you would pass 'text' to your LLM provider or local model
    mock_embeddings = [{
        "object": "embedding",
        "index": 0,
        "embedding": [0.015, -0.022, 0.089] 
    }]
        
    # 3. Return the standard OpenAI-compatible response format
    return JSONResponse({
        "object": "list",
        "data": mock_embeddings,
        "model": payload.model,
        "usage": {"prompt_tokens": 5, "total_tokens": 5}
    })
```

---

## 7. E-commerce: Product Management with `BaseModel`

This example demonstrates a product creation endpoint typical in e-commerce backends. We use `BaseModel` to validate the incoming product details and then insert them into our database using PyBerry's native LibSQL integration.

```python
from pyberry import BaseModel
from pyberry.app import get, post
from pyberry.core.request import Request
from pyberry.core.responses import JSONResponse
from pyberry.db import db
from pyberry import NotFoundException

class ProductCreate(BaseModel):
    name: str
    description: str
    price: float
    stock: int
    category: str

@post("/products")
async def add_product(req: Request, product: ProductCreate):
    """
    Adds a new product to the e-commerce store.
    PyBerry automatically validates price (float) and stock (int).
    """
    
    # 1. Insert into database using parameterized queries
    await db.execute(
        "INSERT INTO products (name, description, price, stock, category) VALUES (?, ?, ?, ?, ?)",
        [product.name, product.description, product.price, product.stock, product.category]
    )
    
    # 2. Return success
    return JSONResponse(
        {"status": "success", "message": f"Product '{product.name}' added to catalog."}, 
        status=201
    )

@get("/products/{product_id}")
async def get_product(req: Request, product_id: int):
    """Retrieves a single product from the database."""
    product = await db.query_first("SELECT * FROM products WHERE id = ?", [product_id])
    
    if not product:
        raise NotFoundException("Product not found")
        
    return JSONResponse({"product": product})
```

---

## 8. E-commerce: Shopping Cart Checkout with `@dataclass`

When processing a checkout, you need to validate complex nested data, like a list of items and payment details. 

```python
from dataclasses import dataclass
from typing import List
from pyberry.app import post
from pyberry.core.request import Request
from pyberry.core.responses import JSONResponse
from pyberry import BadRequestException

@dataclass
class CartItem:
    product_id: int
    quantity: int

@dataclass
class CheckoutRequest:
    user_id: int
    items: List[CartItem]
    payment_token: str

@post("/checkout")
async def process_checkout(req: Request, payload: CheckoutRequest):
    """
    Processes an e-commerce checkout.
    PyBerry validates the list of CartItem dataclasses automatically.
    """
    
    if not payload.items:
        raise BadRequestException("Your cart is empty.")
        
    # 1. Calculate total order value (mock database lookup)
    total_price = 0.0
    for item in payload.items:
        # In a real app, you would query the DB for the product's price here
        mock_price = 19.99 
        total_price += (mock_price * item.quantity)
        
    # 2. Process Payment (Mock)
    payment_successful = True # Mocking a call to Stripe/PayPal
    
    if not payment_successful:
        return JSONResponse({"error": "Payment declined"}, status=402)
        
    # 3. Create Order Record (Mock)
    order_id = "ORD-99321"
    
    # 4. Return Receipt
    return JSONResponse({
        "status": "success",
        "order_id": order_id,
        "amount_paid": round(total_price, 2),
        "message": "Thank you for your purchase!"
    })
```

---

## 9. Computed Fields in `BaseModel`

Unlike FastAPI/Pydantic which relies on custom decorators like `@computed_field`, PyBerry leans on standard Python idioms for maximum speed. You can easily create computed properties on your `BaseModel` using the standard `@property` decorator.

```python
from pyberry import BaseModel
from pyberry.app import post
from pyberry.core.request import Request
from pyberry.core.responses import JSONResponse

class UserRegistration(BaseModel):
    first_name: str
    last_name: str
    
    @property
    def full_name(self) -> str:
        """A standard Python computed property."""
        return f"{self.first_name} {self.last_name}"

@post("/register")
def register_user(req: Request, user: UserRegistration):
    """
    Registers a new user.
    The computed property `full_name` is readily available on the validated object.
    """
    
    # 1. Access the computed field securely
    greeting = f"Welcome to the platform, {user.full_name}!"
    
    # 2. Return a response utilizing the computed data
    return JSONResponse({
        "message": greeting,
        "user_profile": {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "full_name": user.full_name
        }
    })
```

---

## 10. Interoperability & Computed Fields in `@dataclass`

PyBerry fully supports mixing and matching `BaseModel` and `@dataclass`. Additionally, if you are using standard dataclasses, you can compute values instantly after parsing by utilizing the native `__post_init__` hook.

```python
from pyberry import BaseModel
from dataclasses import dataclass, field
from typing import List
from pyberry.app import post
from pyberry.core.request import Request
from pyberry.core.responses import JSONResponse

# 1. A standard dataclass with a computed field
@dataclass
class Item:
    name: str
    price: float
    tax_rate: float
    # We use init=False because the client doesn't provide this; we compute it.
    total_price: float = field(init=False)
    
    def __post_init__(self):
        """Standard Python hook called immediately after PyBerry validates the fields."""
        self.total_price = self.price + (self.price * self.tax_rate)

# 2. A BaseModel that houses a List of standard dataclasses
class OrderReceipt(BaseModel):
    order_id: str
    items: List[Item]
    
    @property
    def grand_total(self) -> float:
        """Computed field aggregating all nested dataclass computed totals."""
        return sum(item.total_price for item in self.items)

@post("/receipts")
def process_receipt(req: Request, receipt: OrderReceipt):
    """
    PyBerry automatically parses the BaseModel, which in turn parses the nested
    list of Item dataclasses, triggering their `__post_init__` hooks instantly!
    """
    
    # Access the computed grand total seamlessly
    final_amount = receipt.grand_total
    
    return JSONResponse({
        "status": "success",
        "order": receipt.order_id,
        "items_processed": len(receipt.items),
        "total_amount_due": round(final_amount, 2)
    })
```
