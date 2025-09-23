# app/routers/appointments.py
# V4: Corrected to import the limiter from its own file.

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, date

from app import crud, schemas
from app.database import get_db
from app.limiter import limiter # <-- IMPORT FROM THE NEW FILE

router = APIRouter(
    prefix="/appointments",
    tags=["Appointments"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.Appointment)
@limiter.limit("5/minute") # This decorator now works correctly
def create_new_appointment(
    appointment: schemas.AppointmentCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Create a new appointment (rate-limited)."""
    return crud.create_appointment(db=db, appointment=appointment)

# ... (the rest of the file remains the same) ...

@router.get("/", response_model=List[schemas.Appointment])
def read_appointments(
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db)
):
    """Retrieve appointments within a date range."""
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    return crud.get_appointments_by_date_range(db, start_date=start_datetime, end_date=end_datetime)

@router.patch("/{appointment_id}/status", response_model=schemas.Appointment)
def update_appointment_status_endpoint(
    appointment_id: int,
    status_update: schemas.AppointmentUpdate,
    db: Session = Depends(get_db)
):
    """Update an appointment's status (e.g., to 'Confirmed' or 'Cancelled')."""
    db_appointment = crud.get_appointment(db, appointment_id=appointment_id)
    if db_appointment is None:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return crud.update_appointment_status(db=db, appointment_id=appointment_id, status=status_update.status)
