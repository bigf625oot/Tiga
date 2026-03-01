
import sys
import os
from fastapi import FastAPI
from fastapi.routing import APIRoute

# Add backend to path
sys.path.append(os.getcwd())

# Import app creation logic
from app.main import app

def print_routes(routes):
    for route in routes:
        if isinstance(route, APIRoute):
            methods = ", ".join(route.methods)
            print(f"{methods} {route.path}")
        elif hasattr(route, "routes"):  # Router or Mount with routes
            print_routes(route.routes)

print("--- Registered Routes ---")
print_routes(app.routes)
