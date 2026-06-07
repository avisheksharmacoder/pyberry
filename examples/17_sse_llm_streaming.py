"""
Example 17: Server-Sent Events (SSE) with LLM Token Streaming
-------------------------------------------------------------
This example demonstrates how to use PyBerry's native SSEResponse to stream 
real-time data to a client. This pattern is commonly used for AI Chatbots 
(like streaming tokens from an LLM) or real-time progress bars.

To run this example:
    pyberry run examples.17_sse_llm_streaming --dev
"""

import asyncio
from pyberry.app import get
from pyberry.core.request import Request
from pyberry.core.responses import SSEResponse, HTMLResponse

# 1. The Generator Function
# SSE requires an asynchronous generator. Here we simulate a slow LLM generating text.
async def generate_ai_response():
    tokens = ["Hello", " there!", " I", " am", " an", " AI", " streaming", " tokens", " natively", " through", " PyBerry!"]
    
    for i, token in enumerate(tokens):
        # We yield a standard Python dictionary.
        # PyBerry's C-engine intercepts this, automatically serializes it to JSON 
        # using the high-speed `fastjson` module, and wraps it in the SSE 'data: ' format.
        yield {
            "id": i,
            "token": token,
            "status": "generating"
        }
        
        # Simulate the delay of token generation
        await asyncio.sleep(0.3)
        
    # The final chunk signals completion
    yield {"status": "done"}

# 2. The Streaming Endpoint
# We bind the GET route using PyBerry's standard decorator.
@get("/stream")
def stream_endpoint(req: Request):
    """
    Returns the SSEResponse. The SSEResponse automatically injects the required headers:
    - content-type: text/event-stream
    - cache-control: no-cache
    - connection: keep-alive
    """
    return SSEResponse(generate_ai_response())


# 3. A Simple Frontend
# We provide a simple HTML page to consume the SSE stream using the browser's EventSource API.
@get("/")
def index(req: Request):
    html = """
    <!DOCTYPE html>
    <html>
    <head><title>PyBerry SSE Chat</title></head>
    <body style="font-family: sans-serif; padding: 2rem;">
        <h2>LLM Streaming Example</h2>
        <button onclick="startStream()">Start Stream</button>
        <p id="chatbox" style="margin-top: 1rem; padding: 1rem; border: 1px solid #ccc; min-height: 50px;"></p>
        
        <script>
            function startStream() {
                const box = document.getElementById('chatbox');
                box.innerHTML = ''; // clear
                
                // EventSource connects to our SSE endpoint
                const source = new EventSource('/stream');
                
                source.onmessage = function(event) {
                    // PyBerry sent us JSON stringified data
                    const data = JSON.parse(event.data);
                    
                    if (data.status === 'done') {
                        source.close(); // Stop listening
                        box.innerHTML += '<br><br><i>Stream complete.</i>';
                        return;
                    }
                    
                    // Append the incoming token to the chat box
                    if (data.token) {
                        box.innerHTML += data.token;
                    }
                };
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(html)
