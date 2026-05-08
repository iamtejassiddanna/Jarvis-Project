from google import genai
from google.genai import types
import os
from decouple import config

client = genai.Client(api_key=config("GEMINI_API_KEY"))
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="What is the weather in Paris today?",
    config=types.GenerateContentConfig(
        tools=[{"google_search": {}}]
    )
)
print("Response:", response.text)
if response.candidates[0].grounding_metadata:
    print("Grounding successful")
