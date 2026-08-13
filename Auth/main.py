import os
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
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


class AuthCredentials(BaseModel):
    email: Optional[str] = None
    password: Optional[str] = None


@app.post("/auth/signup")
def signup(credentials: AuthCredentials):
    if not credentials.email or not credentials.password:
        return JSONResponse(status_code=400, content={"error": "Email and password are required"})

    try:
        result = supabase.auth.sign_up(
            {"email": credentials.email, "password": credentials.password}
        )
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})

    return JSONResponse(status_code=201, content={"user": result.user.model_dump(mode="json")})


@app.post("/auth/login")
def login(credentials: AuthCredentials):
    if not credentials.email or not credentials.password:
        return JSONResponse(status_code=400, content={"error": "Email and password are required"})

    try:
        result = supabase.auth.sign_in_with_password(
            {"email": credentials.email, "password": credentials.password}
        )
    except Exception:
        return JSONResponse(status_code=401, content={"error": "Invalid login credentials"})

    return JSONResponse(
        status_code=200,
        content={
            "access_token": result.session.access_token,
            "refresh_token": result.session.refresh_token,
        },
    )