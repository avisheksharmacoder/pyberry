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
