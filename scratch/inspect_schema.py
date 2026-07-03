import json
import os

path = os.path.join(os.path.dirname(__file__), "openapi.json")
with open(path) as f:
    schema = json.load(f)

for endpoint in ["/run", "/run_sse"]:
    print(f"\n=== Endpoint: {endpoint} ===")
    if endpoint in schema.get("paths", {}):
        post_info = schema["paths"][endpoint].get("post", {})
        print("Summary:", post_info.get("summary"))
        print("Description:", post_info.get("description"))
        
        request_body = post_info.get("requestBody", {})
        content = request_body.get("content", {})
        for content_type, details in content.items():
            print(f"Content Type: {content_type}")
            schema_ref = details.get("schema", {})
            ref = schema_ref.get("$ref")
            if ref:
                # Resolve ref
                ref_path = ref.split("/")
                current = schema
                for p in ref_path[1:]:
                    current = current[p]
                print("Request Schema Properties:")
                print(json.dumps(current.get("properties", {}), indent=2))
            else:
                print("Request Schema:", json.dumps(schema_ref, indent=2))
