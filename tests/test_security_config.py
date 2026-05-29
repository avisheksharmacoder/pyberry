import pytest
import sys
from unittest.mock import MagicMock
from pyberry.config import Config

def test_load_security_success(monkeypatch):
    mock_security = MagicMock()
    mock_security.CORS_ENABLED = False
    mock_security.ALLOWED_HOSTS = ["custom.com"]
    mock_security.SECURITY_HEADERS_ENABLED = False
    mock_security.RATE_LIMIT_ENABLED = True
    mock_security.MAX_BODY_SIZE = 5000
    
    monkeypatch.setitem(sys.modules, 'security', mock_security)
    
    c = Config()
    c.load_security()
    
    assert c.cors_enabled is False
    assert c.allowed_hosts == ["custom.com"]
    assert c.security_headers_enabled is False
    assert c.rate_limit_enabled is True
    assert c.max_body_size == 5000

def test_load_security_missing(monkeypatch):
    if 'security' in sys.modules:
        monkeypatch.delitem(sys.modules, 'security')
        
    c = Config()
    c.load_security()
    
    # Should fall back to defaults without crashing
    assert c.cors_enabled is True
    assert c.allowed_hosts == ["*"]
    assert c.security_headers_enabled is True
    assert c.path_traversal_protection is True
    assert c.max_body_size == 1048576
    assert c.rate_limit_enabled is False
