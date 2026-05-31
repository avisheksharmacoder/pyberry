# To start the server with 1 worker:
# python robyn_test.py --workers 1
import json
from robyn import Robyn, jsonify

app = Robyn(__file__)

@app.get("/")
def hello_world(request):
    return "hello world"

@app.post("/test-benchmark")
def benchmark_endpoint(request):
    # Robyn stores the request body in request.body
    body = request.body if isinstance(request.body, str) else request.body.decode('utf-8')
    data = json.loads(body)
    
    return jsonify({
        "status": "success",
        "received_id": data.get("id"),
        "received_name": data.get("name"),
        "received_active_status": data.get("is_active"),
    })

if __name__ == "__main__":
    app.start(port=8000, host="127.0.0.1")
