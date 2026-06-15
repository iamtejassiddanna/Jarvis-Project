# J.A.R.V.I.S. — Just A Rather Very Intelligent System

A personal AI assistant inspired by Iron Man's JARVIS, built with Python and Google Gemini. Features a sleek HUD-style web interface, real-time streaming responses, voice input/output, and the ability to execute macOS system commands.

---

##  Project Objective

The objective of this project is to develop an intelligent virtual assistant capable of understanding user commands and performing automated tasks efficiently. The system aims to improve productivity by integrating voice interaction, information retrieval, and automation features into a single platform.

---

## Features

- **Conversational AI** — Powered by Gemini 2.5 Flash with persistent conversation memory (last 20 turns)
- **Streaming Responses** — Real-time sentence-by-sentence text and audio delivery via Server-Sent Events
- **Voice I/O** — Push-to-talk mic input (Web Speech API) and text-to-speech output (Microsoft Edge TTS, British male voice)
- **File Understanding** — Attach images or PDFs and ask JARVIS about them
- **System Command Execution** — JARVIS can open apps and control macOS via `<EXECUTE: ...>` commands embedded in AI responses
- **Online Skills** — Weather (OpenWeatherMap), top news headlines (NewsAPI), live data which includes sports score, Wikipedia search, IP lookup, and dad jokes
- **System Skills** — Current time, date, opening camera, calculator and other applications
- **Intent Detection** — Lightweight regex-based routing for fast responses to common queries (time, date, IP, jokes) before falling back to the LLM
- **Google Search Grounding** — Automatically enabled for queries about news, weather, sports, and more
- **HUD Interface** — Sci-fi themed web UI with animated orb, transcript panel, and live clock

---

## Project Structure

```
Jarvis-Project/
├── core/
│   ├── ai_brain.py       # Gemini client, system prompt, memory-aware chat & streaming
│   └── memory.py         # In-memory conversation history (rolling window)
├── server/
│   └── app.py            # FastAPI server — REST + SSE endpoints, TTS, intent routing
├── skills/
│   ├── device_control.py # Async shell command execution (macOS)
│   ├── online.py         # Weather, news, IP, jokes, Wikipedia, YouTube/Google
│   └── system.py         # Time, date, camera, calculator
├── ui/
│   ├── index.html        # HUD layout
│   ├── script.js         # Audio queue, streaming client, mic handling, file upload
│   └── style.css         # Sci-fi HUD styles (Orbitron font, animated rings)
└── requirement.txt       # Python dependencies
```

---

## Prerequisites

- Python 3.10+
- macOS / windows (device control features use `open` and `osascript`)
- A microphone (for voice mode)

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/iamtejassiddanna/Jarvis-Project.git
cd Jarvis-Project
```

### 2. Install dependencies

```bash
pip install -r requirement.txt
```

### 3. Configure API keys

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_google_gemini_api_key
NEWS_API_KEY=your_newsapi_org_key
OPENWEATHER_APP_ID=your_openweathermap_api_key
```

| Key | Where to get it |
|-----|-----------------|
| `GEMINI_API_KEY`     | [Google AI Studio](https://aistudio.google.com/app/apikey) |
| `NEWS_API_KEY`       | [NewsAPI.org](https://newsapi.org/) |
| `OPENWEATHER_APP_ID` | [OpenWeatherMap](https://openweathermap.org/api) |

### 4. Run the server

```bash
cd server
uvicorn app:app --reload --port 8000
```

### 5. Open the interface

Navigate to [http://localhost:8000/ui](http://localhost:8000/ui) in your browser.

---

## Usage

### Voice Mode (default)
Click **MIC** and speak your command. JARVIS will respond with both text (in the transcript panel) and audio.

### Text Mode
Click **AUDIO MODE** to toggle to text input. Type your query and press **SEND** (or hit Enter).

### File Attachments
In text mode, click **+** to attach an image or PDF, then ask JARVIS about it.

### Stop
Click **STOP** at any time to interrupt JARVIS mid-response.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/ping` | Health check |
| `GET` | `/status` | Current time and date |
| `GET` | `/wake` | Wake greeting with weather |
| `POST` | `/ask` | Single-shot query (returns full reply + audio) |
| `POST` | `/ask_stream` | Streaming query via SSE (sentence-by-sentence) |
| `GET` | `/weather/{city}` | Weather for a given city |
| `GET` | `/news` | Top 5 Indian news headlines |

### Request body for `/ask` and `/ask_stream`

```json
{
  "text": "What's the weather in Mumbai?",
  "file_data": "<base64-encoded file, optional>",
  "file_mime": "image/jpeg"
}
```

---

## How It Works

1. **Request arrives** → intent router checks for fast-path responses (time, date, IP, jokes)
2. **LLM path** → query keywords determine if Google Search grounding is enabled
3. **Streaming** → `ask_jarvis_stream` yields text chunks; sentence boundaries trigger TTS
4. **TTS worker** → each sentence is converted to MP3 via Edge TTS and base64-encoded
5. **SSE stream** → client receives `{ type: "sentence_audio", text, audio }` events and queues playback
6. **Command interception** → `<EXECUTE: ...>` tags are stripped from the response and run silently via `asyncio.create_subprocess_shell`

---

## Notes

- Device control commands (opening apps, controlling Spotify, etc.) use macOS-specific commands (`open`, `osascript`). They will not work on Windows or Linux.
- Weather defaults to Bangalore if no city is specified.
- Conversation memory resets when the server restarts (in-memory only).

---

## License

This project is licensed under the MIT License.
