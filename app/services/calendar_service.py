
import os
import json
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
import asyncio
from google.oauth2.credentials import Credentials
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging
from sqlalchemy.orm import Session

from ..config import get_settings
from .. import models, schemas, crud

logger = logging.getLogger(__name__)

class GoogleCalendarService:
    """Google Calendar integration for appointment scheduling and availability"""

    def __init__(self):
        self.scopes = [
            'https://www.googleapis.com/auth/calendar',
            'https://www.googleapis.com/auth/calendar.events'
        ]

        # Try to initialize with service account or OAuth credentials
        self.service = None
        self.enabled = False

        self._initialize_service()

    def _initialize_service(self):
        """Initialize Google Calendar service"""
        try:
            # Try service account first (for server-to-server)
            service_account_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
            if service_account_file and os.path.exists(service_account_file):
                credentials = ServiceAccountCredentials.from_service_account_file(
                    service_account_file,
                    scopes=self.scopes
                )
                self.service = build('calendar', 'v3', credentials=credentials)
                self.enabled = True
                logger.info("✅ Google Calendar Service Account - ENABLED")
                return

            # Try OAuth credentials (for user authorization)
            credentials_file = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
            token_file = os.getenv("GOOGLE_TOKEN_FILE", "token.json")

            if os.path.exists(token_file):
                credentials = Credentials.from_authorized_user_file(token_file, self.scopes)
                if credentials and credentials.valid:
                    self.service = build('calendar', 'v3', credentials=credentials)
                    self.enabled = True
                    logger.info("✅ Google Calendar OAuth - ENABLED")
                    return
                elif credentials and credentials.expired and credentials.refresh_token:
                    credentials.refresh()
                    # Save refreshed credentials
                    with open(token_file, 'w') as token:
                        token.write(credentials.to_json())
                    self.service = build('calendar', 'v3', credentials=credentials)
                    self.enabled = True
                    logger.info("✅ Google Calendar OAuth (Refreshed) - ENABLED")
                    return

            logger.warning("⚠️ Google Calendar not configured - Service disabled")

        except Exception as e:
            logger.error(f"Failed to initialize Google Calendar service: {str(e)}")
            self.enabled = False

    def get_authorization_url(self) -> Optional[str]:
        """Get OAuth authorization URL for first-time setup"""
        try:
            credentials_file = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
            if not os.path.exists(credentials_file):
                logger.error("Google credentials file not found")
                return None

            flow = Flow.from_client_secrets_file(
                credentials_file,
                scopes=self.scopes,
                redirect_uri='urn:ietf:wg:oauth:2.0:oob'  # For desktop/server apps
            )

            authorization_url, _ = flow.authorization_url(prompt='consent')
            return authorization_url

        except Exception as e:
            logger.error(f"Failed to get authorization URL: {str(e)}")
            return None

    def exchange_code_for_token(self, authorization_code: str) -> bool:
        """Exchange authorization code for access token"""
        try:
            credentials_file = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
            token_file = os.getenv("GOOGLE_TOKEN_FILE", "token.json")

            flow = Flow.from_client_secrets_file(
                credentials_file,
                scopes=self.scopes,
                redirect_uri='urn:ietf:wg:oauth:2.0:oob'
            )

            flow.fetch_token(code=authorization_code)
            credentials = flow.credentials

            # Save credentials
            with open(token_file, 'w') as token:
                token.write(credentials.to_json())

            # Initialize service
            self.service = build('calendar', 'v3', credentials=credentials)
            self.enabled = True

            logger.info("✅ Google Calendar authorization successful")
            return True

        except Exception as e:
            logger.error(f"Failed to exchange code for token: {str(e)}")
            return False

    async def create_calendar_event(self, appointment: models.Appointment, 
                                  patient: models.Patient, location: models.Location) -> Optional[str]:
        """Create a calendar event for an appointment"""
        if not self.enabled:
            logger.info("Google Calendar not enabled - skipping event creation")
            return None

        try:
            # Format event details
            start_time = appointment.start_time.isoformat()
            end_time = appointment.end_time.isoformat()

            appointment_id = str(appointment.id)
            patient_phone = patient.phone_number or "Not provided"
            appointment_reason = appointment.reason or "General consultation"
            appointment_type = appointment.appointment_type or "Consultation"
            appointment_notes = appointment.notes or "No additional notes"

            description = f"""Patient: {patient.name}
Reason: {appointment_reason}
Type: {appointment_type}
Phone: {patient_phone}
Appointment ID: #{appointment_id}

Notes: {appointment_notes}"""

            event = {
                'summary': f'Appointment: {patient.name}',
                'description': description,
                'start': {
                    'dateTime': start_time,
                    'timeZone': location.timezone or 'UTC',
                },
                'end': {
                    'dateTime': end_time,
                    'timeZone': location.timezone or 'UTC',
                },
                'location': location.address or location.name,
                'attendees': [],
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'popup', 'minutes': 1440},  # 1 day before
                        {'method': 'popup', 'minutes': 60},    # 1 hour before
                    ],
                },
                'colorId': '9',  # Blue color for appointments
                'visibility': 'private',
            }

            # Add patient email if available
            if patient.email:
                event['attendees'].append({
                    'email': patient.email,
                    'displayName': patient.name,
                    'responseStatus': 'tentative'
                })

            # Create the event
            created_event = self.service.events().insert(
                calendarId='primary',
                body=event,
                sendUpdates='all' if patient.email else 'none'
            ).execute()

            event_id = created_event.get('id')
            logger.info(f"Created calendar event {event_id} for appointment {appointment.id}")

            return event_id

        except HttpError as e:
            logger.error(f"Failed to create calendar event: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating calendar event: {str(e)}")
            return None

    async def update_calendar_event(self, event_id: str, appointment: models.Appointment,
                                  patient: models.Patient, location: models.Location) -> bool:
        """Update an existing calendar event"""
        if not self.enabled:
            return False

        try:
            # Get existing event
            existing_event = self.service.events().get(
                calendarId='primary',
                eventId=event_id
            ).execute()

            # Update event details
            start_time = appointment.start_time.isoformat()
            end_time = appointment.end_time.isoformat()

            appointment_id = str(appointment.id)
            patient_phone = patient.phone_number or "Not provided"
            appointment_reason = appointment.reason or "General consultation"
            appointment_type = appointment.appointment_type or "Consultation"
            appointment_status = appointment.status.value.title()
            appointment_notes = appointment.notes or "No additional notes"

            description = f"""Patient: {patient.name}
Reason: {appointment_reason}
Type: {appointment_type}
Phone: {patient_phone}
Status: {appointment_status}
Appointment ID: #{appointment_id}

Notes: {appointment_notes}"""

            existing_event.update({
                'summary': f'Appointment: {patient.name}',
                'description': description,
                'start': {
                    'dateTime': start_time,
                    'timeZone': location.timezone or 'UTC',
                },
                'end': {
                    'dateTime': end_time,
                    'timeZone': location.timezone or 'UTC',
                },
                'location': location.address or location.name,
            })

            # Update color based on status
            status_colors = {
                'scheduled': '9',    # Blue
                'confirmed': '10',   # Green
                'cancelled': '4',    # Red
                'completed': '2',    # Green
                'no_show': '6',      # Orange
            }
            existing_event['colorId'] = status_colors.get(appointment.status.value, '9')

            # Update the event
            updated_event = self.service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=existing_event,
                sendUpdates='all' if patient.email else 'none'
            ).execute()

            logger.info(f"Updated calendar event {event_id} for appointment {appointment.id}")
            return True

        except HttpError as e:
            logger.error(f"Failed to update calendar event: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error updating calendar event: {str(e)}")
            return False

    async def delete_calendar_event(self, event_id: str) -> bool:
        """Delete a calendar event"""
        if not self.enabled:
            return False

        try:
            self.service.events().delete(
                calendarId='primary',
                eventId=event_id,
                sendUpdates='all'
            ).execute()

            logger.info(f"Deleted calendar event {event_id}")
            return True

        except HttpError as e:
            if e.resp.status == 404:
                logger.info(f"Calendar event {event_id} not found (already deleted)")
                return True
            logger.error(f"Failed to delete calendar event: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting calendar event: {str(e)}")
            return False

    async def get_busy_times(self, start_date: datetime, end_date: datetime,
                           calendar_id: str = 'primary') -> List[Dict[str, datetime]]:
        """Get busy times from calendar"""
        if not self.enabled:
            return []

        try:
            # Query for free/busy information
            body = {
                'timeMin': start_date.isoformat(),
                'timeMax': end_date.isoformat(),
                'items': [{'id': calendar_id}]
            }

            freebusy_query = self.service.freebusy().query(body=body).execute()
            busy_times = []

            for calendar_info in freebusy_query.get('calendars', {}).values():
                for busy_period in calendar_info.get('busy', []):
                    busy_times.append({
                        'start': datetime.fromisoformat(busy_period['start'].replace('Z', '+00:00')),
                        'end': datetime.fromisoformat(busy_period['end'].replace('Z', '+00:00'))
                    })

            return busy_times

        except HttpError as e:
            logger.error(f"Failed to get busy times: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error getting busy times: {str(e)}")
            return []

    async def get_unavailable_periods(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get unavailable periods from calendar (e.g., vacations, meetings)"""
        if not self.enabled:
            return []

        try:
            # Get events that mark unavailable periods
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=start_date.isoformat(),
                timeMax=end_date.isoformat(),
                singleEvents=True,
                orderBy='startTime',
                q='unavailable OR vacation OR meeting OR blocked'
            ).execute()

            unavailable_periods = []

            for event in events_result.get('items', []):
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))

                # Handle all-day events
                if 'T' not in start:
                    start += 'T00:00:00'
                    end = (datetime.fromisoformat(end) - timedelta(days=1)).strftime('%Y-%m-%d') + 'T23:59:59'

                unavailable_periods.append({
                    'start': datetime.fromisoformat(start.replace('Z', '+00:00')),
                    'end': datetime.fromisoformat(end.replace('Z', '+00:00')),
                    'summary': event.get('summary', 'Unavailable'),
                    'event_id': event.get('id')
                })

            return unavailable_periods

        except HttpError as e:
            logger.error(f"Failed to get unavailable periods: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error getting unavailable periods: {str(e)}")
            return []

    async def create_unavailable_period(self, start_time: datetime, end_time: datetime,
                                      reason: str = "Unavailable") -> Optional[str]:
        """Create an unavailable period in the calendar"""
        if not self.enabled:
            return None

        try:
            event = {
                'summary': f'🚫 {reason}',
                'description': f'Clinic unavailable: {reason}',
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'UTC',
                },
                'colorId': '4',  # Red color for unavailable periods
                'transparency': 'opaque',  # Show as busy
                'visibility': 'private',
                'status': 'confirmed'
            }

            created_event = self.service.events().insert(
                calendarId='primary',
                body=event
            ).execute()

            event_id = created_event.get('id')
            logger.info(f"Created unavailable period {event_id}: {reason}")

            return event_id

        except HttpError as e:
            logger.error(f"Failed to create unavailable period: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating unavailable period: {str(e)}")
            return None

    async def sync_appointments_to_calendar(self, db: Session) -> Dict[str, int]:
        """Sync all appointments without calendar events to Google Calendar"""
        if not self.enabled:
            return {"success": 0, "failed": 0, "skipped": 0}

        stats = {"success": 0, "failed": 0, "skipped": 0}

        try:
            # Get appointments without Google Calendar event IDs
            appointments = crud.get_appointments_without_calendar_events(db)

            for appointment in appointments:
                try:
                    patient = crud.get_patient(db, appointment.patient_id)
                    location = crud.get_location(db, appointment.location_id)

                    if not patient or not location:
                        stats["skipped"] += 1
                        continue

                    # Create calendar event
                    event_id = await self.create_calendar_event(appointment, patient, location)

                    if event_id:
                        # Update appointment with event ID
                        crud.update_appointment_calendar_event(db, appointment.id, event_id)
                        stats["success"] += 1
                    else:
                        stats["failed"] += 1

                except Exception as e:
                    logger.error(f"Failed to sync appointment {appointment.id}: {str(e)}")
                    stats["failed"] += 1

            logger.info(f"Calendar sync completed: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Calendar sync failed: {str(e)}")
            return stats

    def get_service_status(self) -> Dict[str, Any]:
        """Get Google Calendar service status"""
        status = {
            "enabled": self.enabled,
            "service_initialized": self.service is not None,
            "calendar_id": "primary" if self.enabled else None
        }

        if self.enabled:
            try:
                # Test API call
                calendar_info = self.service.calendars().get(calendarId='primary').execute()
                status["calendar_name"] = calendar_info.get("summary", "Primary Calendar")
                status["last_check"] = datetime.now(timezone.utc).isoformat()
                status["status"] = "healthy"
            except Exception as e:
                status["status"] = "error"
                status["error"] = str(e)
        else:
            status["status"] = "disabled"

        return status
