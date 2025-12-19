from fastapi import FastAPI, Header, HTTPException
from garminconnect import Garmin
import os
from datetime import date, timedelta

app = FastAPI()

API_KEY = os.getenv("SYNC_API_KEY", "")

@app.get("/")
def home():
    return {"ok": True}

@app.post("/sync/sleep")
def sync_sleep(x_api_key: str | None = Header(default=None)):
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Bad API key")

    api = Garmin(os.getenv("GARMIN_EMAIL"), os.getenv("GARMIN_PASSWORD"))
    api.login()

    d = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    sleep = api.get_sleep_data(d)

    # For now: just return the data so we know it works.
    # Next step we will save it into your RevLuna database.
    return {"date": d, "sleep": sleep}
