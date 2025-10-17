# app/routers/appointments.py
# V4: Corrected to import the limiter from its own file.

from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks, status
from fastapi.responses import JSONResponse
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
@limiter.limit("5/minute")
async def create_new_appointment(
    appointment: schemas.AppointmentCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """Create a new appointment and sync to Google Calendar."""
    new_appointment = await crud.create_appointment(db=db, appointment=appointment, user_id=current_user.id)
    background_tasks.add_task(
        crud.create_audit_log,
        db=db, user_id=current_user.id, action="CREATE", category="APPOINTMENT",
        resource_id=new_appointment.id, details=f"Created new appointment for patient ID {new_appointment.patient_id}",
        new_values=appointment.dict(exclude_unset=True)
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

@router.put("/appointments/{appointment_id}", response_model=schemas.AppointmentResponse)
async def update_appointment_endpoint(
    appointment_id: int,
    appointment_update: schemas.AppointmentUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """Update an appointment and sync changes to Google Calendar."""
    db_appointment = await crud.update_appointment(db=db, appointment_id=appointment_id, appointment_update=appointment_update)
    if db_appointment is None:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    background_tasks.add_task(
        crud.create_audit_log,
        db=db, user_id=current_user.id, action="UPDATE", category="APPOINTMENT",
        resource_id=appointment_id, details=f"Updated appointment details for appointment ID {appointment_id}",
        new_values=appointment_update.dict(exclude_unset=True)
    )
    return db_appointment

@router.delete("/appointments/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_appointment_endpoint(
    appointment_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """Delete an appointment and sync to Google Calendar."""
    success = await crud.delete_appointment(db=db, appointment_id=appointment_id)
    if not success:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    background_tasks.add_task(
        crud.create_audit_log,
        db=db, user_id=current_user.id, action="DELETE", category="APPOINTMENT",
        resource_id=appointment_id, details=f"Deleted appointment ID {appointment_id}"
    )
    return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)

@router.patch("/appointments/{appointment_id}/status", response_model=schemas.AppointmentResponse)
async def update_appointment_status_endpoint(
    appointment_id: int,
    status_update: schemas.AppointmentUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """Update an appointment's status and sync to Google Calendar."""
    db_appointment = await crud.update_appointment(db=db, appointment_id=appointment_id, appointment_update=status_update)
    if db_appointment is None:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    background_tasks.add_task(
        crud.create_audit_log,
        db=db, user_id=current_user.id, action="UPDATE", category="APPOINTMENT",
        resource_id=appointment_id, details=f"Updated appointment status to '{status_update.status.value}'",
        new_values={"status": status_update.status.value}
    )
    return db_appointment