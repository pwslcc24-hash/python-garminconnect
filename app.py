from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from garminconnect import Garmin
import os
from datetime import date, timedelta

app = FastAPI()

# ✅ CORS: allow Base44 preview + Base44 prod + RevLuna domain
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

    sleep_date = (date.today() - timedelta(days=1)).isoformat()
    data = client.get_sleep_data(sleep_date)

    return {
        "date": sleep_date,
        "sleep": data
    }


