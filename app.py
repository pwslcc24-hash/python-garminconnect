from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from garminconnect import Garmin
import os
from datetime import date, timedelta

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://rev-luna-copy-ab1f5d2f.base44.app"
    ],
    allow_credentials=True,
    allow_methods=["GET"],
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

    client = Garmin(email, password)
    client.login()

    d = (date.today() - timedelta(days=1)).isoformat()
    data = client.get_sleep_data(d)

    return {"date": d, "sleep": data}
