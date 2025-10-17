from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, List
from .. import crud, schemas, security, models
from ..database import get_db
from ..services.whatsapp_service import whatsapp_service
from ..services.email_service import email_service
import os
from fastapi import UploadFile, File, Form
from fastapi.responses import JSONResponse, HTMLResponse
import bleach
from xhtml2pdf import pisa
from io import BytesIO
from fastapi.responses import StreamingResponse
from fastapi import Body

router = APIRouter(
    prefix="/prescriptions",
    tags=["Prescriptions"],
    dependencies=[Depends(security.get_current_user)],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.PrescriptionResponse, status_code=201)
def create_new_prescription(
    prescription: schemas.PrescriptionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.require_medical_staff)
):
    """
    Create a new prescription.
    """
    try:
        return crud.create_prescription(db=db, prescription=prescription, prescribed_by=current_user.id)
    except crud.CRUDError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/rich", status_code=201)
def create_prescription_rich(
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.require_medical_staff)
):
    """
    Create a prescription with optional patient object.
    payload: { patient: { id? or minimal fields }, title?, body_html?, medications?[] }
    """
    try:
        patient_id = payload.get('patient_id')
        patient_payload = payload.get('patient')
        if not patient_id and patient_payload:
            patient = crud.create_or_get_patient_from_payload(db, patient_payload, created_by=current_user.id)
            patient_id = patient.id
        if not patient_id:
            raise HTTPException(status_code=400, detail="patient_id or patient payload required")

        # Persist HTML as a document entry for later viewing/printing
        html = payload.get('body_html') or ''
        doc_path = None
        doc_id = None
        if html:
            out_dir = os.path.join("patient_uploads", f"patient_{patient_id}")
            os.makedirs(out_dir, exist_ok=True)
            file_path = os.path.join(out_dir, f"prescription_{current_user.id}_{patient_id}_{int(os.path.getctime(out_dir) if os.path.exists(out_dir) else 0)}.html")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(html)
            doc = crud.create_document_for_patient(db, patient_id, file_path.replace("\\", "/"), "Prescription (editor)", current_user.id, models.DocumentType.prescription, "text/html", len(html.encode('utf-8')))
            doc_id = doc.id
            doc_path = file_path

        # Create base prescription row
        presc_schema = schemas.PrescriptionCreate(
            patient_id=patient_id,
            medication_name=payload.get('medication_name') or 'See attached',
            dosage=payload.get('dosage') or '-',
            frequency=payload.get('frequency') or '-',
            duration=payload.get('duration') or '-'
        )
        created = crud.create_prescription(db, presc_schema, prescribed_by=current_user.id)
        # Link document id to prescription if present
        if doc_id:
            try:
                obj = db.query(models.Prescription).filter(models.Prescription.id == created.id).first()
                if obj:
                    obj.document_id = doc_id
                    db.commit()
            except Exception:
                pass
        return {"id": created.id, "patient_id": patient_id, "document_path": doc_path, "document_id": doc_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/template/upload")
def upload_prescription_template(
    template_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.require_admin)
):
    """Upload a clinic prescription template (image/PDF). Stored in system configuration, not printed with data."""
    templates_dir = os.path.join("patient_uploads", "templates")
    os.makedirs(templates_dir, exist_ok=True)
    save_path = os.path.join(templates_dir, template_file.filename)
    with open(save_path, "wb") as f:
        f.write(template_file.file.read())

    crud.set_system_config(
        db,
        key="prescription_template_path",
        value=save_path.replace("\\", "/"),
        value_type="string",
        description="Path to clinic prescription template",
        category="prescriptions",
    )
    return {"success": True, "path": save_path}


