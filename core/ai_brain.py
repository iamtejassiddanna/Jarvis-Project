import warnings
warnings.filterwarnings("ignore")

from google import genai
from google.genai import types
from decouple import config
from core.memory import Memory
import base64

client = genai.Client(api_key=config("GEMINI_API_KEY"))
memory = Memory()

from skills.system import get_time, get_date

def get_system_prompt():
    return f"""
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
Current time: {get_time()}
Current date: {get_date()}
"""

def ask_jarvis(user_input: str, enable_search: bool = False) -> str:
    try:
        memory.add_user(user_input)
        history = [
            types.Content(
                role=m["role"] if m["role"] != "assistant" else "model",
                parts=[types.Part(text=m["content"])]
            )
            for m in memory.get()
        ]
        
        cfg = types.GenerateContentConfig(
            system_instruction=get_system_prompt(),
            max_output_tokens=1024,
        )
        if enable_search:
            cfg.tools = [{"google_search": {}}]
            
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            config=cfg,
            contents=history
        )
        reply = response.text.strip()
        memory.add_jarvis(reply)
        return reply
    except Exception:
        return "I am having trouble connecting Sir. Please try again."

async def ask_jarvis_stream(user_input: str, enable_search: bool = False, file_data: str = None, file_mime: str = None):
    try:
        memory.add_user(user_input)
        
        mem_list = memory.get()
        history = []
        for i, m in enumerate(mem_list):
            parts = [types.Part.from_text(text=m["content"])]
            
            # If it's the latest user message and a file is attached
            if i == len(mem_list) - 1 and file_data and file_mime:
                if "," in file_data:
                    file_data = file_data.split(",")[1]
                file_bytes = base64.b64decode(file_data)
                parts.append(types.Part.from_bytes(data=file_bytes, mime_type=file_mime))
                
            history.append(types.Content(
                role=m["role"] if m["role"] != "assistant" else "model",
                parts=parts
            ))
        
        cfg = types.GenerateContentConfig(
            system_instruction=get_system_prompt(),
            max_output_tokens=1024,
        )
        if enable_search:
            cfg.tools = [{"google_search": {}}]
            
        response_stream = await client.aio.models.generate_content_stream(
            model="gemini-2.5-flash",
            config=cfg,
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