import warnings
warnings.filterwarnings("ignore")

import asyncio
import edge_tts
from datetime import datetime
import subprocess
import os

VOICE = "en-GB-RyanNeural"  # Professional British voice

async def _save_audio(text: str, file_path: str):
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(file_path)

def speak(text: str):
    # Print logic
    time_now = datetime.now().strftime("%H:%M:%S")
    print("\n" + "─" * 52)
    print(f"  🤖  JARVIS  [{time_now}]")
    print("─" * 52)
    words = text.split()
    line  = ""
    for word in words:
        if len(line) + len(word) + 1 > 48:
            print(f"  {line}")
            line = word
        else:
            line += (" " if line else "") + word
    if line:
        print(f"  {line}")
    print("─" * 52 + "\n")
    
    # Audio logic
    file_path = "/tmp/jarvis_speech.mp3"
    try:
        asyncio.run(_save_audio(text, file_path))
        subprocess.run(["afplay", file_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"Audio Error: {e}")
