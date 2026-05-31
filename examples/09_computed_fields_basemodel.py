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
