import os
import uvicorn
import logging
import sys
from datetime import datetime, timezone, timedelta, date
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, Request, status, Form, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

# Import our modules
from app import models, schemas, crud
from app.database import get_db, create_tables, drop_tables # Explicitly import drop_tables for internal use
from app.hash_password import create_or_update_admin, create_initial_data
from app.routers import auth, patients, appointments, schedule, unavailable_periods, locations, users, prescriptions, logs, services, consultations, slots
from app.services.whatsapp_service import whatsapp_service # Import the WhatsApp service instance
# --- Logging Configuration --- START ---
# Configure root logger to output DEBUG messages to console
logging.basicConfig(level=logging.DEBUG,
                    stream=sys.stdout, # Explicitly direct to stdout
                    format='%(levelname)-8s %(name)s: %(message)s')

logger = logging.getLogger(__name__)
# Optional: Set level for specific libraries if too noisy
# logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
# logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
# --- Logging Configuration --- END ---

from app.security import (
    verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES,
    get_current_user, require_admin
)

app = FastAPI(title="Dr. Dhingra's Clinic Management System")

# Lifespan for startup events
@app.on_event("startup")
def on_startup():
    create_tables()
    create_initial_data()
    create_or_update_admin()

app.add_middleware(
    CORSMiddleware,
    # REFACTORED: Be explicit about the front-end origin (http://127.0.0.1:5501) and localhost for robust local development.
    # We also keep "*" in the original list for simplicity if other origins were intended.
    allow_origins=["http://127.0.0.1:5501", "http://localhost:5501", "*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
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
app.include_router(logs.router, prefix="/api/v1")
app.include_router(services.router, prefix="/api/v1")
app.include_router(consultations.router, prefix="/api/v1") # Add the new consultations router
app.include_router(slots.router, prefix="/api/v1") # Add the new slots router

# +++ NEW TWILIO WEBHOOK ENDPOINT +++
@app.post("/webhooks/twilio", status_code=status.HTTP_204_NO_CONTENT)
async def handle_twilio_webhook(
    From: str = Form(...), # Sender's WhatsApp number (e.g., whatsapp:+1...)
    Body: str = Form(...), # Message text
    # Twilio sends many other fields, but From and Body are essential
    db: Session = Depends(get_db)
):
    """
    Receive incoming WhatsApp messages from Twilio webhook.
    """
    logger.info(f"Received Twilio webhook message from: {From}, Body: {Body}")
    # Construct a simplified message_data dictionary for process_incoming_message
    phone_number_without_prefix = From.split(':')[-1] # Get number part after 'whatsapp:'
    message_data = {
        "from": phone_number_without_prefix, 
        "type": "text", # Assume text for simplicity from Twilio's basic webhook
        "text": {"body": Body}
    }
    try:
        # Process the message using the existing service function
        await whatsapp_service.process_incoming_message(message_data, db)
    except Exception as e:
        # Log errors but still return 2xx to Twilio to prevent retries for processing errors
        logger.error(f"Error processing Twilio webhook for {From}: {e}", exc_info=True)
        # Optionally, you could send an error message back via WhatsApp API here if needed
    
    # Return No Content to acknowledge receipt to Twilio
    return Response(status_code=status.HTTP_204_NO_CONTENT)
# +++ END NEW ENDPOINT +++


# ==================== AUTHENTICATION (UPGRADED) ====================
@app.post("/token", include_in_schema=False)
async def token_redirect():
    return RedirectResponse(url="/api/v1/auth/token", status_code=307)

# ==================== DASHBOARD & OTHER ENDPOINTS (RESTORED) ====================
@app.get("/api/v1/dashboard/stats", response_model=schemas.DashboardStatsResponse, tags=["Dashboard"])
async def get_dashboard_stats(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return crud.get_dashboard_stats(db)

app.mount("/", StaticFiles(directory="static", html = True), name="static")