# To start the server:
# sanic sanic_test.app --host=127.0.0.1 --port=8000
from sanic import Sanic
from sanic.response import json, text

app = Sanic("BenchmarkApp")

@app.get("/")
async def hello_world(request):
    return text("hello world")

@app.post("/test-benchmark")
async def benchmark_endpoint(request):
    data = request.json
    return json({
        "status": "success",
        "received_id": data.get("id"),
        "received_name": data.get("name"),
        "received_active_status": data.get("is_active"),
    })
