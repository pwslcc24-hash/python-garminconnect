from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from garminconnect import Garmin
from datetime import date, timedelta

app = FastAPI()

# ===== CORS =====
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https://preview-sandbox--.*\.base44\.app$|^https://.*\.base44\.app$|^https://(www\.)?revluna\.com$",
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)

# ===== MVP IN-MEMORY SESSION STORE =====
# key: user_id (from Base44)
# value: logged-in Garmin client
GARMIN_SESSIONS = {}

# ===== MODELS =====
class GarminLogin(BaseModel):
    user_id: str
    email: str
    password: str

# ===== BASIC ROUTES =====
@app.get("/")
def home():
    return {"status": "ok"}

@app.get("/health")
def health():
    return {"ok": True}

# ===== CONNECT GARMIN (LOGIN ONCE) =====
@app.post("/connect-garmin")
def connect_garmin(body: GarminLogin):
    try:
        client = Garmin(body.email, body.password)
        client.login()
        GARMIN_SESSIONS[body.user_id] = client
        return {"status": "connected"}
    except Exception as e:
        return {"error": "Garmin login failed"}

# ===== GARMIN CONNECTION STATUS =====
@app.get("/garmin-status")
def garmin_status(user_id: str):
    return {"connected": user_id in GARMIN_SESSIONS}

# ===== DISCONNECT GARMIN =====
@app.post("/disconnect-garmin")
def disconnect_garmin(user_id: str):
    if user_id in GARMIN_SESSIONS:
        del GARMIN_SESSIONS[user_id]
    return {"status": "disconnected"}

# ===== SYNC SLEEP =====
@app.get("/sleep")
def sleep(user_id: str):
    client = GARMIN_SESSIONS.get(user_id)

    if not client:
        return {"error": "Garmin not connected"}

    # Try today first
    today = date.today().isoformat()
    data = client.get_sleep_data(today)
    sleep_date = today

    # Fallback to yesterday if Garmin hasn't published today yet
    if not data or not data.get("dailySleepDTO"):
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        data = client.get_sleep_data(yesterday)
        sleep_date = yesterday

    return {
        "date": sleep_date,
        "sleep": data
    }
