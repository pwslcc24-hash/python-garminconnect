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

# ===== IN-MEMORY SESSION STORE =====
# key: Base44 user_id
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

# ===== CONNECT GARMIN =====
@app.post("/connect-garmin")
def connect_garmin(body: GarminLogin):
    try:
        client = Garmin(body.email, body.password)
        client.login()
        GARMIN_SESSIONS[body.user_id] = client
        return {"status": "connected"}
    except Exception:
        return {"error": "Garmin login failed"}

# ===== GARMIN STATUS =====
@app.get("/garmin-status")
def garmin_status(user_id: str):
    return {"connected": user_id in GARMIN_SESSIONS}

# ===== DISCONNECT GARMIN =====
@app.post("/disconnect-garmin")
def disconnect_garmin(user_id: str):
    GARMIN_SESSIONS.pop(user_id, None)
    return {"status": "disconnected"}

# ===== HELPER: CHECK IF SLEEP IS REAL =====
def has_real_sleep(data: dict) -> bool:
    dto = data.get("dailySleepDTO") if data else None
    if not dto:
        return False

    return any([
        dto.get("sleepTimeSeconds"),
        dto.get("sleepStartTimestampGMT"),
        dto.get("sleepEndTimestampGMT"),
        dto.get("deepSleepSeconds"),
        dto.get("lightSleepSeconds"),
        dto.get("remSleepSeconds"),
        dto.get("awakeSleepSeconds"),
    ])

# ===== SYNC SLEEP (NEWEST VALID ONLY) =====
@app.get("/sleep")
def sleep(user_id: str):
    client = GARMIN_SESSIONS.get(user_id)

    if not client:
        return {"error": "Garmin not connected"}

    # Look back up to 7 days and return newest REAL sleep
    for days_back in range(0, 7):
        check_date = (date.today() - timedelta(days=days_back)).isoformat()
        data = client.get_sleep_data(check_date)

        if has_real_sleep(data):
            return {
                "date": check_date,
                "sleep": data
            }

    return {
        "error": "No valid Garmin sleep data found"
    }

