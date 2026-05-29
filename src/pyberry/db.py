import libsql_client

class DatabaseManager:
    def __init__(self):
        self.client = None

    def init_db(self, url: str, auth_token: str = None):
        if self.client is None:
            # libsql_client.create_client can be called synchronously
            # and returns an async client.
            self.client = libsql_client.create_client(url, auth_token=auth_token)

    async def close_db(self):
        if self.client is not None:
            await self.client.close()
            self.client = None

    async def execute(self, sql: str, args: list = None):
        if not self.client:
            raise RuntimeError("Database not initialized. Ensure LIBSQL_URL is set.")
        return await self.client.execute(sql, args or [])

    async def query(self, sql: str, args: list = None):
        if not self.client:
            raise RuntimeError("Database not initialized. Ensure LIBSQL_URL is set.")
        result = await self.client.execute(sql, args or [])
        return [dict(zip(result.columns, row)) for row in result.rows]

    async def query_first(self, sql: str, args: list = None):
        rows = await self.query(sql, args)
        return rows[0] if rows else None

db = DatabaseManager()
