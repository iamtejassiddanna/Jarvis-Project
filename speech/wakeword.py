import warnings
warnings.filterwarnings("ignore")

import speech_recognition as sr

def wait_for_wake_word():
    r = sr.Recognizer()
    print("\n" + "=" * 52)
    print("  👂  Say  'Hey Jarvis'  to activate...")
    print("=" * 52)
    while True:
        with sr.Microphone() as source:
            r.adjust_for_ambient_noise(source, duration=0.3)
            try:
                audio = r.listen(source, timeout=5, phrase_time_limit=3)
                text  = r.recognize_google(audio).lower()
                if "jarvis" in text:
                    print("  ✅  Wake word detected!\n")
                    return True
            except sr.WaitTimeoutError:
                pass
            except sr.UnknownValueError:
                pass
            except Exception:
                pass