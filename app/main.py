
import os
import uvicorn
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, Depends, HTTPException, Request, Response, status
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

# Import our enhanced modules
from app import models, schemas
from app.database import engine, get_db, SessionLocal
from app.security import (
    SecurityConfig, audit_logger, rate_limiter, session_manager,
    mfa_service, get_current_user, require_admin, require_staff,
    require_medical_staff, require_permission, Permissions,
    add_security_headers, verify_password, get_password_hash,
    create_access_token, create_refresh_token, create_mfa_token,
    verify_token, validate_password_strength
)
from app.services.whatsapp_service import WhatsAppService
from app.services.email_service import EmailService
from app.services.calendar_service import GoogleCalendarService
from app.crud import enhanced_crud as crud

# Create database tables
models.Base.metadata.create_all(bind=engine)

# Initialize FastAPI with security configuration
app = FastAPI(
    title="Dr. Dhingra's Clinic Management System",
    description="HIPAA-Compliant Healthcare Management System with Advanced Security",
    version="2.0.0",
    docs_url="/docs" if os.getenv("ENVIRONMENT") == "development" else None,
    redoc_url="/redoc" if os.getenv("ENVIRONMENT") == "development" else None,
    openapi_url="/openapi.json" if os.getenv("ENVIRONMENT") == "development" else None
)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["localhost", "127.0.0.1", "*.clinic.local"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5501",
        "https://clinic.local"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
    expose_headers=["Authorization"],
)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Static files with security
if not os.path.exists("static"):
    os.makedirs("static")
if not os.path.exists("uploads"):
    os.makedirs("uploads")

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Services
whatsapp_service = WhatsAppService()
email_service = EmailService()
calendar_service = GoogleCalendarService()

# Middleware for security headers and audit logging
@app.middleware("http")
async def security_middleware(request: Request, call_next):
    """Add security headers and audit logging"""
    start_time = datetime.now()

    # Log request
    audit_logger.log_access(
        user_id=None,
        action="HTTP_REQUEST",
        resource=request.url.path,
        ip_address=request.client.host,
        user_agent=request.headers.get("User-Agent"),
        details=f"{request.method} {request.url.path}"
    )

    response = await call_next(request)

    # Add security headers
    response = add_security_headers(response)

    # Log response time
    process_time = (datetime.now() - start_time).total_seconds()
    response.headers["X-Process-Time"] = str(process_time)

    return response

# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with proper logging"""
    audit_logger.log_access(
        user_id=None,
        action="HTTP_ERROR",
        resource=request.url.path,
        ip_address=request.client.host,
        success=False,
        details=f"HTTP {exc.status_code}: {exc.detail}"
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": exc.detail}
    )

@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    """Handle database exceptions"""
    audit_logger.log_access(
        user_id=None,
        action="DATABASE_ERROR",
        resource=request.url.path,
        ip_address=request.client.host,
        success=False,
        details=f"Database error: {str(exc)}"
    )

    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "Database error occurred"}
    )

# Health check endpoint
@app.get("/health", tags=["System"], response_model=schemas.HealthCheck)
@limiter.limit("10/minute")
async def health_check(request: Request):
    """Health check endpoint for monitoring"""
    try:
        # Check database connection
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    services = {
        "database": db_status,
        "whatsapp": "enabled" if whatsapp_service.enabled else "disabled",
        "email": "enabled" if email_service.enabled else "disabled",
        "calendar": "enabled" if calendar_service.enabled else "disabled"
    }

    return schemas.HealthCheck(
        timestamp=datetime.now(timezone.utc),
        services=services
    )

