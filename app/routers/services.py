from fastapi import APIRouter, Query, HTTPException
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


@router.get("/google-calendar/authorize-url")
def get_google_calendar_authorize_url():
    """
    Get the URL to authorize the application with Google Calendar.
    """
    calendar = GoogleCalendarService()
    url = calendar.get_authorization_url()
    if not url:
        raise HTTPException(status_code=500, detail="Could not generate Google Calendar authorization URL. Check server logs and credentials file.")
    return {"authorization_url": url}


@router.post("/google-calendar/exchange-token")
def exchange_google_calendar_token(code: str = Query(..., description="The authorization code from Google")):
    """
    Exchange the authorization code for an access token and save it.
    """
    calendar = GoogleCalendarService()
    success = calendar.exchange_code_for_token(code)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to exchange authorization code for token. The code may be invalid or expired.")
    return {"message": "Google Calendar authorized successfully. Please restart the server."}

