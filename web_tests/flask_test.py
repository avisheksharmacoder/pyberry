# To start the server:
# flask --app flask_test run --port 8000
# OR: gunicorn flask_test:app -b 127.0.0.1:8000
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/", methods=["GET"])
def hello_world():
    return "hello world"

@app.route("/test-benchmark", methods=["POST"])
def benchmark_endpoint():
    data = request.get_json()
    return jsonify({
        "status": "success",
        "received_id": data.get("id"),
        "received_name": data.get("name"),
        "received_active_status": data.get("is_active"),
    })
