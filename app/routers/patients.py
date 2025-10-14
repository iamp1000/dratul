# app/routers/patients.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from .. import crud, schemas, security, models
from ..database import get_db

from fastapi import File, UploadFile, Form
import shutil
import os

router = APIRouter(
    prefix="/patients",
    tags=["Patients"],
    dependencies=[Depends(security.get_current_user)],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.PatientResponse, status_code=status.HTTP_201_CREATED)
def create_new_patient(
    patient: schemas.PatientCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """
    Create a new patient record.
    """
    db_patient = crud.get_patient_by_phone(db, phone_number=patient.phone_number)
    if db_patient:
        raise HTTPException(status_code=400, detail="Patient with this phone number already exists")
    
    new_patient = crud.create_patient(db=db, patient=patient, created_by=current_user.id)
    crud.create_activity_log(db, user_id=current_user.id, action="Create Patient", details=f"Created new patient: {new_patient.first_name} {new_patient.last_name or ''} (ID: {new_patient.id})")
    return new_patient

@router.get("/", response_model=List[schemas.PatientResponse])
def read_all_patients(skip: int = 0, limit: int = 200, search: Optional[str] = None, db: Session = Depends(get_db)):
    patients = crud.get_patients(db, skip=skip, limit=limit, search=search)
    return patients

@router.get("/{patient_id}", response_model=schemas.PatientResponse)
def read_patient_details(patient_id: int, db: Session = Depends(get_db)):
    db_patient = crud.get_patient(db, patient_id=patient_id)
    if db_patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return db_patient

@router.post("/{patient_id}/documents/", response_model=schemas.Document)
def upload_patient_document(
    patient_id: int,
    description: str = Form(...),
    upload_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    UPLOAD_DIRECTORY = "uploads"
    file_path = os.path.join(UPLOAD_DIRECTORY, f"patient_{patient_id}_{upload_file.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)

    # Use a relative path for the database so the frontend can use it
    relative_path = f"/uploads/patient_{patient_id}_{upload_file.filename}"

    return crud.create_patient_document(
        db=db, patient_id=patient_id, file_path=relative_path, description=description, user_id=current_user.id
    )

@router.post("/{patient_id}/remarks/", response_model=schemas.RemarkResponse)
def create_new_remark(
    patient_id: int,
    remark: schemas.RemarkCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    return crud.create_remark(
        db=db, patient_id=patient_id, author_id=current_user.id, text=remark.text
    )