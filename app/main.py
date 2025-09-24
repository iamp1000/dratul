import os
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler as ratelimit_exceeded_handler

from sqlalchemy.orm import Session

from app import models, crud, schemas, security
from app.database import engine, get_db, SessionLocal
from app.limiter import limiter
from app.routers import auth, users, patients, appointments, locations, logs, prescriptions
from fastapi.security import OAuth2PasswordRequestForm  

# ---- Create database tables (sync engine) ----
models.Base.metadata.create_all(bind=engine)

# ---- Initialize FastAPI ----
app = FastAPI(
    title="Dr. Dhingra's Clinic Management System",
    description="Backend API for appointments, patients, schedules, and users with role-based access.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---- Middleware (single CORS) ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5501",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
    expose_headers=["Authorization"],
)

# ---- Rate limiter wiring (single place) ----
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, ratelimit_exceeded_handler)

# ---- Static files (single mount) ----
if not os.path.exists("patient_uploads"):
    os.makedirs("patient_uploads")
app.mount("/uploads", StaticFiles(directory="patient_uploads"), name="uploads")

# ---- Routers (include once each with consistent prefix) ----
app.include_router(auth.router, prefix="/api/v1", tags=["Authentication"])
app.include_router(users.router, prefix="/api/v1", tags=["Users"])
app.include_router(patients.router, prefix="/api/v1", tags=["Patients"])
app.include_router(appointments.router, prefix="/api/v1", tags=["Appointments"])
app.include_router(locations.router, prefix="/api/v1", tags=["Locations"])
app.include_router(logs.router, prefix="/api/v1", tags=["Logs"])
app.include_router(prescriptions.router, prefix="/api/v1", tags=["Prescriptions"])

# Legacy includes so frontend paths like /patients, /appointments, /locations, /users/me work
app.include_router(auth.router, include_in_schema=False)
app.include_router(users.router, include_in_schema=False)
app.include_router(patients.router, include_in_schema=False)
app.include_router(appointments.router, include_in_schema=False)
app.include_router(locations.router, include_in_schema=False)

# ---- Root and Health ----

@app.post("/token", response_model=schemas.Token, include_in_schema=False)
async def login_for_access_token(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    user = crud.get_user_by_username(db, username=form_data.username)
    if not user or not await security.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = security.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer", "user": user}

@app.get("/users/me", response_model=schemas.User)
def read_users_me(current_user: models.User = Depends(security.get_current_user)):
    return current_user

@app.get("/")
def read_root():
    return {"status": "ok"}

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy", "version": "1.0.0", "database": "connected"}

# ---- Global HTTPException handler ----
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(status_code=exc.status_code, content={"message": exc.detail, "type": "HTTP_ERROR"})

# ---- Startup: ensure initial admin users (sync DB usage) ----
@app.on_event("startup")
def on_startup():
    db = SessionLocal()
    try:
        if not crud.get_user_by_username(db, username="p1000"):
            crud.create_initial_admin_user(db, username="p1000", password="superadminpassword")
        if not crud.get_user_by_username(db, username="dratul"):
            crud.create_initial_admin_user(db, username="dratul", password="dratulpassword")
    finally:
        db.close()

# =========================
# Inline endpoints (kept)
# =========================

# Location schedules
@app.post("/locations/{location_id}/schedules", response_model=schemas.LocationSchedule)
def create_location_schedule(
    location_id: int,
    schedule: schemas.LocationScheduleCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.require_admin)
):
    schedule.location_id = location_id
    return crud.create_location_schedule(db=db, schedule=schedule)

@app.get("/locations/{location_id}/schedules", response_model=List[schemas.LocationSchedule])
def get_location_schedules(
    location_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    return crud.get_location_schedules(db=db, location_id=location_id)

@app.get("/locations/available", response_model=List[schemas.Location])
def get_available_locations(
    day_of_week: int = Query(..., ge=0, le=6),
    time_slot: str = Query(...),  # Format: "HH:MM"
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    time_obj = datetime.strptime(time_slot, "%H:%M").time()
    return crud.get_available_locations_for_time(db=db, day_of_week=day_of_week, time_slot=time_obj)

# Documents
@app.post("/documents", response_model=schemas.Document)
def upload_document(
    document: schemas.DocumentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    return crud.create_document(db=db, document=document)

@app.get("/patients/{patient_id}/documents", response_model=List[schemas.Document])
def get_patient_documents(
    patient_id: int,
    document_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    return crud.get_patient_documents(db=db, patient_id=patient_id, document_type=document_type)

# Prescription sharing
@app.post("/prescriptions/share")
def share_prescription(
    share_request: schemas.PrescriptionShare,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    document = crud.get_document(db=db, document_id=share_request.document_id)
    patient = crud.get_patient(db=db, patient_id=share_request.patient_id)

    if not document or not patient:
        raise HTTPException(status_code=404, detail="Document or patient not found")

    if share_request.method == "email":
        result = {"success": True, "message": "Email sent successfully"}
    elif share_request.method == "whatsapp":
        result = {"success": True, "message": "WhatsApp sent successfully"}
    else:
        raise HTTPException(status_code=400, detail="Unsupported share method")

    crud.create_activity_log(
        db=db,
        user_id=current_user.id,
        action="Prescription Shared",
        details=f"Shared prescription for {patient.name} via {share_request.method}",
        category="Prescription"
    )
    return result

# Remarks
@app.post("/patients/{patient_id}/remarks", response_model=schemas.Remark)
def create_patient_remark(
    patient_id: int,
    remark: schemas.RemarkCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    remark.patient_id = patient_id
    return crud.create_remark(db=db, remark=remark, author_id=current_user.id)

@app.get("/patients/{patient_id}/remarks", response_model=List[schemas.Remark])
def get_patient_remarks(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    return crud.get_patient_remarks(db=db, patient_id=patient_id)

# Logs (with category filter)
@app.get("/logs", response_model=List[schemas.ActivityLog])
def get_activity_logs(
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.require_admin)
):
    return crud.get_activity_logs_by_category(db=db, category=category, skip=skip, limit=limit)

# Appointments: reschedule
@app.put("/appointments/{appointment_id}/reschedule")
def reschedule_appointment(
    appointment_id: int,
    reschedule_data: schemas.AppointmentReschedule,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    appointment = crud.reschedule_appointment(
        db=db,
        appointment_id=appointment_id,
        new_start=reschedule_data.new_start_time,
        new_end=reschedule_data.new_end_time
    )
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    crud.create_activity_log(
        db=db,
        user_id=current_user.id,
        action="Appointment Rescheduled",
        details=f"Rescheduled appointment for {appointment.patient.name}",
        category="Appointment"
    )
    return {"success": True, "message": "Appointment rescheduled successfully"}

# Appointments: cancel
@app.put("/appointments/{appointment_id}/cancel")
def cancel_appointment(
    appointment_id: int,
    reason: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    appointment = crud.cancel_appointment(db=db, appointment_id=appointment_id, reason=reason)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    crud.create_activity_log(
        db=db,
        user_id=current_user.id,
        action="Appointment Cancelled",
        details=f"Cancelled appointment for {appointment.patient.name}. Reason: {reason or 'None provided'}",
        category="Appointment"
    )
    return {"success": True, "message": "Appointment cancelled successfully"}
