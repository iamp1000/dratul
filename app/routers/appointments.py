# app/routers/appointments.py
# V4: Corrected to import the limiter from its own file.

from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, date

from app import crud, schemas, models, security
from app.database import get_db
from app.limiter import limiter # <-- IMPORT FROM THE NEW FILE

router = APIRouter(
    tags=["Appointments"],
    responses={404: {"description": "Not found"}},
)

@router.post("/appointments", response_model=schemas.AppointmentResponse)
@limiter.limit("5/minute") # This decorator now works correctly
def create_new_appointment(
    appointment: schemas.AppointmentCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """Create a new appointment (rate-limited)."""
    new_appointment = crud.create_appointment(db=db, appointment=appointment, user_id=current_user.id)
    background_tasks.add_task(
        crud.create_audit_log,
        db=db, user_id=current_user.id, action="CREATE", category="APPOINTMENT",
        resource_id=new_appointment.id, details=f"Created new appointment for patient ID {new_appointment.patient_id} at {new_appointment.start_time}",
        new_values=appointment.dict()
    )
    return new_appointment

# ... (the rest of the file remains the same) ...

@router.get("/appointments", response_model=List[schemas.AppointmentResponse])
def read_appointments(
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db)
):
    """Retrieve appointments within a date range."""
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    return crud.get_appointments_by_date_range(db, start_date=start_datetime, end_date=end_datetime)

@router.patch("/appointments/{appointment_id}/status", response_model=schemas.AppointmentResponse)
def update_appointment_status_endpoint(
    appointment_id: int,
    status_update: schemas.AppointmentUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """Update an appointment's status (e.g., to 'Confirmed' or 'Cancelled')."""
    db_appointment = crud.get_appointment(db, appointment_id=appointment_id)
    if db_appointment is None:
        raise HTTPException(status_code=404, detail="Appointment not found")

    old_status = db_appointment.status.value
    updated_appointment = crud.update_appointment_status(db=db, appointment_id=appointment_id, status=status_update.status)
    
    background_tasks.add_task(
        crud.create_audit_log,
        db=db, user_id=current_user.id, action="UPDATE", category="APPOINTMENT",
        resource_id=appointment_id, details=f"Updated appointment status from '{old_status}' to '{status_update.status.value}'",
        old_values={"status": old_status},
        new_values={"status": status_update.status.value}
    )
    return updated_appointment