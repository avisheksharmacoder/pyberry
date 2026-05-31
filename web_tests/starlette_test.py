# To start the server:
# uvicorn starlette_test:app --host 127.0.0.1 --port 8000
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse, JSONResponse
from starlette.routing import Route

async def hello_world(request):
    return PlainTextResponse("hello world")

async def benchmark_endpoint(request):
    data = await request.json()
    return JSONResponse({
        "status": "success",
        "received_id": data.get("id"),
        "received_name": data.get("name"),
        "received_active_status": data.get("is_active"),
    })

routes = [
    Route("/", endpoint=hello_world, methods=["GET"]),
    Route("/test-benchmark", endpoint=benchmark_endpoint, methods=["POST"])
]

app = Starlette(debug=False, routes=routes)
