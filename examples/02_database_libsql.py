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
