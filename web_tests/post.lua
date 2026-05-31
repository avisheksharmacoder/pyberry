-- post.lua
wrk.method = "POST"
wrk.body   = '{"id": 1, "name": "BenchTest", "is_active": true}'
wrk.headers["Content-Type"] = "application/json"
wrk.headers["Connection"] = "keep-alive"

