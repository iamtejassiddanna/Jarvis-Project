import warnings
warnings.filterwarnings("ignore")

from datetime import datetime
from core.ai_brain import ask_jarvis
from core.classifier import classify
from speech.listener import listen
from speech.speaker import speak
from speech.wakeword import wait_for_wake_word
from skills.online import (get_joke, get_ip, search_wikipedia, play_youtube, search_google)
from skills.system import (get_time, get_date, open_camera, open_calculator)

def print_banner():
    print("\n" + "=" * 52)
    print("        J A R V I S")
    print("   Just A Rather Very Intelligent System")
    print("=" * 52)
    print(f"  Status    : ONLINE")
    print(f"  AI Model  : Gemini 2.5 Flash")
    print(f"  STT       : Whisper Base")
    print(f"  Wake Word : Hey Jarvis")
    print(f"  Started   : {datetime.now().strftime('%d %b %Y  %H:%M:%S')}")
    print("=" * 52 + "\n")

def greet():
    hour = datetime.now().hour
    if   6  <= hour < 12: speak("Good morning Sir.")
    elif 12 <= hour < 17: speak("Good afternoon Sir.")
    else:                  speak("Good evening Sir.")
    speak("J.A.R.V.I.S online. All systems operational. How may I assist you?")

def handle(intent: str, query: str):
    if   intent == "play_youtube":    play_youtube(query); speak("Playing on YouTube Sir.")
    elif intent == "google_search":   search_google(query); speak("Searching Google Sir.")
    elif intent == "wikipedia":       speak(search_wikipedia(query))
    elif intent == "joke":            speak(get_joke())
    elif intent == "open_camera":     open_camera();        speak("Opening camera Sir.")
    elif intent == "open_calculator": open_calculator();    speak("Opening calculator Sir.")
    elif intent == "ip_address":      speak(f"Your IP is {get_ip()} Sir.")
    elif intent == "time":            speak(f"The time is {get_time()} Sir.")
    elif intent == "date":            speak(f"Today is {get_date()} Sir.")
    else:                             speak(ask_jarvis(query))

def run():
    print_banner()
    greet()
    while True:
        try:
            wait_for_wake_word()
            speak("Yes Sir?")
            query = listen(duration=6)
            if not query:
                speak("I did not catch that Sir. Please try again.")
                continue
            if any(w in query.lower() for w in
                   ["stop", "exit", "goodbye", "shut down", "thank you", "thanks"]):
                speak("Shutting down. Goodbye Sir.")
                break
            intent, confidence = classify(query.lower())
            print(f"\n  📊  Intent     : {intent}")
            print(f"  📈  Confidence : {confidence:.0%}\n")
            if confidence > 0.55:
                handle(intent, query)
            else:
                speak(ask_jarvis(query))
        except KeyboardInterrupt:
            speak("Shutting down Sir.")
            break
        except Exception as e:
            print(f"  ⚠️  Error: {e}")
            speak("I encountered an error Sir. Please try again.")

if __name__ == "__main__":
    run()
