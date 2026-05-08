import warnings
warnings.filterwarnings("ignore")

import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import tempfile, os
from datetime import datetime
from faster_whisper import WhisperModel

# Use base.en for much faster CPU inference
model = WhisperModel("base.en", device="cpu", compute_type="int8")

def listen(duration=5, sample_rate=16000) -> str:
    print("  🎙️  Listening...")
    audio = sd.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype='float32'
    )
    sd.wait()
    print("  🔄  Processing...")
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        wav.write(f.name, sample_rate,
                  (audio * 32767).astype(np.int16))
        
        segments, info = model.transcribe(f.name, vad_filter=True)
        text = " ".join([segment.text for segment in segments]).strip()
        os.unlink(f.name)
        
    if text:
        time_now = datetime.now().strftime("%H:%M:%S")
        print("\n" + "─" * 52)
        print(f"  🧑  YOU  [{time_now}]")
        print("─" * 52)
        print(f"  {text}")
        print("─" * 52)
    return text
