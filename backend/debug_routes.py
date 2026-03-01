
import sys
import os
import asyncio
from fastapi import FastAPI

# Add backend to path
sys.path.append(os.getcwd())

# Import app creation logic (simplified)
from app.main import app

print("--- Registered Routes ---")
for route in app.routes:
    if hasattr(route, "path"):
        print(f"{route.methods} {route.path}")
