import asyncio
import os
import sys

# Add current directory to path so it can import app
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from google.adk.runners import InMemoryRunner
from google.genai import types
from app.agent import app

async def main():
    runner = InMemoryRunner(app=app)
    session = await runner.session_service.create_session(
        app_name="app", user_id="test_user"
    )
    print("Session created:", session.id)
    
    # Run the query
    query = "What is a myocardial infarction and dyspnea?"
    print(f"Sending message: '{query}'")
    
    async for event in runner.run_async(
        user_id="test_user",
        session_id=session.id,
        new_message=types.Content(role="user", parts=[types.Part.from_text(text=query)]),
    ):
        print("Event Output:", event.output)
        print("Event Content:", event.content)
        print("Event Interrupted:", getattr(event, "interrupted", False))
        
        # Check if the session is interrupted for human review
        is_interrupt = any(fc.name == 'adk_request_input' for fc in event.get_function_calls())
        if is_interrupt:
            print("Interrupt detected. Resuming with approval...")
            await asyncio.sleep(1)
            resume_msg = types.Content(
                role="user",
                parts=[
                    types.Part(
                        function_response=types.FunctionResponse(
                            name="adk_request_input",
                            id="approve_guide",
                            response={"approve_guide": "yes"}
                        )
                    )
                ]
            )
            async for resume_event in runner.run_async(
                user_id="test_user",
                session_id=session.id,
                new_message=resume_msg
            ):
                print("Resume Event Output:", resume_event.output)
                print("Resume Event Content:", resume_event.content)

if __name__ == "__main__":
    asyncio.run(main())
