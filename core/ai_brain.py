import warnings
warnings.filterwarnings("ignore")

from google import genai
from google.genai import types
from decouple import config
from core.memory import Memory

client = genai.Client(api_key=config("GEMINI_API_KEY"))
memory = Memory()

SYSTEM_PROMPT = """
You are JARVIS — Just A Rather Very Intelligent System.
You are Tejas's personal AI assistant.
Tejas created you.
You are highly intelligent, speak formally and professionally.
Always address the user as Sir.
Give concise, helpful, accurate answers in 1 to 3 sentences only.
Never show errors, codes, or technical details to the user.
If you don't know something, say so politely.
If the user asks for the weather without specifying a location, assume the default location is Bangalore.
Always include the current temperature in celsius and humidit percentage and inform upcoming weather changes when asked about the weather.
"""

def ask_jarvis(user_input: str) -> str:
    try:
        memory.add_user(user_input)
        history = [
            types.Content(
                role=m["role"] if m["role"] != "assistant" else "model",
                parts=[types.Part(text=m["content"])]
            )
            for m in memory.get()
        ]
        response = client.models.generate_content(
            model="gemini-flash-lite-latest",
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                max_output_tokens=1024,
            ),
            contents=history
        )
        reply = response.text.strip()
        memory.add_jarvis(reply)
        return reply
    except Exception:
        return "I am having trouble connecting Sir. Please try again."

async def ask_jarvis_stream(user_input: str):
    try:
        memory.add_user(user_input)
        history = [
            types.Content(
                role=m["role"] if m["role"] != "assistant" else "model",
                parts=[types.Part(text=m["content"])]
            )
            for m in memory.get()
        ]
        response_stream = await client.aio.models.generate_content_stream(
            model="gemini-flash-lite-latest",
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                max_output_tokens=1024,
            ),
            contents=history
        )
        
        full_reply = ""
        async for chunk in response_stream:
            if chunk.text:
                full_reply += chunk.text
                yield chunk.text
                
        memory.add_jarvis(full_reply.strip())
    except Exception as e:
        yield "I am having trouble connecting Sir. Please try again."