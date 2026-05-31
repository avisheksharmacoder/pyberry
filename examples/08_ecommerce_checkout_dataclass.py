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
