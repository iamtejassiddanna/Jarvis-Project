import warnings
warnings.filterwarnings("ignore")

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response
from pydantic import BaseModel
import edge_tts
import base64

from core.ai_brain import ask_jarvis

from skills.online import get_joke, get_ip, search_wikipedia, get_weather, get_news
from skills.system import get_time, get_date
from skills.device_control import execute_system_command
app = FastAPI(title="JARVIS API")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

class Query(BaseModel):
    text: str
    file_data: str | None = None
    file_mime: str | None = None

def process(text: str) -> str:
    q = text.lower()
    intent = "general_chat"
    confidence = 0.0
    
    if re.search(r'\bjoke\b', q): intent, confidence = "joke", 1.0
    elif re.search(r'\bip\b', q) and ("address" in q or "my" in q): intent, confidence = "ip_address", 1.0
    elif re.search(r'\btime\b', q) and "what" in q: intent, confidence = "time", 1.0
    elif re.search(r'\bdate\b', q) or "day is it" in q: intent, confidence = "date", 1.0
    
    if confidence > 0.55:
        if   intent == "joke":       return get_joke()
        elif intent == "ip_address": return f"Your IP is {get_ip()} Sir."
        elif intent == "time":       return f"The time is {get_time()} Sir."
        elif intent == "date":       return f"Today is {get_date()} Sir."
    
    needs_search = bool(re.search(r'\b(news|sports|ipl|score|match|update|search|who|what|where|why|how|weather|today|yesterday|wikipedia)\b', q))
    return ask_jarvis(text, enable_search=needs_search)

# Add this after middleware
app.mount("/ui", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "../ui"), html=True), name="ui")

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)

@app.get("/ping")
def root():
    return {"status": "JARVIS online", "version": "2.0"}

@app.post("/ask")
async def ask(query: Query):
    reply_text = process(query.text)
    
    file_path = f"/tmp/jarvis_ui_resp.mp3"
    communicate = edge_tts.Communicate(reply_text, "en-GB-RyanNeural")
    await communicate.save(file_path)
    
    with open(file_path, "rb") as f:
        audio_b64 = base64.b64encode(f.read()).decode("utf-8")
        
    return {"reply": reply_text, "audio": audio_b64}

import json
import re
import asyncio
from fastapi.responses import StreamingResponse
from core.ai_brain import ask_jarvis_stream

@app.post("/ask_stream")
async def ask_stream(query: Query):
    async def generate():
        q = query.text.lower()
        intent = "general_chat"
        confidence = 0.0
        
        if re.search(r'\bjoke\b', q): intent, confidence = "joke", 1.0
        elif re.search(r'\bip\b', q) and ("address" in q or "my" in q): intent, confidence = "ip_address", 1.0
        elif re.search(r'\btime\b', q) and "what" in q: intent, confidence = "time", 1.0
        elif re.search(r'\bdate\b', q) or "day is it" in q: intent, confidence = "date", 1.0
        
        # Static responses can just be sent in one go
        if confidence > 0.55 and intent in ["joke", "ip_address", "time", "date"]:
            if intent == "joke":       reply_text = get_joke()
            elif intent == "ip_address": reply_text = f"Your IP is {get_ip()} Sir."
            elif intent == "time":       reply_text = f"The time is {get_time()} Sir."
            elif intent == "date":       reply_text = f"Today is {get_date()} Sir."
            
            file_path = f"/tmp/jarvis_ui_resp.mp3"
            communicate = edge_tts.Communicate(reply_text, "en-GB-RyanNeural")
            await communicate.save(file_path)
            with open(file_path, "rb") as f:
                audio_b64 = base64.b64encode(f.read()).decode("utf-8")
            yield f"data: {json.dumps({'type': 'sentence_audio', 'text': reply_text, 'audio': audio_b64})}\n\n"
            return

        # Dynamic AI stream
        queue = asyncio.Queue()
        sentence_queue = asyncio.Queue()
        
        async def tts_worker():
            while True:
                sentence = await sentence_queue.get()
                if sentence is None:
                    break
                try:
                    tts_sentence = re.sub(r'[*_#`]', '', sentence)
                    file_path = f"/tmp/jarvis_ui_resp_chunk.mp3"
                    communicate = edge_tts.Communicate(tts_sentence, "en-GB-RyanNeural")
                    await communicate.save(file_path)
                    with open(file_path, "rb") as f:
                        audio_b64 = base64.b64encode(f.read()).decode("utf-8")
                    await queue.put({'type': 'sentence_audio', 'text': sentence, 'audio': audio_b64})
                except Exception as e:
                    print("TTS Error:", e)
                finally:
                    sentence_queue.task_done()
            await queue.put({'type': 'tts_done'})

        async def llm_worker():
            sentence_buffer = ""
            try:
                needs_search = bool(re.search(r'\b(news|sports|ipl|score|match|update|search|who|what|where|why|how|weather|today|yesterday|wikipedia)\b', q))
                async for chunk in ask_jarvis_stream(query.text, enable_search=needs_search, file_data=query.file_data, file_mime=query.file_mime):
                    sentence_buffer += chunk
                    
                    # Intercept execution commands
                    while True:
                        cmd_match = re.search(r'<EXECUTE:\s*(.*?)\s*>', sentence_buffer)
                        if not cmd_match:
                            break
                        cmd = cmd_match.group(1)
                        asyncio.create_task(execute_system_command(cmd))
                        sentence_buffer = sentence_buffer[:cmd_match.start()] + sentence_buffer[cmd_match.end():]

                    match = re.search(r'([.!?])\s+', sentence_buffer)
                    if match:
                        end_idx = match.end()
                        sentence = sentence_buffer[:end_idx].lstrip()
                        sentence_buffer = sentence_buffer[end_idx:]
                        if sentence.strip():
                            await sentence_queue.put(sentence)
                if sentence_buffer.strip():
                    await sentence_queue.put(sentence_buffer.strip())
            except Exception as e:
                print("LLM Error:", e)
            finally:
                await queue.put({'type': 'llm_done'})
                await sentence_queue.put(None) # Signal TTS worker to stop

        asyncio.create_task(llm_worker())
        asyncio.create_task(tts_worker())

        llm_is_done = False
        tts_is_done = False
        while True:
            item = await queue.get()
            if item['type'] == 'sentence_audio':
                yield f"data: {json.dumps({'type': 'sentence_audio', 'text': item['text'], 'audio': item['audio']})}\n\n"
            elif item['type'] == 'llm_done':
                llm_is_done = True
            elif item['type'] == 'tts_done':
                tts_is_done = True
                
            if llm_is_done and tts_is_done and queue.empty():
                break
            
    return StreamingResponse(generate(), media_type="text/event-stream")

@app.get("/wake")
async def wake():
    weather_info = get_weather("Bangalore")
    reply_text = f"Hello Sir. I am online. {weather_info} How can I help you?"
    
    file_path = f"/tmp/jarvis_ui_wake.mp3"
    communicate = edge_tts.Communicate(reply_text, "en-GB-RyanNeural")
    await communicate.save(file_path)
    
    with open(file_path, "rb") as f:
        audio_b64 = base64.b64encode(f.read()).decode("utf-8")
        
    return {"reply": reply_text, "audio": audio_b64}

@app.get("/status")
def status():
    return {"status": "online", "time": get_time(), "date": get_date()}

@app.get("/weather/{city}")
def weather(city: str = "Bangalore"):
    return {"weather": get_weather(city)}

@app.get("/news")
def news():
    return {"headlines": get_news()}
