from pyberry.app import get, post, put, patch, delete
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

@put("/users/{user_id}")
async def update_user(req: Request, user_id: int):
    """
    Fully replace an existing user.
    """
    if user_id not in USERS:
        raise NotFoundException(f"User with ID {user_id} not found")
        
    data = await req.json()
    name = data.get("name")
    email = data.get("email")
    if not name or not email:
        raise BadRequestException("Both 'name' and 'email' are required for PUT")
        
    USERS[user_id]["name"] = name
    USERS[user_id]["email"] = email
    
    return JSONResponse({"message": "User updated", "user": USERS[user_id]})

@patch("/users/{user_id}")
async def patch_user(req: Request, user_id: int):
    """
    Partially update an existing user.
    """
    if user_id not in USERS:
        raise NotFoundException(f"User with ID {user_id} not found")
        
    data = await req.json()
    if "name" in data:
        USERS[user_id]["name"] = data["name"]
    if "email" in data:
        USERS[user_id]["email"] = data["email"]
        
    return JSONResponse({"message": "User patched", "user": USERS[user_id]})

@delete("/users/{user_id}")
def delete_user(req: Request, user_id: int):
    """
    Delete a user by ID.
    """
    if user_id not in USERS:
        raise NotFoundException(f"User with ID {user_id} not found")
        
    del USERS[user_id]
    return JSONResponse({"message": "User deleted", "id": user_id})
