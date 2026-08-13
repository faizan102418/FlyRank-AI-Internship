import os
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import JSONResponse, Response
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


@app.get("/public/info")
def public_info():
    return JSONResponse(
        status_code=200,
        content={"message": "Welcome stranger! This info is public."},
    )


def get_current_user(request: Request) -> dict:
    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Access token required")

    token = auth_header.removeprefix("Bearer ").strip()

    if not token:
        raise HTTPException(status_code=401, detail="Access token required")

    try:
        result = supabase.auth.get_user(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    if not result or not result.user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return {"user": result.user, "token": token}


@app.get("/protected/profile")
def protected_profile(current=Depends(get_current_user)):
    user = current["user"]
    return JSONResponse(
        status_code=200,
        content={
            "id": user.id,
            "email": user.email,
            "created_at": user.created_at.isoformat() if hasattr(user.created_at, "isoformat") else str(user.created_at),
        },
    )


@app.get("/protected/dashboard")
def protected_dashboard(current=Depends(get_current_user)):
    user = current["user"]
    return JSONResponse(
        status_code=200,
        content={"message": f"Welcome to your dashboard, {user.email}"},
    )


@app.post("/auth/logout")
def logout(current=Depends(get_current_user)):
    try:
        supabase.auth.sign_out()
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})

    return Response(status_code=204)