import asyncio
import httpx
import os
import sys

async def main():
    async with httpx.AsyncClient() as client:
        # Start a session
        url = "http://127.0.0.1:8000/apps/app/users/test_user/sessions"
        res = await client.post(url)
        session = res.json()
        session_id = session["id"]
        print("Created Session ID:", session_id)
        
        # Run agent query
        run_url = "http://127.0.0.1:8000/run_sse"
        payload = {
            "appName": "app",
            "userId": "test_user",
            "sessionId": session_id,
            "newMessage": {
                "role": "user",
                "parts": [
                    {"text": "What is a myocardial infarction?"}
                ]
            }
        }
        
        print("Sending query to /run_sse...")
        async with client.stream("POST", run_url, json=payload, timeout=60.0) as response:
            async for line in response.aiter_lines():
                if line:
                    print("SSE Line:", line)

if __name__ == "__main__":
    asyncio.run(main())
