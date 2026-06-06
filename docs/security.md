# PyBerry Security

Security in PyBerry is designed to be **secure by default**. We prioritize zero-configuration, robust protection for all applications out of the box, mitigating common web vulnerabilities such as Host Header Injection (BadHost) and Cross-Site Request Forgery (CSRF) via strict CORS policies.

## The `security.py` File

When you scaffold a new project using `pyberry init`, a `security.py` file is automatically generated in your project's root directory. PyBerry detects this file and automatically applies its configurations to your application at runtime. 

There is **no need** to manually import or configure these settings inside your `user_app.py`.

### Default Configuration

```python
# security.py
# High-grade security configurations for PyBerry

# Allowed Hosts prevents Host Header Injection attacks.
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# Strict CORS policy
CORS_ENABLED = True

# To allow external frontends to access your API, define them here.
# Supports exact matches and wildcards (e.g., "https://*.mycoolapp.com")
CORS_ALLOWED_ORIGINS = [] 

# Memory exhaustion protection (Default: 1MB)
MAX_BODY_SIZE = 1048576 

# Automatically injects X-Content-Type-Options, X-Frame-Options, etc.
SECURITY_HEADERS_ENABLED = True
```

## Security Mechanisms

### 1. Host Header Validation (BadHost Mitigation)

Many modern web vulnerabilities, such as cache poisoning and password reset poisoning, originate from **Host Header Injection**. Frameworks that blindly trust the incoming `Host` header can be easily exploited (e.g., historical vulnerabilities in Starlette/FastAPI).

PyBerry actively validates the `Host` header against the `ALLOWED_HOSTS` list defined in your `security.py`. 
- If a request is received with an untrusted `Host` header, PyBerry immediately intercepts the request and returns an HTTP `400 Bad Request` response, preventing any malicious payload from reaching your application logic.
- To allow all hosts (e.g., during testing or behind a trusted reverse proxy that rewrites the host), you can set `ALLOWED_HOSTS = ["*"]`.

### 2. CORS (Cross-Origin Resource Sharing)

By default, PyBerry enforces a strict CORS policy when `CORS_ENABLED = True` is set in your `security.py`.
* The framework ensures that the request's `Origin` header securely matches the `Host` header, preventing unauthorized Cross-Site Request Forgery (CSRF).
* If you have a separate frontend application (e.g., a React app at `https://app.example.com`), you can safely whitelist it using the `CORS_ALLOWED_ORIGINS` array. PyBerry natively supports exact matches and wildcard subdomains (e.g., `https://*.example.com`).
* Unauthorized cross-origin requests are intercepted instantly with an HTTP `403 Forbidden` response.

### 3. Null Byte Injection Prevention

When handling user-supplied paths or file interactions, malicious users often append null bytes (`\x00` or `%00`) to manipulate the underlying C-level filesystem APIs into truncating the string early. PyBerry actively blocks null bytes from resolving during path normalization by returning a `400 Bad Request` instantly before the request enters Python execution logic.

### 4. Body Payload Limiting

PyBerry protects against memory exhaustion (RAM DOS) natively via strict payload sizing. By default, any incoming payload exceeding 1MB is rejected immediately with a `413 Payload Too Large`. 
- This virtually zero-latency interception ensures the server never allocates RAM to buffer malicious payloads. 
- You can override this limit by defining `MAX_BODY_SIZE` (in bytes) in your `security.py`.

### 5. Global Security Headers

A secure framework shouldn't require developers to memorize security headers. PyBerry automatically injects an optimized set of default headers onto **every** outgoing HTTP response.
- At an absolute minimum, responses include `X-Content-Type-Options: nosniff` and `X-Frame-Options: deny`.
- You can override these defaults by setting `SECURITY_HEADERS_ENABLED = False` or modifying `X_FRAME_OPTIONS` and `CONTENT_SECURITY_POLICY` inside `security.py`.

## Going to Production

When deploying your PyBerry application to a production environment, ensure you update your `security.py` with your actual domain name(s):

```python
# security.py
ALLOWED_HOSTS = ["api.mycoolapp.com", "mycoolapp.com"]
```

Because PyBerry handles these validations at the C-extension level before the request even reaches the Python runtime, malicious requests incur virtually zero performance overhead on your server.
