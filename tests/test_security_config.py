import pytest
import sys
from unittest.mock import MagicMock
from pyberry.config import Config

def test_load_security_success(monkeypatch):
    mock_security = MagicMock()
    mock_security.CORS_ENABLED = False
    mock_security.ALLOWED_HOSTS = ["custom.com"]
    
    monkeypatch.setitem(sys.modules, 'security', mock_security)
    
    c = Config()
    c.load_security()
    
    assert c.cors_enabled is False
    assert c.allowed_hosts == ["custom.com"]

def test_load_security_missing(monkeypatch):
    if 'security' in sys.modules:
        monkeypatch.delitem(sys.modules, 'security')
        
    c = Config()
    c.load_security()
    
    # Should fall back to defaults without crashing
    assert c.cors_enabled is True
    assert c.allowed_hosts == ["*"]
