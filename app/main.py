from dotenv import load_dotenv
load_dotenv()

import os
import uvicorn
from datetime import datetime, timezone, timedelta, date
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, Request, status, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

# Import our modules
from app import models, schemas, crud
from app.database import get_db, create_tables
from app.hash_password import create_or_update_admin
from app.routers import auth, patients, appointments, schedule, unavailable_periods, locations, users, prescriptions
from app.security import (
    verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES,
    get_current_user, require_admin
)

app = FastAPI(title="Dr. Dhingra's Clinic Management System")

# Lifespan for startup events
@app.on_event("startup")
def on_startup():
    create_tables()
    create_or_update_admin()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(patients.router, prefix="/api/v1")
app.include_router(appointments.router, prefix="/api/v1")
app.include_router(schedule.router, prefix="/api/v1")
app.include_router(unavailable_periods.router, prefix="/api/v1")
app.include_router(locations.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(prescriptions.router, prefix="/api/v1")


# ==================== AUTHENTICATION (UPGRADED) ====================
@app.post("/token", include_in_schema=False)
async def token_redirect():
    return RedirectResponse(url="/api/v1/auth/token", status_code=307)

# ==================== DASHBOARD & OTHER ENDPOINTS (RESTORED) ====================
@app.get("/api/v1/dashboard/stats", response_model=schemas.DashboardStatsResponse, tags=["Dashboard"])
async def get_dashboard_stats(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return crud.get_dashboard_stats(db)

app.mount("/", StaticFiles(directory="static", html = True), name="static")