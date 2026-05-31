from pyberry.app import get
from pyberry.core.request import Request
from pyberry.core.responses import HTMLResponse

@get("/dashboard")
def user_dashboard(req: Request):
    """Returns an HTML dashboard with custom caching headers."""
    
    # Check if user is authenticated via cookie
    auth_cookie = req.headers.get("cookie", "")
    if "session_token" not in auth_cookie:
        # Redirect to login (Setting a 302 status and Location header)
        return HTMLResponse(
            "Redirecting to login...", 
            status=302, 
            headers=[("Location", "/login")]
        )
        
    # Build HTML response
    html = """
    <html>
        <head><title>Dashboard</title></head>
        <body>
            <h1>Welcome to your Dashboard</h1>
            <p>Your secure data is loaded.</p>
        </body>
    </html>
    """
    
    # Set headers (e.g., preventing caching for sensitive pages)
    custom_headers = [
        ("Cache-Control", "no-store, no-cache, must-revalidate, private"),
        ("Pragma", "no-cache")
    ]
    
    return HTMLResponse(html, headers=custom_headers)
