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
