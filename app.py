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

# ===== IN-MEMORY GARMIN SESSIONS =====
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
    except Exception as e:
        return {"error": "Garmin login failed", "detail": str(e)}

# ===== GARMIN STATUS =====
@app.get("/garmin-status")
def garmin_status(user_id: str):
    return {"connected": user_id in GARMIN_SESSIONS}

# ===== DISCONNECT GARMIN =====
@app.post("/disconnect-garmin")
def disconnect_garmin(user_id: str):
    GARMIN_SESSIONS.pop(user_id, None)
    return {"status": "disconnected"}

# ===== SLEEP (NEWEST REAL) =====
@app.get("/sleep")
def sleep(user_id: str):
    client = GARMIN_SESSIONS.get(user_id)
    if not client:
        return {"error": "Garmin not connected"}

    for days_back in range(0, 7):
        check_date = (date.today() - timedelta(days=days_back)).isoformat()
        try:
            data = client.get_sleep_data(check_date)
        except Exception as e:
            continue

        dto = data.get("dailySleepDTO") if data else None
        if dto and dto.get("sleepTimeSeconds"):
            return {"date": check_date, "sleep": data}

    return {"error": "No sleep found"}

# ===== HRV (TODAY) =====
@app.get("/hrv")
def hrv(user_id: str):
    client = GARMIN_SESSIONS.get(user_id)
    if not client:
        return {"error": "Garmin not connected"}

    day = date.today().isoformat()

    # Try likely HRV method names across garminconnect versions
    method_names = [
        "get_hrv_data",
        "get_hrv",
        "get_daily_hrv",
        "get_hrv_summary",
        "get_hrv_status",
        "get_wellness_hrv",
    ]

    last_error = None

    for name in method_names:
        fn = getattr(client, name, None)
        if not fn:
            continue
        try:
            # Most versions take a date string like "2025-12-23"
            return {"date": day, "hrv": fn(day), "method_used": name}
        except TypeError:
            # Some versions take no args
            try:
                return {"date": day, "hrv": fn(), "method_used": name}
            except Exception as e:
                last_error = str(e)
        except Exception as e:
            last_error = str(e)

    # If none worked, show what exists so you can see the right one
    available = [n for n in dir(client) if "hrv" in n.lower() or "wellness" in n.lower()]
    available.sort()

    return {
        "error": "No HRV method worked in this garminconnect version",
        "date": day,
        "available_hrv_related_methods": available,
        "last_error": last_error,
    }



