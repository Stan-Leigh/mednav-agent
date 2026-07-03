import asyncio
import os
import sys

# Add current directory to path
sys_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(sys_path)

from google.adk.runners import InMemoryRunner
from google.genai import types
from google.adk.apps import App
from app.agent import mednav_orchestrator

async def main():
    test_app = App(root_agent=mednav_orchestrator, name="test")
    runner = InMemoryRunner(app=test_app)
    session = await runner.session_service.create_session(
        app_name="test", user_id="test_user"
    )
    
    query = "What is a myocardial infarction and dyspnea?"
    print(f"Running query: '{query}'")
    
    async for event in runner.run_async(
        user_id="test_user",
        session_id=session.id,
        new_message=types.Content(role="user", parts=[types.Part.from_text(text=query)]),
    ):
        print("Event Content:", event.content)
        print("Event Output:", event.output)
        print("---")

if __name__ == "__main__":
    asyncio.run(main())
