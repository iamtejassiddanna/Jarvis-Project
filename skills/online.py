import warnings
warnings.filterwarnings("ignore")

import requests
import wikipedia
import pywhatkit as kit
from decouple import config

NEWS_API_KEY       = config("NEWS_API_KEY")
OPENWEATHER_APP_ID = config("OPENWEATHER_APP_ID")

def get_weather(city="Bangalore") -> str:
    try:
        res = requests.get(
            f"http://api.openweathermap.org/data/2.5/weather"
            f"?q={city}&appid={OPENWEATHER_APP_ID}&units=metric"
        ).json()
        desc  = res["weather"][0]["description"]
        temp  = round(res["main"]["temp"])
        feels = round(res["main"]["feels_like"])
        humid = res["main"]["humidity"]
        return (f"The weather in {city} is {desc}. "
                f"Temperature is {temp} degrees, feels like {feels} degrees, "
                f"with {humid} percent humidity Sir.")
    except:
        return "I could not fetch the weather right now Sir."

def get_news() -> list:
    try:
        res = requests.get(
            f"https://newsapi.org/v2/top-headlines"
            f"?country=in&apiKey={NEWS_API_KEY}&category=general"
        ).json()
        return [a["title"] for a in res.get("articles", [])[:5]]
    except:
        return ["I could not fetch the news right now Sir."]

def get_ip() -> str:
    try:
        return requests.get(
            "https://api64.ipify.org?format=json").json()["ip"]
    except:
        return "unavailable"

def get_joke() -> str:
    try:
        return requests.get(
            "https://icanhazdadjoke.com/",
            headers={"Accept": "application/json"}
        ).json()["joke"]
    except:
        return "Why did the AI go to therapy? Too many deep issues Sir."

def search_wikipedia(query: str) -> str:
    try:
        return wikipedia.summary(query, sentences=2)
    except:
        return f"I could not find information about {query} Sir."

def play_youtube(query: str):
    try:
        kit.playonyt(query)
    except:
        pass

def search_google(query: str):
    try:
        kit.search(query)
    except:
        pass