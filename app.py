from fastapi import FastAPI
from garminconnect import Garmin
import os
from datetime import date, timedelta

app = FastAPI()
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

    client = Garmin(email, password)
    client.login()

    d = (date.today() - timedelta(days=1)).isoformat()
    data = client.get_sleep_data(d)

    return {"date": d, "sleep": data}
