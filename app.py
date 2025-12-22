from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from garminconnect import Garmin
import os
from datetime import date, timedelta

app = FastAPI()

# Allow Base44 + RevLuna
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https://preview-sandbox--.*\.base44\.app$|^https://.*\.base44\.app$|^https://(www\.)?revluna\.com$",
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)

# ===== MVP IN-MEMORY SESSION STORE =====
# key: user_id
# value: logged-in Garmin client
GARMIN_SESSIONS = {}

class GarminLogin(BaseModel):
    user_id: str
    email: str
    password: str

@app.get("/")
def home():
    return {"status": "ok"}

@app.get("/health")
def health():
    return {"ok": True}

# ===== CONNECT GARMIN (LOGIN ONCE) =====
@app.post("/connect-garmin")
def connect_garmin(body: GarminLogin):
    client = Garmin(body.email, body.password)
    client.login()

    GARMIN_SESSIONS[body.user_id] = client

    return {"status": "connected"}

# ===== FETCH SLEEP USING SAVED SESSION =====
@app.get("/sleep")
def sleep(user_id: str):
    client = GARMIN_SESSIONS.get(user_id)

    if not client:
        return {"error": "Garmin not connected"}

    today = date.today().isoformat()
    data = client.get_sleep_data(today)
    sleep_date = today

    # fallback if today not available yet
    if not data or not data.get("dailySleepDTO"):
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        data = client.get_sleep_data(yesterday)
        sleep_date = yesterday

    return {
        "date": sleep_date,
        "sleep": data
    }
