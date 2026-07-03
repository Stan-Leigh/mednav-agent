import os
import sys
import json

# Add app parent directory to python path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from app.fast_api_app import app

openapi_schema = app.openapi()
output_path = os.path.join(os.path.dirname(__file__), "openapi.json")

with open(output_path, "w") as f:
    json.dump(openapi_schema, f, indent=2)

print(f"OpenAPI schema written to {output_path}")
