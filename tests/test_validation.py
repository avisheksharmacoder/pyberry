import pytest
from dataclasses import dataclass
from pyberry import BaseModel
from pyberry.exceptions import UnprocessableEntityException
from pyberry.core.validation import compile_schema, validate_data
from pyberry.core.rsgi import app, router
from pyberry.core.responses import JSONResponse
from conftest import MockRSGIScope, MockRSGIProtocol
from pyberry.db import db
from unittest.mock import Mock
import json

@pytest.fixture(autouse=True)
def mock_db_init(monkeypatch):
    monkeypatch.setattr(db, "init_db", Mock())

class UserModel(BaseModel):
    id: int
    name: str
    is_active: bool = True

@dataclass
class DataClassModel:
    id: int
    name: str
    is_active: bool = True

def test_basemodel_validation_success():
    user = UserModel(id="123", name="Alice")
    assert user.id == 123
    assert user.name == "Alice"
    assert user.is_active is True

    user2 = UserModel(id=456, name="Bob", is_active="false")
    assert user2.id == 456
    assert user2.is_active is False

def test_basemodel_validation_failure():
    with pytest.raises(UnprocessableEntityException) as exc:
        UserModel(name="Alice")
    assert "Field 'id' is required" in exc.value.detail

    with pytest.raises(UnprocessableEntityException) as exc:
        UserModel(id="abc", name="Alice")
    assert "Field 'id' must be an integer" in exc.value.detail

def test_dataclass_validation_engine():
    schema = compile_schema(DataClassModel)
    
    # Valid
    validated = validate_data(schema, {"id": "123", "name": "Alice"})
    assert validated["id"] == 123
    assert validated["name"] == "Alice"
    assert "is_active" not in validated 
    
    dc = DataClassModel(**validated)
    assert dc.id == 123
    assert dc.name == "Alice"
    assert dc.is_active is True

    # Invalid
    with pytest.raises(UnprocessableEntityException):
        validate_data(schema, {"name": "Alice"})

@pytest.mark.asyncio
async def test_rsgi_basemodel_injection(mock_proto):
    def handler(req, user: UserModel):
        return JSONResponse({"id": user.id, "name": user.name})
        
    router.add_python_route("POST", "/test_basemodel", handler)
        
    scope = MockRSGIScope(method="POST", path="/test_basemodel", proto="http")
    mock_proto.body = json.dumps({"id": 999, "name": "Zack"}).encode("utf-8")
    
    await app(scope, mock_proto)
    
    assert mock_proto.response_called
    assert mock_proto.response_status == 200
    assert json.loads(mock_proto.response_body) == {"id": 999, "name": "Zack"}

@pytest.mark.asyncio
async def test_rsgi_dataclass_injection(mock_proto):
    def handler(req, dc: DataClassModel):
        return JSONResponse({"id": dc.id, "active": dc.is_active})
        
    router.add_python_route("POST", "/test_dataclass", handler)
        
    scope = MockRSGIScope(method="POST", path="/test_dataclass", proto="http")
    mock_proto.body = json.dumps({"id": 111, "name": "Dan"}).encode("utf-8")
    
    await app(scope, mock_proto)
    
    assert mock_proto.response_called
    assert mock_proto.response_status == 200
    assert json.loads(mock_proto.response_body) == {"id": 111, "active": True}
    
@pytest.mark.asyncio
async def test_rsgi_validation_error(mock_proto):
    def handler(req, user: UserModel):
        return JSONResponse({"ok": True})
        
    router.add_python_route("POST", "/test_invalid", handler)
        
    scope = MockRSGIScope(method="POST", path="/test_invalid", proto="http")
    mock_proto.body = json.dumps({"name": "No ID"}).encode("utf-8")
    
    await app(scope, mock_proto)
    
    assert mock_proto.response_called
    assert mock_proto.response_status == 422
    assert "Field 'id' is required" in mock_proto.response_body
