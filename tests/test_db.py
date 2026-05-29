import pytest
import pytest_asyncio
import os
from pyberry.db import db

# Create a temporary local db for testing
TEST_DB_URL = "file:test_local.db"

@pytest_asyncio.fixture(autouse=True)
async def setup_teardown_db():
    db.init_db(TEST_DB_URL)
    
    # Create a test table
    await db.execute("""
        CREATE TABLE IF NOT EXISTS test_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT
        )
    """)
    await db.execute("DELETE FROM test_users")
    
    yield
    
    await db.close_db()
    if os.path.exists("test_local.db"):
        os.remove("test_local.db")

@pytest.mark.asyncio
async def test_db_execute_and_query():
    # Insert
    await db.execute("INSERT INTO test_users (name) VALUES (?)", ["Alice"])
    
    # Query
    users = await db.query("SELECT * FROM test_users")
    assert len(users) == 1
    assert users[0]["name"] == "Alice"
    assert "id" in users[0]

@pytest.mark.asyncio
async def test_db_query_first():
    await db.execute("INSERT INTO test_users (name) VALUES (?)", ["Bob"])
    await db.execute("INSERT INTO test_users (name) VALUES (?)", ["Charlie"])
    
    user = await db.query_first("SELECT * FROM test_users WHERE name = ?", ["Charlie"])
    assert user is not None
    assert user["name"] == "Charlie"
    
    non_existent = await db.query_first("SELECT * FROM test_users WHERE name = ?", ["David"])
    assert non_existent is None

@pytest.mark.asyncio
async def test_db_update():
    await db.execute("INSERT INTO test_users (name) VALUES (?)", ["Eve"])
    
    # Update
    await db.execute("UPDATE test_users SET name = ? WHERE name = ?", ["Eva", "Eve"])
    
    # Verify
    user = await db.query_first("SELECT * FROM test_users WHERE name = ?", ["Eva"])
    assert user is not None
    assert user["name"] == "Eva"

@pytest.mark.asyncio
async def test_db_delete():
    await db.execute("INSERT INTO test_users (name) VALUES (?)", ["Frank"])
    
    # Delete
    await db.execute("DELETE FROM test_users WHERE name = ?", ["Frank"])
    
    # Verify
    user = await db.query_first("SELECT * FROM test_users WHERE name = ?", ["Frank"])
    assert user is None

@pytest.mark.asyncio
async def test_db_returning():
    # Insert with RETURNING clause
    user = await db.query_first(
        "INSERT INTO test_users (name) VALUES (?) RETURNING *", 
        ["Grace"]
    )
    
    assert user is not None
    assert user["name"] == "Grace"
    assert "id" in user
