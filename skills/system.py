import subprocess
from datetime import datetime

def get_time() -> str:
    return datetime.now().strftime("%I:%M %p")

def get_date() -> str:
    return datetime.now().strftime("%A, %B %d, %Y")

def open_camera():
    subprocess.run(["open", "-a", "Photo Booth"])

def open_calculator():
    subprocess.run(["open", "-a", "Calculator"])
