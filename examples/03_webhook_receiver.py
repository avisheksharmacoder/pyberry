from pyberry.app import post
from pyberry.core.request import Request
from pyberry.core.responses import JSONResponse, PlainTextResponse
import hmac
import hashlib

WEBHOOK_SECRET = b"my_super_secret_key"

@post("/webhooks/github")
async def github_webhook(req: Request):
    """Receives and verifies a GitHub webhook."""
    
    # 1. Get the signature from the headers
    signature_header = req.headers.get("x-hub-signature-256")
    if not signature_header:
        return PlainTextResponse("Missing signature", status=401)
        
    # 2. Read the raw request body as bytes for signature verification
    raw_body = await req.body()
    
    # 3. Verify the HMAC signature
    expected_mac = hmac.new(WEBHOOK_SECRET, raw_body, hashlib.sha256).hexdigest()
    expected_signature = f"sha256={expected_mac}"
    
    if not hmac.compare_digest(expected_signature, signature_header):
        return PlainTextResponse("Invalid signature", status=403)
        
    # 4. Parse the body as JSON now that we know it's safe
    # We can use json.loads since we already have the raw_body bytes,
    # or just call await req.json() (PyBerry caches the body internally).
    data = await req.json()
    
    event_type = req.headers.get("x-github-event", "unknown")
    
    if event_type == "push":
        commits = len(data.get("commits", []))
        print(f"Received push event with {commits} commits!")
        
    return JSONResponse({"status": "Webhook processed successfully"})
