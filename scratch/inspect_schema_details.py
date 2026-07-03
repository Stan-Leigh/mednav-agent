import json
import os

path = os.path.join(os.path.dirname(__file__), "openapi.json")
with open(path) as f:
    schema = json.load(f)

schemas = schema.get("components", {}).get("schemas", {})

for name in ["Content", "Part", "FunctionResponse"]:
    if name in schemas:
        print(f"\n=== Schema: {name} ===")
        print(json.dumps(schemas[name], indent=2))
