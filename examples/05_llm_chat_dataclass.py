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
