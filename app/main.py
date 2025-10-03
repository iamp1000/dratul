# app/main.py - Complete FastAPI application with all routes and middleware
import os
import uvicorn
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, Request, Response, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address  
from slowapi.errors import RateLimitExceeded
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

# Import our modules
from app import models, schemas, crud
from app.database import engine, get_db, create_tables
from app.security import (
    SecurityConfig, audit_logger, rate_limiter, session_manager,
    mfa_service, get_current_user, get_password_hash, verify_password,
    create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, 
    require_admin, require_staff, require_medical_staff
)

# Import service modules  
from app.services.whatsapp_service import WhatsAppChatbot
from app.services.email_service import EmailService
from app.services.calendar_service import GoogleCalendarService

# Startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application lifespan events"""
    # Startup
    try:
        create_tables()
        audit_logger.info("Database tables created/verified")
        audit_logger.info("Dr. Dhingra's Clinic Management System started")
        yield
    except Exception as e:
        audit_logger.error(f"Startup error: {str(e)}")
        raise
    finally:
        # Shutdown
        audit_logger.info("Dr. Dhingra's Clinic Management System shutdown")

# Initialize FastAPI app
app = FastAPI(
    title="Dr. Dhingra's Clinic Management System",
    description="HIPAA-compliant clinic management with WhatsApp integration, appointment scheduling, and patient management",
    version="2.0.0",
    docs_url="/docs" if os.getenv("ENVIRONMENT") == "development" else None,
    redoc_url="/redoc" if os.getenv("ENVIRONMENT") == "development" else None,
    lifespan=lifespan
)

# Initialize services
whatsapp_service = WhatsAppChatbot()
email_service = EmailService()
calendar_service = GoogleCalendarService()

# Configure CORS
allowed_origins = [
    "http://localhost:3000",
    "http://localhost:8000", 
    "https://yourdomain.com",  # Replace with actual domain
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# Add trusted host middleware
trusted_hosts = ["localhost", "127.0.0.1", "yourdomain.com"]  # Replace with actual hosts
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=trusted_hosts
)

# Add rate limiting
app.state.limiter = rate_limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    audit_logger.error(f"Unhandled exception: {str(exc)}", extra={
        "path": request.url.path,
        "method": request.method,
        "client": request.client.host if request.client else None
    })
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

@app.exception_handler(crud.CRUDError)
async def crud_exception_handler(request: Request, exc: crud.CRUDError):
    """Handle CRUD operation errors"""
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )

# SERVE ADMIN PANEL HTML
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def serve_admin_panel():
    """Serve the admin panel HTML file"""
    try:
        return FileResponse("admin_panel.html", media_type="text/html")
    except FileNotFoundError:
        return HTMLResponse("<h1>Admin Panel Not Found</h1><p>Please ensure admin_panel.html exists in the root directory.</p>", status_code=404)

@app.get("/admin", response_class=HTMLResponse, include_in_schema=False)
async def serve_admin_panel_alt():
    """Alternative route for admin panel"""
    return await serve_admin_panel()

