import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

# Corrected absolute imports
from app import models, crud
from app.database import engine, SessionLocal
from app.routers import appointments, auth, users, patients, locations
from app.limiter import limiter

# Create the database tables
models.Base.metadata.create_all(bind=engine)

# Initialize FastAPI and Rate Limiter
app = FastAPI(
    title="Dr. Dhingra's Clinic OS API (V5 - User Management)",
    description="The backend API for managing appointments, patients, schedules, and users with role-based access.",
    version="5.0.0",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- Automated Admin User Creation on Startup ---
@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    try:
        # Check if the main admin user exists
        user_p1000 = crud.get_user_by_username(db, username="p1000")
        if not user_p1000:
            print("Creating initial superadmin user: p1000")
            crud.create_initial_admin_user(db, username="p1000", password="superadminpassword")
            print("--> User 'p1000' created with password 'superadminpassword'")
        
        # Check if the client admin user exists
        user_dratul = crud.get_user_by_username(db, username="dratul")
        if not user_dratul:
            print("Creating initial client admin user: dratul")
            crud.create_initial_admin_user(db, username="dratul", password="dratulpassword")
            print("--> User 'dratul' created with password 'dratulpassword'")

    finally:
        db.close()

# Configure CORS
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
if not os.path.exists("patient_uploads"):
    os.makedirs("patient_uploads")
app.mount("/uploads", StaticFiles(directory="patient_uploads"), name="uploads")
app.include_router(auth.router)
app.include_router(appointments.router)
app.include_router(users.router)
app.include_router(patients.router)
app.include_router(locations.router)

# Root Endpoint
@app.get("/")
def read_root():
    """Root endpoint to confirm the API is running."""
    return {"status": "ok", "message": "Welcome to Dr. Dhingra's Clinic OS API"}
