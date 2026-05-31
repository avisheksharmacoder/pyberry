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
