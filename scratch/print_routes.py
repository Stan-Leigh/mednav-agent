import os
import sys
from fastapi.routing import APIRoute

# Add app parent directory to python path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from app.fast_api_app import app

print("=== FASTAPI ROUTES ===")
for route in app.routes:
    if isinstance(route, APIRoute):
        print(f"Path: {route.path} | Methods: {route.methods} | Name: {route.name}")
