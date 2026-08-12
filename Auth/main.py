import os

from dotenv import load_dotenv
from fastapi import FastAPI
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI(title="FlyRank Auth API")


@app.on_event("startup")
def on_startup() -> None:
    print(f"Server running and connected to Supabase at {SUPABASE_URL}")


@app.get("/")
def root():
    return {"status": "ok"}