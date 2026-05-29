# Database Integration (LibSQL)

PyBerry comes with high-performance, native support for **LibSQL**, the open-source and edge-ready fork of SQLite. It allows you to build extremely fast edge applications while maintaining the simplicity of traditional SQLite.

Our database integration uses an asynchronous wrapper (`libsql-client`) to prevent I/O blocking in the free-threaded worker environment.

## 1. Project Scaffold and Folder Structure
When you create a new project using `pyberry create <name>`, PyBerry automatically scaffolds a `db/` folder inside the root directory.

```text
my_project/
├── db/
│   ├── initial_schema.sql  # Your SQL migrations and table setups
│   └── local.db            # Your local development database (created at runtime)
├── main.py
└── security.py
```

## 2. Configuration (`security.py`)
By default, your PyBerry project is configured to use the local database file. Inside `security.py`, you'll find the configuration settings:

```python
from pyberry.config import config

# Set to "file:db/local.db" for local development
# Set to "libsql://<your-db>.turso.io" for edge production!
config.libsql_url = "file:db/local.db"
config.libsql_auth_token = None # Replace with your Turso Auth Token in production
```

When your PyBerry application starts up, the RSGI server automatically hooks into the core database client, establishing a warm connection pool on the very first request so that all subsequent requests resolve instantly.

## 3. Writing and Running Migrations

PyBerry handles database migrations using simple, raw SQL files. Your project comes with a `db/initial_schema.sql` file out-of-the-box.

Write your SQL queries inside `initial_schema.sql`:
```sql
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL
);
```

You can execute these schemas to sync your database using the CLI:
```bash
# Runs the default db/initial_schema.sql against your LIBSQL_URL
pyberry migrate

# Runs a specific schema file
pyberry migrate --file db/updates.sql
```

## 4. Querying the Database
Because PyBerry handles the connection pool natively, you can easily access the database from any file or route by importing the globally shared `db` instance from `pyberry.db`.

Our asynchronous database API exposes 3 main methods tailored for speed:

### `db.execute(query, params)`
Used for `INSERT`, `UPDATE`, `DELETE`, and `CREATE` statements where no returned rows are expected.

```python
from pyberry.core.responses import JSONResponse
from pyberry.db import db

async def create_user(req):
    # Execute the raw SQL statement asynchronously
    await db.execute(
        "INSERT INTO users (name, email) VALUES (?, ?)", 
        ["John Doe", "john@example.com"]
    )
    return JSONResponse({"status": "created"})
```

### `db.query(query, params)`
Used for `SELECT` statements where you expect a list of rows to be returned. The results are automatically parsed into standard Python dictionaries for incredibly easy JSON serialization.

```python
async def get_users(req):
    # Returns a list of dictionaries: [{"id": 1, "name": "John Doe", ...}]
    users = await db.query("SELECT * FROM users")
    return JSONResponse({"data": users})
```

### `db.query_first(query, params)`
Used for `SELECT` statements where you only want the very first row returned (or `None` if it doesn't exist). Extremely useful for lookups.

```python
async def get_user(req, user_id: int):
    # Returns a single dictionary or None
    user = await db.query_first(
        "SELECT * FROM users WHERE id = ?", 
        [user_id]
    )
    
    if not user:
        return JSONResponse({"error": "Not Found"}, status_code=404)
        
    return JSONResponse(user)
```

### Advanced: Updates and Deletions
You can run `UPDATE` and `DELETE` commands seamlessly using `db.execute()`. 

```python
async def update_user(req, user_id: int):
    # Update a user's name
    await db.execute(
        "UPDATE users SET name = ? WHERE id = ?",
        ["Jane Doe", user_id]
    )
    return JSONResponse({"status": "updated"})

async def delete_user(req, user_id: int):
    # Delete a user
    await db.execute(
        "DELETE FROM users WHERE id = ?",
        [user_id]
    )
    return JSONResponse({"status": "deleted"})
```

### Advanced: Using `RETURNING` for instant lookups
Because LibSQL supports modern SQLite features like the `RETURNING` clause, you can insert or update records and get the updated row back immediately using `db.query_first()` instead of `db.execute()`.

```python
async def create_and_get_user(req):
    # Insert and immediately get the generated ID and data back!
    new_user = await db.query_first(
        "INSERT INTO users (name, email) VALUES (?, ?) RETURNING *", 
        ["Alice", "alice@example.com"]
    )
    
    # new_user is {"id": 2, "name": "Alice", "email": "alice@example.com"}
    return JSONResponse({"created": new_user})
```

## 5. Deployment / Edge Production

When you are ready to deploy your application to an edge network (like Turso), simply update your `security.py` (or inject via environment variables):

```python
import os

config.libsql_url = os.environ.get("LIBSQL_URL", "file:db/local.db")
config.libsql_auth_token = os.environ.get("LIBSQL_AUTH_TOKEN")
```

The `pyberry migrate` and PyBerry core runtime are fully agnostic; they will connect remotely over HTTP/WebSocket without any changes to your route code!