# --- Authentication Endpoints ---
@app.post("/api/v1/auth/token", response_model=schemas.Token, tags=["Authentication"])
@limiter.limit("5/minute")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Authenticate user and return access token"""
    client_ip = request.client.host

    # Get user
    user = crud.get_user_by_username(db, username=form_data.username)
    if not user:
        audit_logger.log_access(
            user_id=None,
            action="LOGIN",
            resource="authentication",
            ip_address=client_ip,
            success=False,
            details=f"User not found: {form_data.username}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if account is locked
    if user.account_locked_until and user.account_locked_until > datetime.now(timezone.utc):
        audit_logger.log_access(
            user_id=user.id,
            action="LOGIN",
            resource="authentication",
            ip_address=client_ip,
            success=False,
            details="Account locked"
        )
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Account is temporarily locked due to multiple failed login attempts"
        )

    # Verify password
    if not verify_password(form_data.password, user.password_hash):
        # Increment failed login attempts
        crud.increment_login_attempts(db, user.id)

        audit_logger.log_access(
            user_id=user.id,
            action="LOGIN",
            resource="authentication",
            ip_address=client_ip,
            success=False,
            details="Invalid password"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        audit_logger.log_access(
            user_id=user.id,
            action="LOGIN",
            resource="authentication",
            ip_address=client_ip,
            success=False,
            details="Account inactive"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )

    # Check if MFA is required
    if user.mfa_enabled or (user.role == "admin" and SecurityConfig.MFA_REQUIRED_FOR_ADMIN):
        if not user.mfa_secret:
            # User needs to set up MFA
            mfa_token = create_mfa_token(user.id)
            return JSONResponse(
                status_code=202,
                content={
                    "mfa_setup_required": True,
                    "mfa_token": mfa_token
                }
            )
        else:
            # User needs to provide MFA code
            mfa_token = create_mfa_token(user.id)
            return JSONResponse(
                status_code=202,
                content={
                    "mfa_required": True,
                    "mfa_token": mfa_token
                }
            )

    # Successful login
    crud.reset_login_attempts(db, user.id)
    crud.update_last_login(db, user.id)

    # Create tokens
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id, "role": user.role.value}
    )
    refresh_token = create_refresh_token(
        data={"sub": user.username, "user_id": user.id}
    )

    # Create session
    session_id = session_manager.create_session(
        user_id=user.id,
        user_data={"username": user.username, "role": user.role.value},
        ip_address=client_ip
    )

    audit_logger.log_access(
        user_id=user.id,
        action="LOGIN",
        resource="authentication",
        ip_address=client_ip,
        success=True,
        details="Successful login"
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": SecurityConfig.SESSION_TIMEOUT_MINUTES * 60,
        "refresh_token": refresh_token,
        "user": user
    }

@app.post("/api/v1/auth/mfa/setup", tags=["Authentication"])
@limiter.limit("3/minute")
async def setup_mfa(
    request: Request,
    mfa_token: str,
    db: Session = Depends(get_db)
):
    """Set up Multi-Factor Authentication"""
    payload = verify_token(mfa_token, "mfa")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid MFA token"
        )

    user_id = payload.get("user_id")
    user = crud.get_user_by_id(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Generate MFA secret and QR code
    secret, qr_code, backup_codes = mfa_service.generate_secret(user.username)

    # Store encrypted secret
    crud.update_user_mfa_secret(db, user.id, secret)

    audit_logger.log_access(
        user_id=user.id,
        action="MFA_SETUP",
        resource="authentication",
        ip_address=request.client.host,
        success=True
    )

    return {
        "secret": secret,
        "qr_code": qr_code,
        "backup_codes": backup_codes
    }

@app.post("/api/v1/auth/mfa/verify", response_model=schemas.Token, tags=["Authentication"])
@limiter.limit("5/minute")
async def verify_mfa(
    request: Request,
    mfa_token: str,
    mfa_code: str,
    db: Session = Depends(get_db)
):
    """Verify MFA code and complete authentication"""
    payload = verify_token(mfa_token, "mfa")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid MFA token"
        )

    user_id = payload.get("user_id")
    user = crud.get_user_by_id(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Verify MFA code
    if not mfa_service.verify_totp(user.mfa_secret, mfa_code):
        audit_logger.log_access(
            user_id=user.id,
            action="MFA_VERIFY",
            resource="authentication",
            ip_address=request.client.host,
            success=False,
            details="Invalid MFA code"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid MFA code"
        )

    # Enable MFA if not already enabled
    if not user.mfa_enabled:
        crud.enable_user_mfa(db, user.id)

    # Create tokens
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id, "role": user.role.value}
    )

    audit_logger.log_access(
        user_id=user.id,
        action="MFA_VERIFY",
        resource="authentication",
        ip_address=request.client.host,
        success=True
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": SecurityConfig.SESSION_TIMEOUT_MINUTES * 60,
        "user": user
    }

@app.post("/api/v1/auth/logout", tags=["Authentication"])
async def logout(
    request: Request,
    current_user: models.User = Depends(get_current_user)
):
    """Logout user and invalidate session"""
    # In a full implementation, we would blacklist the JWT token
    # For now, we just log the logout event

    audit_logger.log_access(
        user_id=current_user.id,
        action="LOGOUT",
        resource="authentication",
        ip_address=request.client.host,
        success=True
    )

    return {"message": "Successfully logged out"}

# --- User Management Endpoints ---
@app.get("/api/v1/users/me", response_model=schemas.User, tags=["Users"])
async def get_current_user_info(
    current_user: models.User = Depends(get_current_user)
):
    """Get current user information"""
    return current_user

@app.get("/api/v1/users", response_model=List[schemas.User], tags=["Users"])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_permission(Permissions.USER_READ))
):
    """List all users (admin only)"""
    users = crud.get_users(db, skip=skip, limit=limit)
    return users

@app.post("/api/v1/users", response_model=schemas.User, tags=["Users"])
async def create_user(
    user: schemas.UserCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_permission(Permissions.USER_WRITE))
):
    """Create new user (admin only)"""
    # Validate password strength
    password_checks = validate_password_strength(user.password)
    if not all(password_checks.values()):
        failed_checks = [k for k, v in password_checks.items() if not v]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password does not meet requirements: {', '.join(failed_checks)}"
        )

    # Check if username already exists
    if crud.get_user_by_username(db, username=user.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Check if email already exists
    if user.email and crud.get_user_by_email(db, email=user.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create user
    created_user = crud.create_user(db=db, user=user, created_by=current_user.id)

    audit_logger.log_access(
        user_id=current_user.id,
        action="CREATE",
        resource="user",
        resource_id=str(created_user.id),
        success=True,
        details=f"Created user: {user.username}"
    )

    return created_user

@app.put("/api/v1/users/{user_id}", response_model=schemas.User, tags=["Users"])
async def update_user(
    user_id: int,
    user_update: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_permission(Permissions.USER_WRITE))
):
    """Update user information (admin only)"""
    user = crud.get_user_by_id(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    updated_user = crud.update_user(db=db, user_id=user_id, user_update=user_update)

    audit_logger.log_access(
        user_id=current_user.id,
        action="UPDATE",
        resource="user",
        resource_id=str(user_id),
        success=True,
        details=f"Updated user: {user.username}"
    )

    return updated_user

# --- Patient Management Endpoints ---
@app.get("/api/v1/patients", response_model=List[schemas.Patient], tags=["Patients"])
async def list_patients(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_permission(Permissions.PATIENT_READ))
):
    """List patients with optional search"""
    patients = crud.get_patients(db, skip=skip, limit=limit, search=search)

    # Log patient access for HIPAA compliance
    for patient in patients:
        audit_logger.log_access(
            user_id=current_user.id,
            action="READ",
            resource="patient",
            resource_id=str(patient.id),
            patient_id=patient.id,
            success=True
        )

    return patients

@app.get("/api/v1/patients/{patient_id}", response_model=schemas.Patient, tags=["Patients"])
async def get_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_permission(Permissions.PATIENT_READ))
):
    """Get patient by ID"""
    patient = crud.get_patient(db, patient_id=patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )

    # Log patient access for HIPAA compliance
    audit_logger.log_access(
        user_id=current_user.id,
        action="READ",
        resource="patient",
        resource_id=str(patient_id),
        patient_id=patient_id,
        success=True
    )

    return patient

@app.post("/api/v1/patients", response_model=schemas.Patient, tags=["Patients"])
async def create_patient(
    patient: schemas.PatientCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_permission(Permissions.PATIENT_WRITE))
):
    """Create new patient"""
    # Check for duplicate phone number
    existing_patient = crud.get_patient_by_phone(db, phone_number=patient.phone_number)
    if existing_patient:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Patient with this phone number already exists"
        )

    # Check for duplicate email if provided
    if patient.email:
        existing_patient = crud.get_patient_by_email(db, email=patient.email)
        if existing_patient:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Patient with this email already exists"
            )

    created_patient = crud.create_patient(db=db, patient=patient, created_by=current_user.id)

    audit_logger.log_access(
        user_id=current_user.id,
        action="CREATE",
        resource="patient",
        resource_id=str(created_patient.id),
        patient_id=created_patient.id,
        success=True,
        details=f"Created patient: {patient.name}"
    )

    return created_patient

# --- Appointment Management Endpoints ---
@app.get("/api/v1/appointments", response_model=List[schemas.AppointmentWithDetails], tags=["Appointments"])
async def list_appointments(
    skip: int = 0,
    limit: int = 100,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    status: Optional[str] = None,
    location_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_permission(Permissions.APPOINTMENT_READ))
):
    """List appointments with filtering options"""
    appointments = crud.get_appointments(
        db, skip=skip, limit=limit,
        date_from=date_from, date_to=date_to,
        status=status, location_id=location_id
    )

    return appointments

@app.post("/api/v1/appointments", response_model=schemas.Appointment, tags=["Appointments"])
async def create_appointment(
    appointment: schemas.AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_permission(Permissions.APPOINTMENT_WRITE))
):
    """Create new appointment"""
    # Check if patient exists
    patient = crud.get_patient(db, patient_id=appointment.patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )

    # Check if location exists
    location = crud.get_location(db, location_id=appointment.location_id)
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found"
        )

    # Check for scheduling conflicts
    conflicts = crud.check_appointment_conflicts(
        db, location_id=appointment.location_id,
        start_time=appointment.start_time,
        end_time=appointment.end_time
    )
    if conflicts:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Time slot is already booked"
        )

    created_appointment = crud.create_appointment(
        db=db, appointment=appointment, created_by=current_user.id
    )

    # Send confirmation if patient has opted in for communications
    if patient.whatsapp_opt_in and patient.preferred_communication == "whatsapp":
        try:
            await whatsapp_service.send_appointment_confirmation(
                phone_number=patient.whatsapp_number,
                patient_name=patient.name,
                appointment_time=appointment.start_time,
                location=location.name
            )
            crud.mark_appointment_confirmation_sent(db, created_appointment.id)
        except Exception as e:
            # Log error but don't fail the appointment creation
            audit_logger.log_access(
                user_id=current_user.id,
                action="COMMUNICATION_ERROR",
                resource="appointment",
                resource_id=str(created_appointment.id),
                success=False,
                details=f"Failed to send WhatsApp confirmation: {str(e)}"
            )

    audit_logger.log_access(
        user_id=current_user.id,
        action="CREATE",
        resource="appointment",
        resource_id=str(created_appointment.id),
        patient_id=appointment.patient_id,
        success=True
    )

    return created_appointment

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    # Create initial admin users
    db = SessionLocal()
    try:
        if not crud.get_user_by_username(db, username="admin"):
            admin_user = schemas.UserCreate(
                username="admin",
                email="admin@clinic.local",
                role="admin",
                password="AdminPassword123!"
            )
            crud.create_initial_admin(db, admin_user)

        audit_logger.log_access(
            user_id=None,
            action="SYSTEM_STARTUP",
            resource="system",
            success=True,
            details="Application started successfully"
        )
    finally:
        db.close()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=os.getenv("ENVIRONMENT") == "development",
        ssl_keyfile=os.getenv("SSL_KEY_FILE"),
        ssl_certfile=os.getenv("SSL_CERT_FILE")
    )
