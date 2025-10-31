# app/routers/logs.py
from datetime import datetime, timezone # Added datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from .. import crud, schemas, models
from ..models import AppointmentSlot # Import AppointmentSlot for resource type
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


@router.get("/logs/comprehensive", response_model=List[schemas.ComprehensiveLogEntry])
async def read_comprehensive_logs(
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
    Retrieve both standard audit logs and health check inconsistencies,
    combined and sorted by timestamp.
    Only accessible by administrators.
    """
    combined_entries = []

    try:
        # 1. Fetch standard audit logs
        audit_logs_orm = crud.get_audit_logs(
            db, skip=0, limit=1000, # Fetch more initially for sorting, apply limit later
            user_id=user_id, category=category,
            severity=severity, start_date=start_date, end_date=end_date
        )
        for log in audit_logs_orm:
            # Convert ORM log to Pydantic model and add log_type
            log_entry = schemas.AuditLogEntry.from_orm(log)
            combined_entries.append(log_entry)

        # 2. Run health checks (only if no specific category filter is applied, 
        #    or if the category is explicitly HEALTH_CHECK)
        if category is None or category == "HEALTH_CHECK":
            # Call the synchronous function without 'await'
            health_report = crud.run_consistency_checks(db=db)
            
            # Convert inconsistencies to HealthCheckEntry format
            check_timestamp = health_report.get("checked_at", datetime.now(timezone.utc))
            
            for issue_list_key, issue_type_description in [
                ("booked_slots_without_appointments", "Booked Slot Anomaly"),
                ("available_slots_with_appointments", "Available Slot Anomaly"),
                ("status_counter_mismatches", "Slot Counter Mismatch"),
            ]:
                for inconsistency in health_report.get(issue_list_key, []):
                    # Filter health alerts by date range if provided
                    slot_time = inconsistency.get('start_time')
                    if start_date and slot_time and slot_time.date() < start_date:
                        continue
                    if end_date and slot_time and slot_time.date() > end_date:
                        continue
                        
                    health_entry = schemas.HealthCheckEntry(
                        timestamp=check_timestamp,
                        action=issue_type_description,
                        resource_type=models.AppointmentSlot.__tablename__, # Use table name
                        resource_id=inconsistency.get('slot_id'),
                        details=inconsistency.get('issue', 'Unknown inconsistency'),
                        severity="WARN" # Or potentially ERROR depending on check
                    )
                    combined_entries.append(health_entry)

        # 3. Sort combined list by timestamp (descending)
        combined_entries.sort(key=lambda x: x.timestamp, reverse=True)

        # 4. Apply pagination (skip and limit)
        paginated_entries = combined_entries[skip : skip + limit]

        return paginated_entries

    except crud.CRUDError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"ERROR generating comprehensive log: {e}") # Log unexpected errors
        raise HTTPException(status_code=500, detail="An internal error occurred while generating the comprehensive log.")