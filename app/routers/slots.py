# app/routers/slots.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import date

from ..services import slot_service
from .. import schemas, models # Import models for user dependency
from ..database import get_db
from ..security import get_current_user # Assuming authentication is needed

router = APIRouter(
    prefix="/slots",
    tags=["slots"],
    dependencies=[Depends(get_current_user)], # Apply authentication
    responses={404: {"description": "Not found"}},
)

@router.get("/{location_id}/{target_date}", response_model=List[schemas.AppointmentSlot])
def get_available_slots(
    location_id: int,
    target_date: date,
    db: Session = Depends(get_db)
):
    """
    Retrieve available appointment slots for a given location and date.
    Returns a list of AppointmentSlot objects.
    """
    try:
        available_slots = slot_service.get_available_slots_for_day(
            db=db,
            location_id=location_id,
            target_date=target_date
        )
        return available_slots
    except Exception as e:
        # Log the error for debugging
        print(f"ERROR fetching slots for {location_id} on {target_date}: {e}")
        # Return a generic error to the client
        raise HTTPException(
            status_code=500,
            detail="An error occurred while fetching available slots."
        )

# Remember to include this router in your main FastAPI app (app/main.py)