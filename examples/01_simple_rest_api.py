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
