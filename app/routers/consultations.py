# app/routers/consultations.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from .. import crud, schemas, security, models
from ..database import get_db

router = APIRouter(
    prefix="/consultations",
    tags=["Consultations"],
    dependencies=[Depends(security.get_current_user)], # Ensure user is logged in
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.ConsultationResponse, status_code=status.HTTP_201_CREATED)
def create_consultation_endpoint(
    consultation: schemas.ConsultationCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """
    Create a new consultation record for a patient.
    Includes nested creation of Vitals, Diagnoses, and Medications.
    """
    try:
        # Check if the user has the permission to create consultations (e.g., doctor role)
        if current_user.role not in [models.UserRole.doctor, models.UserRole.admin]:
             raise HTTPException(
                 status_code=status.HTTP_403_FORBIDDEN,
                 detail="User does not have permission to create consultations."
             )
        
        db_consultation = crud.create_consultation(db=db, consultation=consultation, user_id=current_user.id)
        return db_consultation
    except crud.CRUDError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        # Catch unexpected errors
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while creating the consultation.")

@router.get("/{consultation_id}", response_model=schemas.ConsultationResponse)
def get_consultation_endpoint(
    consultation_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """
    Retrieve a single consultation by its ID.
    Includes related Vitals, Diagnoses, Medications, Patient, and User info.
    """
    db_consultation = crud.get_consultation(db=db, consultation_id=consultation_id)
    if db_consultation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consultation not found")
    
    # Basic permission check (e.g., allow admin or the doctor who created it, or if related to a patient they can access)
    # More granular checks might be needed depending on roles
    if current_user.role != models.UserRole.admin and db_consultation.user_id != current_user.id:
        # Here you might add logic to check if the user has access to the patient
        pass # Placeholder for more complex access control if needed
        # For now, restrict non-admins to only viewing their own consultations
        # raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User does not have permission to view this consultation.")

    return db_consultation

@router.get("/patient/{patient_id}", response_model=List[schemas.ConsultationResponse])
def get_consultations_for_patient_endpoint(
    patient_id: int,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """
    Retrieve all consultations for a specific patient, ordered by date descending.
    Includes related Vitals, Diagnoses, Medications, and User info.
    """
    # Add permission check if necessary (e.g., can this user view this patient's records?)
    # if not user_can_access_patient(current_user, patient_id, db):
    #    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to patient records.")

    try:
        consultations = crud.get_consultations_for_patient(db=db, patient_id=patient_id, skip=skip, limit=limit)
        return consultations
    except crud.CRUDError as e:
        # This might happen if there's a DB error during the fetch
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# --- Add PUT/DELETE endpoints if needed ---