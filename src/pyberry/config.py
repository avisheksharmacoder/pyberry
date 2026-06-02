import os
import sys

class Config:
    def __init__(self):
        # By default, block all cross origin requests (CORS enabled)
        # To disable, users can set this to False in their app initialization
        self.cors_enabled = True
        
        # By default, allow all hosts, but this is overridden by security.py
        self.allowed_hosts = ["*"]
        
        # Zero-latency background logging
        self.logging_enabled = True
        self.stdout_logging_enabled = True
        
        # LibSQL configuration
        self.libsql_url = "file:db/local.db"
        self.libsql_auth_token = None
        
    def load_security(self):
        try:
            import security
            self.cors_enabled = getattr(security, 'CORS_ENABLED', True)
            self.allowed_hosts = getattr(security, 'ALLOWED_HOSTS', ["*"])
            self.logging_enabled = getattr(security, 'LOGGING_ENABLED', True)
            self.stdout_logging_enabled = getattr(security, 'STDOUT_LOGGING_ENABLED', True)
            
            # New Security Features
            self.security_headers_enabled = getattr(security, 'SECURITY_HEADERS_ENABLED', True)
            self.hsts_max_age = getattr(security, 'HSTS_MAX_AGE', 31536000)
            self.x_frame_options = getattr(security, 'X_FRAME_OPTIONS', 'DENY')
            self.content_security_policy = getattr(security, 'CONTENT_SECURITY_POLICY', "default-src 'self'")
            self.max_body_size = getattr(security, 'MAX_BODY_SIZE', 1048576) # 1MB
            self.path_traversal_protection = getattr(security, 'PATH_TRAVERSAL_PROTECTION', True)
            
            # Rate Limiter
            self.rate_limit_enabled = getattr(security, 'RATE_LIMIT_ENABLED', False)
            self.rate_limit_requests = getattr(security, 'RATE_LIMIT_REQUESTS', 100)
            self.rate_limit_window = getattr(security, 'RATE_LIMIT_WINDOW', 60)
            
            # LibSQL configuration
            self.libsql_url = getattr(security, 'LIBSQL_URL', 'file:db/local.db')
            self.libsql_auth_token = getattr(security, 'LIBSQL_AUTH_TOKEN', None)

            # Pre-compute headers for ultra-fast appending
            self.security_headers = []
            if self.security_headers_enabled:
                self.security_headers = [
                    ('strict-transport-security', f'max-age={self.hsts_max_age}; includeSubDomains'),
                    ('x-frame-options', self.x_frame_options.lower()),
                    ('x-content-type-options', 'nosniff'),
                    ('content-security-policy', self.content_security_policy),
                    ('referrer-policy', 'strict-origin-when-cross-origin'),
                    ('permissions-policy', 'camera=(), microphone=(), geolocation=()')
                ]
        except ImportError:
            # Fallbacks if security.py is completely missing
            self.security_headers_enabled = True
            self.max_body_size = 1048576
            self.path_traversal_protection = True
            self.rate_limit_enabled = False
            self.rate_limit_requests = 100
            self.rate_limit_window = 60
            self.libsql_url = "file:db/local.db"
            self.libsql_auth_token = None
            self.security_headers = [
                ('strict-transport-security', 'max-age=31536000; includeSubDomains'),
                ('x-frame-options', 'deny'),
                ('x-content-type-options', 'nosniff'),
                ('content-security-policy', "default-src 'self'"),
                ('referrer-policy', 'strict-origin-when-cross-origin'),
                ('permissions-policy', 'camera=(), microphone=(), geolocation=()')
            ]
            pass

config = Config()
# Automatically load user's security configuration if present
config.load_security()
