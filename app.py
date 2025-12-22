from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from garminconnect import Garmin
import os
from datetime import date, timedelta

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https://preview-sandbox--.*\.base44\.app$|^https://.*\.base44\.app$|^https://(www\.)?revluna\.com$",
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/")
def home():
    return {"status": "ok"}

@app.get("/sleep")
def sleep():
    email = os.getenv("GARMIN_EMAIL")
    password = os.getenv("GARMIN_PASSWORD")

    if not email or not password:
        return {"error": "Missing GARMIN_EMAIL or GARMIN_PASSWORD"}

    client = Garmin(email, password)
    client.login()

    # Try today first
    today = date.today().isoformat()
    data = client.get_sleep_data(today)
    sleep_date = today

    # If Garmin hasn't published today yet, fall back to yesterday
    if not data or not data.get("dailySleepDTO"):
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        data = client.get_sleep_data(yesterday)
        sleep_date = yesterday

    return {
        "date": sleep_date,
        "sleep": data
    }