@router.get("/template")
def get_prescription_template(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    entry = crud.get_system_config(db, "prescription_template_path")
    return {"path": entry.value if entry else None}


@router.post("/editor/save")
def save_editor_prescription(
    patient_id: int = Form(...),
    html_content: str = Form(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.require_medical_staff)
):
    """Save WYSIWYG HTML as a prescription document (PDF-ready)."""
    # Sanitize HTML to prevent script injection
    allowed_tags = bleach.sanitizer.ALLOWED_TAGS.union({
        'p','div','span','br','strong','em','u','sub','sup','ul','ol','li','table','thead','tbody','tr','th','td','h1','h2','h3','h4','h5','h6','img'
    })
    allowed_attrs = {
        '*': ['style', 'class'],
        'img': ['src', 'alt', 'width', 'height']
    }
    safe_html = bleach.clean(html_content, tags=allowed_tags, attributes=allowed_attrs, strip=True)

    # Store HTML as a .html file; optionally generate PDF later
    out_dir = os.path.join("patient_uploads", f"patient_{patient_id}")
    os.makedirs(out_dir, exist_ok=True)
    file_path = os.path.join(out_dir, f"prescription_{current_user.id}_{patient_id}_{len(os.listdir(out_dir)) + 1}.html")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(safe_html)

    doc = crud.create_document_for_patient(
        db,
        patient_id=patient_id,
        file_path=file_path.replace("\\", "/"),
        description="Prescription (editor)",
        user_id=current_user.id,
        document_type=models.DocumentType.prescription,
        mime_type="text/html",
        file_size=len(safe_html.encode("utf-8")),
    )
    return {"document_id": doc.id, "path": file_path}


@router.get("/editor/html/{document_id}", response_class=HTMLResponse)
def get_prescription_html(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """Return sanitized HTML for a prescription document for printing (template is client-side overlay)."""
    doc = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    path = bleach.clean(
        # path itself doesn't need bleach; kept consistent
        doc.file_path_encrypted and security.encryption_service.decrypt(doc.file_path_encrypted) or None
    )
    if not path or not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()
    return HTMLResponse(content=html)


@router.get("/editor/pdf/{document_id}")
def get_prescription_pdf(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """Return a PDF generated from the stored HTML content (template not embedded)."""
    doc = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    path = doc.file_path_encrypted and security.encryption_service.decrypt(doc.file_path_encrypted)
    if not path or not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()
    pdf_io = BytesIO()
    pisa.CreatePDF(src=html, dest=pdf_io)
    pdf_io.seek(0)
    return StreamingResponse(pdf_io, media_type="application/pdf", headers={
        "Content-Disposition": f"inline; filename=prescription_{document_id}.pdf"
    })


@router.post("/handwritten/upload")
def upload_handwritten_prescription(
    patient_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.require_medical_staff)
):
    """Upload a handwritten prescription (image/PDF) to the patient's documents."""
    out_dir = os.path.join("patient_uploads", f"patient_{patient_id}")
    os.makedirs(out_dir, exist_ok=True)
    save_path = os.path.join(out_dir, file.filename)
    with open(save_path, "wb") as f:
        f.write(file.file.read())

    doc = crud.create_document_for_patient(
        db,
        patient_id=patient_id,
        file_path=save_path.replace("\\", "/"),
        description="Prescription (handwritten)",
        user_id=current_user.id,
        document_type=models.DocumentType.prescription,
        mime_type=file.content_type,
        file_size=None,
    )
    return {"document_id": doc.id, "path": save_path}


@router.post("/share")
async def share_prescription(
    share_data: schemas.PrescriptionShare,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.require_medical_staff)
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

@router.get("/by-patient/{patient_id}", response_model=List[schemas.PrescriptionResponse])
def get_patient_prescriptions(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """
    Get all prescriptions for a specific patient.
    """
    try:
        return crud.get_prescriptions_for_patient(db=db, patient_id=patient_id)
    except crud.CRUDError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/recent", response_model=List[schemas.PrescriptionResponse])
def get_recent_prescriptions(
    limit: int = 5,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    try:
        return crud.get_recent_prescriptions(db=db, limit=limit)
    except crud.CRUDError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/defaults")
def get_prescription_defaults(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """Return stored editor defaults (header/footer/body/signature)."""
    header = crud.get_system_config(db, "prescription_defaults_header")
    footer = crud.get_system_config(db, "prescription_defaults_footer")
    body = crud.get_system_config(db, "prescription_defaults_body")
    signature = crud.get_system_config(db, "prescription_signature_url")
    return {
        "header_html": header.value if header else "",
        "footer_html": footer.value if footer else "",
        "body_html": body.value if body else "",
        "signature_url": signature.value if signature else ""
    }


@router.post("/defaults")
def set_prescription_defaults(
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.require_admin)
):
    """Save editor defaults to system configuration."""
    crud.set_system_config(db, "prescription_defaults_header", payload.get("header_html", ""), "string", "Prescription header HTML", "prescriptions")
    crud.set_system_config(db, "prescription_defaults_footer", payload.get("footer_html", ""), "string", "Prescription footer HTML", "prescriptions")
    crud.set_system_config(db, "prescription_defaults_body", payload.get("body_html", ""), "string", "Prescription body HTML", "prescriptions")
    crud.set_system_config(db, "prescription_signature_url", payload.get("signature_url", ""), "string", "Doctor signature image URL", "prescriptions")
    return {"success": True}
