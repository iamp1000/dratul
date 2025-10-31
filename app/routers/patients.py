# app/routers/patients.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from .. import crud, schemas, security, models
from ..schemas import PatientMenstrualHistoryResponse, PatientMenstrualHistoryUpdate, PatientMenstrualHistoryCreate
from ..database import get_db

from fastapi import File, UploadFile, Form
import shutil
import os
from fastapi import Body
from fastapi.responses import JSONResponse

router = APIRouter(
    tags=["Patients"],
    dependencies=[Depends(security.get_current_user)],
    responses={404: {"description": "Not found"}},
)

@router.post("/patients", response_model=schemas.PatientResponse, status_code=status.HTTP_201_CREATED)
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
        raise HTTPException(status_code=400, detail="👥 **Duplicate Patient:** A patient with this phone number already exists in the system.")
    
    new_patient = crud.create_patient(db=db, patient=patient, created_by=current_user.id)
    crud.create_audit_log(
        db=db, user_id=current_user.id, action="CREATE", category="PATIENT", 
        resource_id=new_patient.id, details=f"Created new patient: {patient.first_name} {patient.last_name or ''}",
        new_values=patient.dict()
    )
    return new_patient

@router.get("/patients", response_model=List[schemas.PatientResponse])
def read_all_patients(skip: int = 0, limit: int = 200, search: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Retrieve all patients, decrypting necessary fields.
    """
    db_patients = crud.get_patients(db, skip=skip, limit=limit, search=search)
    
    patient_responses = []
    for patient in db_patients:
        try:
            full_name = security.encryption_service.decrypt(patient.name_encrypted) if patient.name_encrypted else ""
            first_name, last_name = (full_name.split(" ", 1) + [None])[:2] if full_name else ("", None)
            patient_data = {
                "id": patient.id,
                "first_name": first_name,
                "last_name": last_name,
                "phone_number": security.encryption_service.decrypt(patient.phone_number_encrypted) if patient.phone_number_encrypted else None,
                "email": security.encryption_service.decrypt(patient.email_encrypted) if patient.email_encrypted else None,
                "date_of_birth": patient.date_of_birth,
                "city": patient.city,
                "gender": patient.gender,
                "preferred_communication": patient.preferred_communication,
                "whatsapp_number": patient.whatsapp_number,
                "whatsapp_opt_in": patient.whatsapp_opt_in,
                "hipaa_authorization": patient.hipaa_authorization,
                "consent_to_treatment": patient.consent_to_treatment,
                "created_at": patient.created_at,
                "updated_at": patient.updated_at,
                "last_visit_date": patient.last_visit_date
            }
            patient_data_filtered = {k: v for k, v in patient_data.items() if v is not None}
            patient_responses.append(schemas.PatientResponse(**patient_data_filtered))
        except Exception as e:
            print(f"Error processing patient ID {patient.id}: {e}")
            continue
            
    return patient_responses

@router.get("/patients/{patient_id}", response_model=schemas.PatientResponse)
def read_patient_details(patient_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(security.get_current_user)):
    db_patient = crud.get_patient(db, patient_id=patient_id)
    if db_patient is None:
        raise HTTPException(status_code=404, detail="🔍 **Not Found:** The patient with the specified ID could not be found.")
    crud.create_audit_log(
        db=db, user_id=current_user.id, action="READ", category="PATIENT", 
        resource_id=patient_id, details=f"Accessed details for patient ID {patient_id}"
    )
    return db_patient


@router.get("/patients/{patient_id}/composite")
def read_patient_composite(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """Return decrypted patient demographics with recent appointments, prescriptions, and remarks."""
    patient = crud.get_patient(db, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="🔍 **Not Found:** The patient with the specified ID could not be found.")
    full_name = security.encryption_service.decrypt(patient.name_encrypted) if patient.name_encrypted else ""
    first_name, last_name = (full_name.split(" ", 1) + [None])[:2] if full_name else ("", None)
    phone = security.encryption_service.decrypt(patient.phone_number_encrypted) if patient.phone_number_encrypted else None
    email = security.encryption_service.decrypt(patient.email_encrypted) if patient.email_encrypted else None

    recent_appointments = db.query(models.Appointment).filter(models.Appointment.patient_id == patient_id).order_by(models.Appointment.start_time.desc()).limit(5).all()
    recent_prescriptions = db.query(models.Prescription).filter(models.Prescription.patient_id == patient_id).order_by(models.Prescription.prescribed_date.desc()).limit(5).all()
    recent_remarks = crud.get_remarks_for_patient(db, patient_id)

    return {
        "patient": {
            "id": patient.id,
            "first_name": first_name,
            "last_name": last_name,
            "date_of_birth": patient.date_of_birth,
            "city": patient.city,
            "gender": patient.gender,
            "phone_number": phone,
            "email": email,
            "whatsapp_number": patient.whatsapp_number,
            "preferred_communication": patient.preferred_communication.value if hasattr(patient.preferred_communication, 'value') else patient.preferred_communication,
            "created_at": patient.created_at,
            "updated_at": patient.updated_at,
        },
        "appointments": recent_appointments,
        "prescriptions": recent_prescriptions,
        "remarks": recent_remarks,
    }


@router.put("/patients/{patient_id}", response_model=schemas.PatientResponse)
def update_patient_details(
    patient_id: int,
    payload: schemas.PatientUpdate = Body(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    updated = crud.update_patient(db, patient_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="🔍 **Not Found:** The patient could not be found to update.")
    return updated

@router.get("/patients/{patient_id}/remarks/", response_model=List[schemas.RemarkResponse])
def get_patient_remarks(
    patient_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all remarks for a specific patient.
    """
    try:
        return crud.get_remarks_for_patient(db=db, patient_id=patient_id)
    except crud.CRUDError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/patients/{patient_id}/menstrual-history", response_model=schemas.PatientMenstrualHistoryResponse)
def get_patient_menstrual_history_endpoint(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """
    Get the menstrual history for a specific patient.
    """
    history = crud.get_patient_menstrual_history(db, patient_id=patient_id)
    if not history:
        # Return a default empty response instead of 404
        # This allows the frontend to display an empty form
        return schemas.PatientMenstrualHistoryResponse(
            id=-1, # Use a non-existent ID to signal 'new'
            patient_id=patient_id
            # All other fields will be None by default
        )
    return history


@router.post("/patients/{patient_id}/menstrual-history", response_model=schemas.PatientMenstrualHistoryResponse)
def create_or_update_patient_menstrual_history_endpoint(
    patient_id: int,
    history_data: schemas.PatientMenstrualHistoryUpdate, # Use Update schema for the body
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """
    Create or update the menstrual history for a specific patient.
    """
    # Manually create the 'Create' schema required by the CRUD function
    # by injecting the patient_id from the URL.
    history_create_schema = schemas.PatientMenstrualHistoryCreate(
        **history_data.dict(exclude_unset=True),
        patient_id=patient_id
    )

    try:
        history = crud.create_or_update_patient_menstrual_history(
            db=db, 
            patient_id=patient_id, 
            history_data=history_create_schema
        )
        crud.create_audit_log(
            db=db, user_id=current_user.id, action="UPDATE", category="PATIENT", 
            resource_id=patient_id, details=f"Updated menstrual history for patient ID {patient_id}"
        )
        return history
    except crud.CRUDError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/patients/{patient_id}/documents/", response_model=schemas.Document)
def upload_patient_document(
    patient_id: int,
    description: str = Form(...),
    upload_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    UPLOAD_DIRECTORY = "uploads"
    file_path = os.path.join(UPLOAD_DIRECTORY, f"patient_{patient_id}_{upload_file.filename}")
    os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)

    # Use a relative path for the database so the frontend can use it
    relative_path = f"/uploads/patient_{patient_id}_{upload_file.filename}"

    new_document = crud.create_patient_document(
        db=db, patient_id=patient_id, file_path=relative_path, description=description, user_id=current_user.id
    )
    crud.create_audit_log(
        db=db, user_id=current_user.id, action="UPDATE", category="PATIENT", 
        resource_id=patient_id, details=f"Uploaded new document: {description} (Doc ID: {new_document.id})"
    )
    return new_document

@router.post("/patients/{patient_id}/remarks/", response_model=schemas.RemarkResponse)
def create_new_remark(
    patient_id: int,
    remark: schemas.RemarkCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    new_remark = crud.create_remark(
        db=db, patient_id=patient_id, author_id=current_user.id, text=remark.text
    )
    crud.create_audit_log(
        db=db, user_id=current_user.id, action="UPDATE", category="PATIENT", 
        resource_id=patient_id, details=f"Added new remark to patient ID {patient_id}"
    )
    return new_remark


@router.get("/patients/{patient_id}/prescriptions", response_model=List[schemas.PrescriptionResponse])
def get_patient_prescriptions_api(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    try:
        return crud.get_prescriptions_for_patient(db=db, patient_id=patient_id)
    except crud.CRUDError as e:
        raise HTTPException(status_code=400, detail=str(e))