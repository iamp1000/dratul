from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
from .. import crud, schemas, security, models
from ..database import get_db
from ..services.whatsapp_service import whatsapp_service
from ..services.email_service import email_service
import os

router = APIRouter(
    prefix="/prescriptions",
    tags=["Prescriptions"],
    dependencies=[Depends(security.get_current_user)],
    responses={404: {"description": "Not found"}},
)

@router.post("/share")
async def share_prescription(
    share_data: schemas.PrescriptionShare,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """Share prescription via WhatsApp or Email"""
    
    # Get patient and document
    patient = crud.get_patient_details(db, share_data.patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    document = db.query(models.Document).filter(models.Document.id == share_data.document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Determine contact method
    if share_data.method == "whatsapp":
        phone_number = share_data.whatsapp_number or patient.whatsapp_number or patient.phone_number
        if not phone_number:
            raise HTTPException(status_code=400, detail="No WhatsApp number available")
        
        # Send WhatsApp message in background
        background_tasks.add_task(
            send_whatsapp_prescription,
            phone_number, patient.name, document.file_path, 
            share_data.message, db, current_user.id, share_data.patient_id
        )
        
    elif share_data.method == "email":
        email = share_data.email or patient.email
        if not email:
            raise HTTPException(status_code=400, detail="No email address available")
        
        # Send email in background
        background_tasks.add_task(
            send_email_prescription,
            email, patient.name, document.file_path, 
            share_data.message, db, current_user.id, share_data.patient_id
        )
    
    return {"message": "Prescription sharing initiated successfully"}

async def send_whatsapp_prescription(phone: str, patient_name: str, document_path: str, message: str, db: Session, user_id: int, patient_id: int):
    """Background task to send WhatsApp prescription"""
    result = await whatsapp_service.send_prescription(phone, patient_name, document_path, message)
    
    # Log the activity
    crud.create_prescription_share_log(db, user_id, patient_id, "whatsapp", result["success"])

async def send_email_prescription(email: str, patient_name: str, document_path: str, 
                                message: str, db: Session, user_id: int, patient_id: int):
    """Background task to send email prescription"""
    result = await email_service.send_prescription_email(email, patient_name, document_path, message)
    
    # Log the activity
    crud.create_prescription_share_log(db, user_id, patient_id, "email", result["success"])