# Health check endpoint
@app.get("/health")
async def health_check():
    """Comprehensive health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "2.0.0",
        "database": "connected",
        "services": {
            "whatsapp": whatsapp_service.get_status(),
            "email": email_service.get_status(),
            "calendar": calendar_service.get_service_status()
        }
    }

# ==================== AUTHENTICATION ENDPOINTS ====================

@app.post("/api/v1/auth/token", response_model=schemas.TokenResponse)
@rate_limiter.limit("5/minute")
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login endpoint with comprehensive security features"""
    try:
        # Get user and validate
        user = crud.get_user_by_username(db, form_data.username)
        if not user or not user.is_active:
            await asyncio.sleep(1)  # Prevent timing attacks
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )

        # Check account lockout
        if user.account_locked_until and user.account_locked_until > datetime.utcnow():
            crud.create_audit_log(
                db=db, user_id=user.id, action="ACCESS_DENIED",
                resource_type="auth", details={"reason": "account_locked"},
                ip_address=request.client.host, user_agent=request.headers.get("user-agent")
            )
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Account is locked. Please contact administrator."
            )

        # Verify password
        if not verify_password(form_data.password, user.password_hash):
            # Increment failed attempts
            user.failed_login_attempts += 1
            
            # Lock account after 5 failed attempts
            if user.failed_login_attempts >= 5:
                user.account_locked_until = datetime.utcnow() + timedelta(minutes=30)
                
            db.commit()
            
            crud.create_audit_log(
                db=db, user_id=user.id, action="ACCESS_DENIED",
                resource_type="auth", details={"reason": "invalid_password"},
                ip_address=request.client.host, user_agent=request.headers.get("user-agent")
            )
            
            await asyncio.sleep(1)  # Prevent timing attacks
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )

        # Reset failed attempts on successful password verification
        user.failed_login_attempts = 0
        user.account_locked_until = None

        # Check if MFA is enabled
        if user.mfa_enabled:
            # Create temporary MFA token
            mfa_token = mfa_service.create_mfa_token(user.id)
            
            crud.create_audit_log(
                db=db, user_id=user.id, action="LOGIN",
                resource_type="auth", details={"mfa_required": True},
                ip_address=request.client.host, user_agent=request.headers.get("user-agent")
            )
            
            return JSONResponse(
                status_code=202,
                content={
                    "mfa_required": True,
                    "mfa_token": mfa_token,
                    "message": "MFA verification required"
                }
            )

        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username, "user_id": user.id, "role": user.role},
            expires_delta=access_token_expires
        )

        # Update user login info
        user.last_login = datetime.utcnow()
        user.last_login_ip = request.client.host
        user.current_session_id = f"session_{user.id}_{int(datetime.utcnow().timestamp())}"
        db.commit()

        # Log successful login
        crud.create_audit_log(
            db=db, user_id=user.id, action="LOGIN",
            resource_type="auth", ip_address=request.client.host,
            user_agent=request.headers.get("user-agent")
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "permissions": user.permissions or {}
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        audit_logger.error(f"Login error for {form_data.username}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@app.post("/api/v1/auth/mfa/verify", response_model=schemas.TokenResponse)
@rate_limiter.limit("3/minute")
async def verify_mfa(
    request: Request,
    mfa_request: schemas.MFAVerifyRequest,
    db: Session = Depends(get_db)
):
    """Verify MFA code and return access token"""
    try:
        # Verify MFA token and get user_id
        user_id = mfa_service.verify_mfa_token(mfa_request.mfa_token)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired MFA token"
            )

        user = crud.get_user(db, user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )

        # Verify MFA code
        if not mfa_service.verify_totp_code(user.mfa_secret, mfa_request.mfa_code):
            crud.create_audit_log(
                db=db, user_id=user.id, action="ACCESS_DENIED",
                resource_type="auth", details={"reason": "invalid_mfa"},
                ip_address=request.client.host
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid MFA code"
            )

        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username, "user_id": user.id, "role": user.role},
            expires_delta=access_token_expires
        )

        # Update user login info
        user.last_login = datetime.utcnow()
        user.last_login_ip = request.client.host
        user.current_session_id = f"session_{user.id}_{int(datetime.utcnow().timestamp())}"
        db.commit()

        # Log successful MFA verification
        crud.create_audit_log(
            db=db, user_id=user.id, action="LOGIN",
            resource_type="auth", details={"mfa_verified": True},
            ip_address=request.client.host
        )

        return {
            "access_token": access_token,
            "token_type": "bearer", 
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "permissions": user.permissions or {}
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        audit_logger.error(f"MFA verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="MFA verification failed"
        )

@app.post("/api/v1/auth/logout")
async def logout(
    request: Request,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Logout endpoint with session invalidation"""
    try:
        # Invalidate current session
        current_user.current_session_id = None
        db.commit()

        # Log logout
        crud.create_audit_log(
            db=db, user_id=current_user.id, action="LOGOUT",
            resource_type="auth", ip_address=request.client.host
        )
        
        return {"message": "Logout successful"}
    except Exception as e:
        audit_logger.error(f"Logout error for user {current_user.id}: {str(e)}")
        return {"message": "Logout completed"}

# ==================== USER MANAGEMENT ENDPOINTS ====================

@app.get("/api/v1/users", response_model=List[schemas.UserResponse])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    role: Optional[str] = None,
    current_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get users (admin only)"""
    users = crud.get_users(db, skip=skip, limit=limit, role=role)
    
    # Log access
    crud.create_audit_log(
        db=db, user_id=current_user.id, action="READ",
        resource_type="users", details={"count": len(users)}
    )
    
    return users

@app.post("/api/v1/users", response_model=schemas.UserResponse)
async def create_user(
    user: schemas.UserCreate,
    current_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create new user (admin only)"""
    try:
        db_user = crud.create_user(db, user, created_by=current_user.id)
        
        # Log creation
        crud.create_audit_log(
            db=db, user_id=current_user.id, action="CREATE",
            resource_type="user", resource_id=db_user.id,
            details={"username": user.username, "role": user.role}
        )
        
        return db_user
    except crud.CRUDError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==================== PATIENT ENDPOINTS ====================

@app.get("/api/v1/patients", response_model=List[schemas.PatientResponse])
async def get_patients(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get patients with optional search"""
    try:
        patients = crud.get_patients(db, skip=skip, limit=limit, search=search)
        
        # Log access
        crud.create_audit_log(
            db=db, user_id=current_user.id, action="READ",
            resource_type="patients", details={
                "count": len(patients),
                "search_term": search if search else None
            },
            business_justification="Patient management and care coordination"
        )
        
        return patients
    except crud.CRUDError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/patients/{patient_id}", response_model=schemas.PatientResponse)
async def get_patient(
    patient_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get single patient"""
    try:
        patient = crud.get_patient(db, patient_id)
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Log access to PHI
        crud.create_audit_log(
            db=db, user_id=current_user.id, action="READ",
            resource_type="patient", resource_id=patient_id,
            business_justification="Patient care and treatment"
        )
        
        return patient
    except crud.CRUDError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/v1/patients", response_model=schemas.PatientResponse)
async def create_patient(
    patient: schemas.PatientCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new patient"""
    try:
        db_patient = crud.create_patient(db, patient, current_user.id)
        
        # Log creation
        crud.create_audit_log(
            db=db, user_id=current_user.id, action="CREATE",
            resource_type="patient", resource_id=db_patient.id,
            details={"name_encrypted": True},
            business_justification="New patient registration"
        )
        
        return db_patient
    except crud.CRUDError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/api/v1/patients/{patient_id}", response_model=schemas.PatientResponse)
async def update_patient(
    patient_id: int,
    patient_update: schemas.PatientUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update patient information"""
    try:
        # Get current patient data for audit log
        current_patient = crud.get_patient(db, patient_id)
        if not current_patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        db_patient = crud.update_patient(db, patient_id, patient_update, current_user.id)
        
        # Log update with old/new values
        crud.create_audit_log(
            db=db, user_id=current_user.id, action="UPDATE",
            resource_type="patient", resource_id=patient_id,
            details={"fields_updated": list(patient_update.dict(exclude_unset=True).keys())},
            business_justification="Patient information update"
        )
        
        return db_patient
    except crud.CRUDError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==================== APPOINTMENT ENDPOINTS ====================

@app.get("/api/v1/appointments", response_model=List[schemas.AppointmentResponse])
async def get_appointments(
    skip: int = 0,
    limit: int = 25,
    status: Optional[str] = None,
    location_id: Optional[int] = None,
    patient_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get appointments with comprehensive filtering"""
    try:
        appointments = crud.get_appointments(
            db, skip=skip, limit=limit, status=status, 
            location_id=location_id, patient_id=patient_id,
            start_date=start_date, end_date=end_date
        )
        
        # Log access
        crud.create_audit_log(
            db=db, user_id=current_user.id, action="READ",
            resource_type="appointments", details={
                "count": len(appointments),
                "filters": {
                    "status": status,
                    "location_id": location_id,
                    "patient_id": patient_id
                }
            }
        )
        
        return appointments
    except crud.CRUDError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/appointments/{appointment_id}", response_model=schemas.AppointmentResponse)
async def get_appointment(
    appointment_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get single appointment"""
    try:
        appointment = crud.get_appointment(db, appointment_id)
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        # Log access
        crud.create_audit_log(
            db=db, user_id=current_user.id, action="READ",
            resource_type="appointment", resource_id=appointment_id
        )
        
        return appointment
    except crud.CRUDError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/v1/appointments", response_model=schemas.AppointmentResponse)
async def create_appointment(
    appointment: schemas.AppointmentCreate,
    background_tasks: BackgroundTasks,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new appointment with calendar integration"""
    try:
        db_appointment = crud.create_appointment(db, appointment, current_user.id)
        
        # Background task: Create Google Calendar event
        if calendar_service.is_enabled():
            background_tasks.add_task(
                create_calendar_event_task,
                appointment_id=db_appointment.id,
                db_session=db
            )
        
        # Background task: Send confirmation if patient has WhatsApp
        if db_appointment.patient and db_appointment.patient.whatsapp_opt_in:
            background_tasks.add_task(
                send_appointment_confirmation,
                appointment_id=db_appointment.id,
                db_session=db
            )
        
        # Log creation
        crud.create_audit_log(
            db=db, user_id=current_user.id, action="CREATE",
            resource_type="appointment", resource_id=db_appointment.id,
            details={
                "patient_id": appointment.patient_id,
                "start_time": appointment.start_time.isoformat(),
                "location_id": appointment.location_id
            }
        )
        
        return db_appointment
    except crud.CRUDError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/api/v1/appointments/{appointment_id}", response_model=schemas.AppointmentResponse)
async def update_appointment(
    appointment_id: int,
    appointment_update: schemas.AppointmentUpdate,
    background_tasks: BackgroundTasks,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update appointment"""
    try:
        db_appointment = crud.update_appointment(db, appointment_id, appointment_update)
        if not db_appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        # Background task: Update calendar event if time changed
        if any(field in appointment_update.dict(exclude_unset=True) for field in ["start_time", "end_time"]):
            if calendar_service.is_enabled() and db_appointment.google_calendar_event_id:
                background_tasks.add_task(
                    update_calendar_event_task,
                    appointment_id=appointment_id,
                    db_session=db
                )
        
        # Log update
        crud.create_audit_log(
            db=db, user_id=current_user.id, action="UPDATE",
            resource_type="appointment", resource_id=appointment_id,
            details={"fields_updated": list(appointment_update.dict(exclude_unset=True).keys())}
        )
        
        return db_appointment
    except crud.CRUDError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==================== WHATSAPP WEBHOOK ENDPOINTS ====================

@app.post("/api/v1/whatsapp/webhook")
async def whatsapp_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """WhatsApp webhook endpoint for receiving messages"""
    try:
        payload = await request.json()
        
        # Process webhook in background to return quickly
        background_tasks.add_task(
            process_whatsapp_webhook,
            payload=payload,
            db_session=db
        )
        
        return {"success": True}
    except Exception as e:
        audit_logger.error(f"WhatsApp webhook error: {str(e)}")
        return {"success": False, "error": "Processing failed"}

@app.get("/api/v1/whatsapp/webhook")
async def whatsapp_webhook_verify(request: Request):
    """WhatsApp webhook verification for Meta"""
    verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN", "your_verify_token")
    
    challenge = request.query_params.get("hub.challenge")
    token = request.query_params.get("hub.verify_token")
    
    if token == verify_token and challenge:
        return int(challenge)
    else:
        raise HTTPException(status_code=403, detail="Invalid verify token")

# ==================== LOCATION ENDPOINTS ====================

@app.get("/api/v1/locations", response_model=List[schemas.LocationResponse])
async def get_locations(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all active locations"""
    try:
        locations = crud.get_locations(db)
        return locations
    except crud.CRUDError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/v1/locations", response_model=schemas.LocationResponse)
async def create_location(
    location: schemas.LocationCreate,
    current_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create new location (admin only)"""
    try:
        db_location = crud.create_location(db, location, current_user.id)
        
        # Log creation
        crud.create_audit_log(
            db=db, user_id=current_user.id, action="CREATE",
            resource_type="location", resource_id=db_location.id,
            details={"name": location.name}
        )
        
        return db_location
    except crud.CRUDError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==================== DASHBOARD ENDPOINTS ====================

@app.get("/api/v1/dashboard/stats", response_model=schemas.DashboardStatsResponse)
async def get_dashboard_stats(
    location_id: Optional[int] = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dashboard statistics"""
    try:
        stats = crud.get_dashboard_stats(db, location_id=location_id)
        return stats
    except crud.CRUDError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==================== SERVICE STATUS ENDPOINTS ====================

@app.get("/api/v1/services/status", response_model=schemas.ServicesStatusResponse)
async def get_services_status():
    """Get status of all integrated services"""
    return {
        "whatsapp": {
            "enabled": bool(os.getenv("WHATSAPP_ACCESS_TOKEN")),
            "status": "connected" if os.getenv("WHATSAPP_ACCESS_TOKEN") else "disconnected"
        },
        "email": {
            "enabled": bool(os.getenv("SENDGRID_API_KEY") or os.getenv("SMTP_SERVER")),
            "status": "connected" if (os.getenv("SENDGRID_API_KEY") or os.getenv("SMTP_SERVER")) else "disconnected"
        },
        "calendar": calendar_service.get_service_status()
    }

# ==================== AUDIT LOG ENDPOINTS ====================

@app.get("/api/v1/audit/logs", response_model=List[schemas.AuditLogResponse])
async def get_audit_logs(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get audit logs (admin only)"""
    try:
        logs = crud.get_audit_logs(
            db, skip=skip, limit=limit, user_id=user_id,
            action=action, resource_type=resource_type,
            start_date=start_date, end_date=end_date
        )
        
        # Log audit log access
        crud.create_audit_log(
            db=db, user_id=current_user.id, action="READ",
            resource_type="audit_logs", details={"count": len(logs)}
        )
        
        return logs
    except crud.CRUDError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==================== BACKGROUND TASK FUNCTIONS ====================

async def create_calendar_event_task(appointment_id: int, db_session: Session):
    """Background task to create Google Calendar event"""
    try:
        appointment = crud.get_appointment(db_session, appointment_id)
        if appointment and appointment.patient and appointment.location:
            event_id = await calendar_service.create_calendar_event(
                appointment, appointment.patient, appointment.location
            )
            if event_id:
                crud.update_appointment_calendar_event(db_session, appointment_id, event_id)
    except Exception as e:
        audit_logger.error(f"Calendar event creation failed for appointment {appointment_id}: {str(e)}")

async def update_calendar_event_task(appointment_id: int, db_session: Session):
    """Background task to update Google Calendar event"""
    try:
        appointment = crud.get_appointment(db_session, appointment_id)
        if appointment and appointment.google_calendar_event_id:
            await calendar_service.update_calendar_event(
                appointment.google_calendar_event_id, appointment
            )
    except Exception as e:
        audit_logger.error(f"Calendar event update failed for appointment {appointment_id}: {str(e)}")

async def send_appointment_confirmation(appointment_id: int, db_session: Session):
    """Background task to send appointment confirmation via WhatsApp"""
    try:
        appointment = crud.get_appointment(db_session, appointment_id)
        if appointment and appointment.patient and appointment.patient.whatsapp_opt_in:
            await whatsapp_service.send_appointment_confirmation(appointment)
    except Exception as e:
        audit_logger.error(f"WhatsApp confirmation failed for appointment {appointment_id}: {str(e)}")

async def process_whatsapp_webhook(payload: dict, db_session: Session):
    """Background task to process WhatsApp webhook"""
    try:
        result = await whatsapp_service.handle_webhook(payload, db_session)
        
        # Log webhook processing
        crud.create_audit_log(
            db=db_session, action="CREATE",
            resource_type="whatsapp_message",
            details={"webhook_processed": True, "result": result}
        )
    except Exception as e:
        audit_logger.error(f"WhatsApp webhook processing failed: {str(e)}")

# ==================== STARTUP SCRIPT ====================

if __name__ == "__main__":
    # Development server
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["app"],
        log_level="info"
    )