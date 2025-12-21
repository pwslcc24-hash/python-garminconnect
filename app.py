from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from garminconnect import Garmin
import os
from datetime import date, timedelta

app = FastAPI()

# CORS: allow Base44 preview + your Base44 production + your custom domain
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https://preview-sandbox--.*\.base44\.app$|^https://.*\.base44\.app$|^https://(www\.)?revluna\.com$",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
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
        return {"error": "Missing GARMIN_EMAIL or GARMIN_PASSWORD env vars"}

    client = Garmin(email, password)
    client.login()

    d = (date.today() - timedelta(days=1)).isoformat()
    data = client.get_sleep_data(d)

    return {"date": d, "sleep": data}

