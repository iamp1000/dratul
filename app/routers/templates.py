# app/routers/templates.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging
from datetime import datetime, timezone

from app import crud, schemas, models
from app.database import get_db
from app.security import get_current_user
from app.crud import CRUDError

router = APIRouter(
    prefix="/templates",
    tags=["Consultation Templates"],
)

logger = logging.getLogger(__name__)

@router.post("/", response_model=schemas.ConsultationTemplateResponse)
def create_consultation_template(
    template_data: schemas.ConsultationTemplateCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Create and save a new consultation template as a JSON file.
    """
    try:
        # The CRUD function saves the file and returns the template name (which we use as an ID)
        template_id = crud.save_consultation_template(template_data)
        
        # Construct the response object based on what was saved
        response_data = template_data.model_dump()
        now = datetime.now(timezone.utc)
        response_data['id'] = template_id
        response_data['created_at'] = now
        response_data['updated_at'] = now
        
        return response_data
        
    except CRUDError as e:
        logger.error(f"Failed to save template {template_data.templateName}: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error saving template {template_data.templateName}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected server error occurred.")