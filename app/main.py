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
from app.routers import auth, patients, appointments, schedule, unavailable_periods, locations, users, prescriptions, logs, services, consultations, slots, health, templates
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
    allow_origins=["http://127.0.0.1:5501", "http://localhost:5173", "*"],
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
app.include_router(templates.router, prefix="/api/v1") # Add the new templates router
app.include_router(slots.router, prefix="/api/v1") # Add the new slots router
app.include_router(health.router, prefix="/api/v1") # Add the new health check router

# +++ META WHATSAPP WEBHOOK ENDPOINTS +++
@app.get("/webhooks/whatsapp")
async def verify_meta_webhook(request: Request):
    """
    Verify the Meta WhatsApp webhook URL.
    This endpoint is called by Meta to verify your server.
    """
    logger.info("Received Meta webhook verification request.")
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    # Import environment variables here for access
    META_WA_VERIFY_TOKEN = os.getenv("META_WA_VERIFY_TOKEN")

    if mode == "subscribe" and token == META_WA_VERIFY_TOKEN:
        logger.info("Meta webhook verification successful.")
        return Response(content=challenge, media_type="text/plain", status_code=status.HTTP_200_OK)
    else:
        logger.warning(f"Meta webhook verification failed. Mode: {mode}, Token: {token}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Verification failed")

@app.post("/webhooks/whatsapp")
async def handle_meta_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Receive incoming WhatsApp messages from Meta webhook.
    """
    logger.info("Received Meta webhook POST request.")
    try:
        body = await request.json()
        logger.debug(f"Meta Webhook Raw Body: {body}")

        # Process only 'messages' from 'changes' in the 'entry' array
        for entry in body.get("entry", []):
            for change in entry.get("changes", []):
                if change.get("field") == "messages":
                    value = change.get("value", {})
                    for message in value.get("messages", []):
                        # This is where we extract the relevant message data for our service
                        message_data = {
                            "from": message.get("from"), # Sender's WhatsApp number
                            "type": message.get("type"), # e.g., 'text', 'interactive'
                            "text": message.get("text", {}), # For 'text' messages
                            "interactive": message.get("interactive", {}), # For 'interactive' messages
                            "metadata": value.get("metadata", {}), # Contains phone_number_id
                            "timestamp": message.get("timestamp")
                        }
                        logger.info(f"Processing Meta message from: {message_data['from']}, Type: {message_data['type']}")
                        await whatsapp_service.process_incoming_message(message_data, db)

    except Exception as e:
        logger.error(f"Error processing Meta webhook: {e}", exc_info=True)
        # Meta expects a 200 OK even on internal processing errors to prevent retries
    return Response(status_code=status.HTTP_200_OK)
# +++ END META WHATSAPP WEBHOOK ENDPOINTS +++


# ==================== AUTHENTICATION (UPGRADED) ====================
@app.post("/token", include_in_schema=False)
async def token_redirect():
    return RedirectResponse(url="/api/v1/auth/token", status_code=307)

# ==================== DASHBOARD & OTHER ENDPOINTS (RESTORED) ====================
@app.get("/api/v1/dashboard/stats", response_model=schemas.DashboardStatsResponse, tags=["Dashboard"])
async def get_dashboard_stats(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return crud.get_dashboard_stats(db)

app.mount("/", StaticFiles(directory="static", html = True), name="static")