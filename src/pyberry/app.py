from pyberry.core.rsgi import router

def get(path):
    def decorator(func):
        print("REGISTERING:", path); router.add_python_route("GET", path, func)
        return func
    return decorator

def post(path):
    def decorator(func):
        router.add_python_route("POST", path, func)
        return func
    return decorator

def put(path):
    def decorator(func):
        router.add_python_route("PUT", path, func)
        return func
    return decorator

def patch(path):
    def decorator(func):
        router.add_python_route("PATCH", path, func)
        return func
    return decorator

def delete(path):
    def decorator(func):
        router.add_python_route("DELETE", path, func)
        return func
    return decorator

def options(path):
    def decorator(func):
        router.add_python_route("OPTIONS", path, func)
        return func
    return decorator

def head(path):
    def decorator(func):
        router.add_python_route("HEAD", path, func)
        return func
    return decorator
