from core.ai_brain import ask_jarvis
import sys
import traceback

from core.ai_brain import client, memory, SYSTEM_PROMPT
from google.genai import types

def ask_jarvis_debug(user_input):
    try:
        memory.add_user(user_input)
        history = [
            types.Content(
                role=m["role"] if m["role"] != "assistant" else "model",
                parts=[types.Part.from_text(text=m["content"])]
            )
            for m in memory.get()
        ]
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                max_output_tokens=300,
                tools=[{"google_search": {}}],
            ),
            contents=history
        )
        reply = response.text.strip()
        memory.add_jarvis(reply)
        return reply
    except Exception as e:
        traceback.print_exc()
        return "I am having trouble connecting Sir. Please try again."

print(ask_jarvis_debug("What is the weather in Paris?"))
