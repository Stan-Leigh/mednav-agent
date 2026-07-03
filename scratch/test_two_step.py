import os
from dotenv import load_dotenv
from google.genai import Client
from google.genai import types

load_dotenv()
client = Client(api_key=os.getenv("GOOGLE_API_KEY"))

model = "gemini-2.5-flash-lite"
contents = [
    types.Content(role="user", parts=[types.Part.from_text(text="What is a myocardial infarction and dyspnea?")]),
    types.Content(role="model", parts=[
        types.Part(
            function_call=types.FunctionCall(
                name="MedJargonAgent",
                args={"request": "What is a myocardial infarction and dyspnea?"},
                id="call-1"
            )
        )
    ]),
    types.Content(role="user", parts=[
        types.Part(
            function_response=types.FunctionResponse(
                name="MedJargonAgent",
                response={"result": "A myocardial infarction is a heart attack. Dyspnea is shortness of breath."},
                id="call-1"
            )
        )
    ])
]

# Supply the tool declaration
config = types.GenerateContentConfig(
    system_instruction="You are the MedNav Orchestrator. Compile the results from your sub-agents into a simple response.",
    tools=[
        types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name="MedJargonAgent",
                    description="Specialist in medical jargon.",
                    parameters=types.Schema(
                        type="OBJECT",
                        properties={
                            "request": types.Schema(type="STRING", description="Term to explain")
                        },
                        required=["request"]
                    )
                )
            ]
        )
    ]
)

try:
    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=config
    )
    print("Response text:", response.text)
    print("Candidates:", response.candidates)
except Exception as e:
    print("Error:", e)
