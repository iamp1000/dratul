from fastapi import APIRouter
from ..services.calendar_service import GoogleCalendarService
from ..services.email_service import email_service
from ..services.whatsapp_service import WhatsAppService
from .. import schemas

router = APIRouter(
    prefix="/services",
    tags=["Services"],
)

@router.get("/status", response_model=schemas.ServicesStatusResponse)
def services_status():
    calendar = GoogleCalendarService()
    whatsapp = WhatsAppService()

    calendar_status = calendar.get_service_status()

    whatsapp_status = {
        "enabled": whatsapp.enabled,
        "status": "healthy" if whatsapp.enabled else "disabled",
        "last_check": None,
        "error": None,
    }

    email_status = {
        "enabled": email_service.enabled,
        "status": "healthy" if email_service.enabled else "disabled",
        "last_check": None,
        "error": None,
    }

    return {
        "whatsapp": whatsapp_status,
        "email": email_status,
        "calendar": calendar_status,
    }
