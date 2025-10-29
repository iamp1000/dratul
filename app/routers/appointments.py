# app/routers/appointments.py
# V4: Corrected to import the limiter from its own file.

from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime, date, timezone # Added timezone

from app import crud, schemas, models, security
from app.models import BookingType, SlotStatus, UserRole # Import new models
from app.database import get_db
from app.limiter import limiter # <-- IMPORT FROM THE NEW FILE
from ..services import slot_service # Import slot service (though not directly used, good practice)

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
    """REBUILT: Create a new appointment with transactional slot capacity logic."""
    
    # --- 1. Determine Booking Type based on User Role ---
    # Front-end users (staff, admin, etc.) can overbook.
    # Other users (e.g., future patient-facing API) would be 'strict'.
    front_end_roles = [UserRole.admin, UserRole.staff, UserRole.receptionist, UserRole.manager, UserRole.doctor]
    booking_type = BookingType.walk_in if current_user.role in front_end_roles else BookingType.strict

    # --- Override booking_type if is_walk_in flag is explicitly set --- 
    if hasattr(appointment, 'is_walk_in') and appointment.is_walk_in is True:
        booking_type = BookingType.walk_in
        print(f"INFO: is_walk_in flag detected. Forcing booking_type to walk_in for user {current_user.username}.")

    # --- 2. Start Transactional Booking Logic ---
    try:
        # Ensure start_time is timezone-aware UTC for query
        start_time_utc = appointment.start_time
        if start_time_utc.tzinfo is None:
             start_time_utc = start_time_utc.replace(tzinfo=timezone.utc)
        else:
             start_time_utc = start_time_utc.astimezone(timezone.utc)

        # --- 3. Find and LOCK the slot for this transaction ---
        target_slot = db.query(models.AppointmentSlot).filter(
            models.AppointmentSlot.location_id == appointment.location_id,
            models.AppointmentSlot.start_time == start_time_utc
        ).with_for_update().first()

        if not target_slot:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="😕 **Slot Not Found:** The selected time slot does not exist or is no longer available."
            )

        # --- 4. Check Slot Status ---
        if target_slot.status in [SlotStatus.emergency_block, SlotStatus.unavailable]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="🚫 **Slot Unavailable:** The selected time slot is blocked and not available for booking."
            )

        # --- 5. Apply Booking Rules & Update Slot Status ---
        slot_updated = False
        if booking_type == BookingType.strict:
            # --- Strict Booking (e.g., Online Patient) ---
            # Check if already booked 
            if target_slot.status == SlotStatus.booked:
                 raise HTTPException(
                     status_code=status.HTTP_400_BAD_REQUEST,
                     detail="🚫 **Slot Unavailable:** The selected time slot is already booked."
                 )
            # Check capacity
            if target_slot.current_strict_appointments >= target_slot.max_strict_capacity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="🈵 **Slot Full:** This time slot is fully booked for online appointments. Please select another time."
                )
            
            # Update slot: Increment counter and set status to booked
            target_slot.current_strict_appointments += 1
            target_slot.status = SlotStatus.booked # Always booked after first strict booking
            db.add(target_slot)
            slot_updated = True
            print(f"STRICT BOOKING: Slot {target_slot.id} status set to booked. Count: {target_slot.current_strict_appointments}")

        elif booking_type == BookingType.walk_in:
            # --- Walk-In Booking using a Slot (e.g., Staff assigning a walk-in to an empty slot) ---
            # Check if the slot is already booked (by strict or a previous walk-in)
            if target_slot.status == SlotStatus.booked:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="🚫 **Slot Unavailable:** The selected time slot is already booked."
                ) # No overbooking allowed
            
            # If the slot was available, mark it as booked. No capacity check needed.
            if target_slot.status == SlotStatus.available:
                target_slot.status = SlotStatus.booked
                db.add(target_slot)
                slot_updated = True
                print(f"WALK-IN SLOT BOOKING: User {current_user.username} booked available slot {target_slot.id}. Status set to booked.")
            # (No 'else' needed here, as the check above handles the 'booked' case)
        
        # Persist slot changes if any were made
        if slot_updated:
             db.flush() # Ensure slot changes are pushed before creating appointment

        # --- 6. Create the Appointment Record ---
        # We pass the slot_id and booking_type to the refactored crud function
        new_appointment = await crud.create_appointment(
            db=db, 
            appointment=appointment, 
            user_id=current_user.id,
            slot_id=target_slot.id, 
            booking_type=booking_type
        )

        # --- 7. Commit the Transaction ---
        # This commits both the slot update (if any) and the new appointment
        db.commit()
        db.refresh(new_appointment)
        print(f"Successfully created appointment {new_appointment.id} for slot {target_slot.id}")

    except HTTPException as http_exc:
        db.rollback() # Rollback on known errors (slot full, blocked, etc.)
        raise http_exc # Re-raise the HTTP exception
    except Exception as e:
        db.rollback() # Rollback on any other error
        print(f"ERROR during transactional appointment creation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error: An unexpected error occurred while creating the appointment."
        )
    
    # Note: The 'create_appointment' crud function now handles its own audit logging for creation.
    return new_appointment

