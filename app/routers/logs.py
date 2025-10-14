# app/routers/logs.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from .. import crud, schemas, models
from ..database import get_db
from ..security import require_admin

router = APIRouter(
    tags=["Logs"],
    dependencies=[Depends(require_admin)],
    responses={404: {"description": "Not found"}},
)

@router.get("/logs", response_model=List[schemas.AuditLogResponse])
def read_audit_logs(
    skip: int = 0, 
    limit: int = 100, 
    user_id: Optional[int] = None,
    category: Optional[str] = None,
    severity: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """
    Retrieve audit logs with optional filtering. 
    Only accessible by administrators.
    """
    try:
        logs = crud.get_audit_logs(
            db, skip=skip, limit=limit, user_id=user_id, category=category, 
            severity=severity, start_date=start_date, end_date=end_date
        )
        return logs
    except crud.CRUDError as e:
        raise HTTPException(status_code=400, detail=str(e))