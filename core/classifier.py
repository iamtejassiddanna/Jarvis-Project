import warnings
warnings.filterwarnings("ignore")

from google import genai
from google.genai import types
from decouple import config
import json

client = genai.Client(api_key=config("GEMINI_API_KEY"))

INTENTS_PROMPT = """
You are an intent classification engine for JARVIS AI.
Classify the user's query into EXACTLY ONE of these intents:
[
  "play_youtube", "google_search", "wikipedia", 
  "open_camera", "open_calculator", "joke", "ip_address", "time", 
  "date", "general_chat"
]
Always return pure JSON.
Example:
{"intent": "general_chat", "confidence": 0.99}
If none match, use "general_chat".
"""

def classify(query: str):
    try:
        response = client.models.generate_content(
            model="gemini-flash-lite-latest",
            contents=query,
            config=types.GenerateContentConfig(
                system_instruction=INTENTS_PROMPT,
                response_mime_type="application/json"
            )
        )
        data = json.loads(response.text)
        return data.get("intent", "general_chat"), float(data.get("confidence", 0.9))
    except Exception as e:
        print(f"Classifier Error: {e}")
        return "general_chat", 0.0