# ... (the rest of the file remains the same) ...

@router.get("/appointments", response_model=List[schemas.AppointmentResponse])
def read_appointments(
    start_date: date,
    end_date: date,
    location_id: Optional[int] = None, # <-- EDIT: Add optional location_id
    db: Session = Depends(get_db)
):
    """Retrieve appointments within a date range."""
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    # --- EDIT: Pass location_id to CRUD function ---
    return crud.get_appointments_by_date_range(db, start_date=start_datetime, end_date=end_datetime, location_id=location_id)

@router.put("/appointments/{appointment_id}", response_model=schemas.AppointmentResponse)
# --- REFACTORED: Add db_appointment parameter to crud.delete_appointment ---
# We also need to update crud.py to accept this.
# This avoids a second DB lookup in the crud function.
async def _helper_patch_crud_delete_appointment():
    pass # This is a placeholder, will edit crud.py next.

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
        raise HTTPException(status_code=404, detail="🔍 **Not Found:** The requested appointment could not be found.")
    
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
    """REBUILT: Delete an appointment, decrement slot capacity, and sync to Google Calendar."""
    
    try:
        # --- 1. Find the appointment and its associated slot ---
        db_appointment = db.query(models.Appointment).options(
            joinedload(models.Appointment.slot)
        ).filter(models.Appointment.id == appointment_id).first()

        if not db_appointment:
            raise HTTPException(status_code=404, detail="🔍 **Not Found:** The requested appointment could not be found.")

        # --- 2. Lock the slot (if it exists) to prevent race conditions ---
        if db_appointment.slot:
            target_slot = db.query(models.AppointmentSlot).filter(
                models.AppointmentSlot.id == db_appointment.slot_id
            ).with_for_update().first()

            # --- 3. Decrement strict count if it was a strict booking ---
            if target_slot and db_appointment.booking_type == BookingType.strict:
                target_slot.current_strict_appointments = max(0, target_slot.current_strict_appointments - 1)
                
                # If the slot was 'booked' (full), it is now 'available' again
                if target_slot.status == SlotStatus.booked:
                    target_slot.status = SlotStatus.available
                
                db.add(target_slot)
                print(f"STRICT DELETION: Slot {target_slot.id} count decremented to {target_slot.current_strict_appointments}")
            
            elif db_appointment.booking_type == BookingType.walk_in:
                print(f"WALK-IN DELETION: No change to slot capacity for {db_appointment.slot_id}")

        # --- 4. Call the CRUD function to delete the appointment (handles GCal) ---
        # Pass the pre-fetched db_appointment to avoid a second query
        success = await crud.delete_appointment(db=db, appointment_id=appointment_id, db_appointment=db_appointment)
        if not success:
             # This shouldn't happen if we just found it, but as a safeguard:
            raise HTTPException(status_code=404, detail="🔍 **Not Found:** The appointment could not be found during the deletion process.")

        # --- 5. Commit the transaction (deletes appointment, updates slot) ---
        db.commit()

    except HTTPException as http_exc:
        db.rollback()
        raise http_exc
    except Exception as e:
        db.rollback()
        print(f"ERROR during transactional appointment deletion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error: An unexpected error occurred while deleting the appointment."
        )

    # --- 6. Add Audit Log --- 
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
        raise HTTPException(status_code=404, detail="🔍 **Not Found:** The requested appointment could not be found.")
    
    background_tasks.add_task(
        crud.create_audit_log,
        db=db, user_id=current_user.id, action="UPDATE", category="APPOINTMENT",
        resource_id=appointment_id, details=f"Updated appointment status to '{status_update.status.value}'",
        new_values={"status": status_update.status.value}
    )
    return db_appointment