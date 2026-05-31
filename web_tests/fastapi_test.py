# To start the server:
# uvicorn fastapi_test:app --host 127.0.0.1 --port 8000
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class TestModel(BaseModel):
    id: int
    name: str
    is_active: bool

@app.get("/")
def hello_world():
    return "hello world"

@app.post("/test-benchmark")
def benchmark_endpoint(data: TestModel):
    return {
        "status": "success",
        "received_id": data.id,
        "received_name": data.name,
        "received_active_status": data.is_active,
    }
