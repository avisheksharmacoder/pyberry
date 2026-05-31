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
