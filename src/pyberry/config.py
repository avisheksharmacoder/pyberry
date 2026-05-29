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
        
    def load_security(self):
        try:
            import security
            self.cors_enabled = getattr(security, 'CORS_ENABLED', True)
            self.allowed_hosts = getattr(security, 'ALLOWED_HOSTS', ["*"])
            self.logging_enabled = getattr(security, 'LOGGING_ENABLED', True)
            print("SECURITY LOADED:", self.allowed_hosts)
        except ImportError as e:
            print("SECURITY IMPORT ERROR:", e)
            pass

config = Config()
# Automatically load user's security configuration if present
config.load_security()
