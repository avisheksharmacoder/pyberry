# To start the server:
# gunicorn falcon_test:app -b 127.0.0.1:8000
import falcon
import json

class HelloResource:
    def on_get(self, req, resp):
        resp.text = "hello world"

class BenchmarkResource:
    def on_post(self, req, resp):
        data = json.load(req.bounded_stream)
        resp.media = {
            "status": "success",
            "received_id": data.get("id"),
            "received_name": data.get("name"),
            "received_active_status": data.get("is_active"),
        }

app = falcon.App()
app.add_route("/", HelloResource())
app.add_route("/test-benchmark", BenchmarkResource())
