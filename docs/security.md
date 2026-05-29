# PyBerry Security

Security in PyBerry is designed to be **secure by default**. We prioritize zero-configuration, robust protection for all applications out of the box, mitigating common web vulnerabilities such as Host Header Injection (BadHost) and Cross-Site Request Forgery (CSRF) via strict CORS policies.

## The `security.py` File

When you scaffold a new project using `pyberry init`, a `security.py` file is automatically generated in your project's root directory. PyBerry detects this file and automatically applies its configurations to your application at runtime. 

There is **no need** to manually import or configure these settings inside your `user_app.py`.

### Default Configuration

```python
# security.py
# High-grade security configurations for PyBerry

# Allowed Hosts prevents Host Header Injection attacks (BadHost vulnerabilities).
# Only requests with a matching Host header will be processed.
# In production, replace "localhost" and "127.0.0.1" with your actual domain names.
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# Strict CORS policy
CORS_ENABLED = True
```

## Security Mechanisms

### 1. Host Header Validation (BadHost Mitigation)

Many modern web vulnerabilities, such as cache poisoning and password reset poisoning, originate from **Host Header Injection**. Frameworks that blindly trust the incoming `Host` header can be easily exploited (e.g., historical vulnerabilities in Starlette/FastAPI).

PyBerry actively validates the `Host` header against the `ALLOWED_HOSTS` list defined in your `security.py`. 
- If a request is received with an untrusted `Host` header, PyBerry immediately intercepts the request and returns an HTTP `400 Bad Request` response, preventing any malicious payload from reaching your application logic.
- To allow all hosts (e.g., during testing or behind a trusted reverse proxy that rewrites the host), you can set `ALLOWED_HOSTS = ["*"]`.

### 2. CORS (Cross-Origin Resource Sharing)

By default, PyBerry enforces a strict CORS policy when `CORS_ENABLED = True` is set in your `security.py`. 
- The framework performs an extremely strict block on cross-origin requests by ensuring that the request's `Origin` header matches the `Host` header. 
- If they do not match, the request is intercepted and an HTTP `403 Forbidden` response is returned.

## Going to Production

When deploying your PyBerry application to a production environment, ensure you update your `security.py` with your actual domain name(s):

```python
# security.py
ALLOWED_HOSTS = ["api.mycoolapp.com", "mycoolapp.com"]
```

Because PyBerry handles these validations at the C-extension level before the request even reaches the Python runtime, malicious requests incur virtually zero performance overhead on your server.
