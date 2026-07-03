import os
from dotenv import load_dotenv
from google.genai import Client

# Add current directory to path
sys_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

load_dotenv(os.path.join(sys_path, ".env"))

client = Client(api_key=os.getenv("GOOGLE_API_KEY"))
try:
    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents="Translate myocardial infarction into simple English"
    )
    print("Response text:", response.text)
    print("Finish reason:", response.candidates[0].finish_reason if response.candidates else "No candidates")
except Exception as e:
    print("Error:", e)
