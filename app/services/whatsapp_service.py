# app/services/whatsapp_service.py - Fixed version with proper imports and rate limiting

import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pywa import WhatsApp
from pywa.types import Message, CallbackButton, Button
import logging
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from ..config import settings
from ..database import get_db
from .. import models, schemas, crud

logger = logging.getLogger(__name__)


class WhatsAppChatbot:
    """WhatsApp chatbot for appointment booking and patient interactions"""

    def __init__(self):
        # Import rate_limiter properly
        try:
            from ..security import rate_limiter
            self.rate_limiter = rate_limiter
        except ImportError:
            logger.warning("Rate limiter not available, creating dummy limiter")
            self.rate_limiter = self._create_dummy_rate_limiter()

        self.flows = {
            "greeting": self.handle_greeting,
            "appointment_booking": self.handle_appointment_booking,
            "appointment_inquiry": self.handle_appointment_inquiry,
            "prescription_request": self.handle_prescription_request,
            "general_inquiry": self.handle_general_inquiry
        }

        self.booking_steps = [
            "collect_name",
            "collect_dob",
            "collect_reason",
            "show_available_slots",
            "confirm_booking"
        ]

    def _create_dummy_rate_limiter(self):
        """Create a dummy rate limiter if the real one fails"""
        class DummyRateLimiter:
            def check_whatsapp_rate_limit(self, phone_number: str, message_limit: int = 3, window_minutes: int = 1) -> bool:
                return True
            def check_appointment_booking_limit(self, phone_number: str, daily_limit: int = 2) -> bool:
                return True
        return DummyRateLimiter()

    async def process_message(self, phone_number: str, message_text: str, 
                            session_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Process incoming WhatsApp message with rate limiting"""
        
        # Check message rate limit (3 messages per minute)
        if not self.rate_limiter.check_whatsapp_rate_limit(phone_number, 
                                                          message_limit=3, 
                                                          window_minutes=1):
            return {
                "message": "⚠️ You're sending messages too quickly. Please wait a moment before sending another message.",
                "session_data": session_data
            }
        
        current_flow = session_data.get("current_flow", "greeting")

        if current_flow in self.flows:
            return await self.flows[current_flow](phone_number, message_text, session_data, db)
        else:
            return await self.handle_greeting(phone_number, message_text, session_data, db)

    async def handle_greeting(self, phone_number: str, message_text: str,
                            session_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Handle initial greeting and main menu"""
        message_lower = message_text.lower().strip()

        # Check if patient exists
        patient = crud.get_patient_by_phone_hash(db, phone_number)

        if patient:
            response = f"Hello {patient.name}! 👋\n\nHow can I help you today?"
        else:
            response = "Hello! Welcome to Dr. Dhingra's Clinic 👋\n\nI'm your virtual assistant. How can I help you today?"

        response += """

Please choose an option:
1️⃣ Book an appointment
2️⃣ Check appointment status
3️⃣ Request prescription
4️⃣ General inquiry
5️⃣ Speak to staff

Simply reply with the number or describe what you need."""

        # Determine next flow based on message
        if any(word in message_lower for word in ["book", "appointment", "schedule", "1"]):
            session_data["current_flow"] = "appointment_booking"
            session_data["current_step"] = "collect_name"
            response = await self.start_appointment_booking(phone_number, session_data, db)
        elif any(word in message_lower for word in ["check", "status", "2"]):
            session_data["current_flow"] = "appointment_inquiry"
        elif any(word in message_lower for word in ["prescription", "medicine", "3"]):
            session_data["current_flow"] = "prescription_request"
        elif any(word in message_lower for word in ["inquiry", "question", "4"]):
            session_data["current_flow"] = "general_inquiry"
        elif any(word in message_lower for word in ["staff", "human", "5"]):
            response = "I'll connect you with our staff. Please hold on...\n\n⏰ Our office hours are: Monday-Friday 9AM-6PM, Saturday 9AM-2PM"
            session_data["current_flow"] = "staff_transfer"

        return {
            "message": response,
            "session_data": session_data
        }

    async def start_appointment_booking(self, phone_number: str,
                                      session_data: Dict[str, Any], db: Session) -> str:
        """Start the appointment booking process with rate limiting"""
        
        # Check appointment booking rate limit (2 per day)
        if not self.rate_limiter.check_appointment_booking_limit(phone_number, daily_limit=2):
            return "⚠️ You have reached the daily limit for appointment bookings. Please try again tomorrow."
        
        # Check if user already has an active appointment
        if crud.has_active_appointment(db, phone_number):
            return "⚠️ You already have an active appointment. Please wait for it to be completed or cancelled before booking a new one."
        
        # Check if patient exists
        patient = crud.get_patient_by_phone_hash(db, phone_number)

        if patient:
            session_data["patient_id"] = patient.id
            session_data["patient_name"] = patient.name
            session_data["current_step"] = "collect_reason"
            return f"Hi {patient.name}! I'll help you book an appointment.\n\nWhat's the reason for your visit?"
        else:
            session_data["current_step"] = "collect_name"
            return "I'll help you book an appointment! First, I need some information.\n\nWhat's your full name?"

    async def handle_appointment_booking(self, phone_number: str, message_text: str,
                                       session_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Handle appointment booking flow"""
        current_step = session_data.get("current_step", "collect_name")

        if current_step == "collect_name":
            return await self.collect_name(phone_number, message_text, session_data, db)
        elif current_step == "collect_dob":
            return await self.collect_dob(phone_number, message_text, session_data, db)
        elif current_step == "collect_reason":
            return await self.collect_reason(phone_number, message_text, session_data, db)
        elif current_step == "show_available_slots":
            return await self.show_available_slots(phone_number, message_text, session_data, db)
        elif current_step == "confirm_booking":
            return await self.confirm_booking(phone_number, message_text, session_data, db)

        return {
            "message": "I'm sorry, I didn't understand. Let's start over.\n\nType 'menu' to see your options.",
            "session_data": {"current_flow": "greeting"}
        }

    async def collect_name(self, phone_number: str, message_text: str,
                        session_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Collect patient name"""
        name = message_text.strip().title()
        if len(name) < 2:
            return {
                "message": "Please provide your full name (at least 2 characters).",
                "session_data": session_data
            }

        session_data["patient_name"] = name
        session_data["current_step"] = "collect_dob"

        return {
            "message": f"Thank you, {name}! Now I need your date of birth.\n\nPlease enter in DD/MM/YYYY format (e.g., 15/03/1990):",
            "session_data": session_data
        }

    async def collect_dob(self, phone_number: str, message_text: str,
                        session_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Collect patient date of birth"""
        try:
            # Parse date
            dob_str = message_text.strip()
            if "/" in dob_str:
                day, month, year = dob_str.split("/")
                dob = datetime(int(year), int(month), int(day)).date()
            elif "-" in dob_str:
                year, month, day = dob_str.split("-")
                dob = datetime(int(year), int(month), int(day)).date()
            else:
                raise ValueError("Invalid format")

            # Validate age
            today = datetime.now().date()
            age = (today - dob).days // 365
            if age < 0 or age > 150:
                raise ValueError("Invalid age")

            session_data["date_of_birth"] = dob.isoformat()
            session_data["current_step"] = "collect_reason"

            return {
                "message": "Perfect! Now, what's the reason for your visit?\n\nFor example:\n• General checkup\n• Specific symptoms\n• Follow-up consultation\n• Other medical concern",
                "session_data": session_data
            }

        except (ValueError, IndexError):
            return {
                "message": "Please enter a valid date of birth in DD/MM/YYYY format (e.g., 15/03/1990):",
                "session_data": session_data
            }

    async def collect_reason(self, phone_number: str, message_text: str,
                        session_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Collect appointment reason"""
        reason = message_text.strip()
        if len(reason) < 3:
            return {
                "message": "Please provide a brief reason for your visit (at least 3 characters).",
                "session_data": session_data
            }

        session_data["appointment_reason"] = reason
        session_data["current_step"] = "show_available_slots"

        return await self.show_available_slots(phone_number, "", session_data, db)

    async def show_available_slots(self, phone_number: str, message_text: str,
                                session_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Show available appointment slots"""
        # Get available slots for the next 7 days
        available_slots = crud.get_available_appointment_slots(db, days_ahead=7)

        if not available_slots:
            return {
                "message": "I'm sorry, there are no available slots in the next week. Please call us at [PHONE_NUMBER] to schedule further out or for urgent matters.",
                "session_data": {"current_flow": "greeting"}
            }

        slots_message = "Here are the available appointment slots:\n\n"

        for i, slot in enumerate(available_slots[:10]):  # Show max 10 slots
            date_str = slot["date"].strftime("%A, %B %d")
            time_str = slot["time"].strftime("%I:%M %p")
            slots_message += f"{i+1}. {date_str} at {time_str}\n"

        slots_message += "\nPlease reply with the number of your preferred slot (e.g., '3'):"

        session_data["available_slots"] = [
            {
                "date": slot["date"].isoformat(),
                "time": slot["time"].isoformat(),
                "location_id": slot["location_id"]
            }
            for slot in available_slots[:10]
        ]
        session_data["current_step"] = "confirm_booking"

        return {
            "message": slots_message,
            "session_data": session_data
        }

    async def confirm_booking(self, phone_number: str, message_text: str,
                            session_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Confirm appointment booking with validation"""
        try:
            slot_number = int(message_text.strip()) - 1
            available_slots = session_data.get("available_slots", [])

            if slot_number < 0 or slot_number >= len(available_slots):
                return {
                    "message": f"Please choose a number between 1 and {len(available_slots)}:",
                    "session_data": session_data
                }

            selected_slot = available_slots[slot_number]

            # Create or get patient
            patient_id = session_data.get("patient_id")
            if not patient_id:
                # Create new patient
                patient_data = schemas.PatientCreate(
                    name=session_data["patient_name"],
                    phone_number=phone_number,
                    date_of_birth=datetime.fromisoformat(session_data["date_of_birth"]).date(),
                    whatsapp_number=phone_number,
                    whatsapp_opt_in=True,
                    preferred_communication="whatsapp",
                    consent_to_treatment=True,  # Assumed consent for booking
                    hipaa_authorization=True   # Assumed authorization
                )
                patient = crud.create_patient_from_whatsapp(db, patient_data)
                patient_id = patient.id

            # Create appointment with validation
            appointment_start = datetime.combine(
                datetime.fromisoformat(selected_slot["date"]).date(),
                datetime.fromisoformat(selected_slot["time"]).time()
            )
            appointment_end = appointment_start + timedelta(hours=1)  # Default 1 hour

            appointment_data = schemas.AppointmentCreate(
                patient_id=patient_id,
                location_id=selected_slot["location_id"],
                start_time=appointment_start,
                end_time=appointment_end,
                reason=session_data["appointment_reason"],
                appointment_type="consultation"
            )

            # Use the validation function that includes rate limiting
            appointment = crud.create_appointment_with_validation(db, appointment_data, phone_number)

            # Success message
            date_str = appointment_start.strftime("%A, %B %d, %Y")
            time_str = appointment_start.strftime("%I:%M %p")

            response = f"""✅ Appointment confirmed!

            📅 Date: {date_str}
            ⏰ Time: {time_str}
            📍 Location: Dr. Dhingra's Clinic
            👤 Patient: {session_data['patient_name']}
            📝 Reason: {session_data['appointment_reason']}

            Appointment ID: #{appointment.id}

            You'll receive a reminder 1 day before your appointment. If you need to reschedule, please call us or message 'reschedule'.

            Thank you for choosing Dr. Dhingra's Clinic! 🏥"""

            return {
                "message": response,
                "session_data": {"current_flow": "greeting", "appointment_id": appointment.id}
            }

        except HTTPException as e:
            return {
                "message": f"⚠️ {e.detail}",
                "session_data": {"current_flow": "greeting"}
            }
        except (ValueError, KeyError, IndexError):
            return {
                "message": f"Please choose a valid number from the list:",
                "session_data": session_data
            }

    async def handle_appointment_inquiry(self, phone_number: str, message_text: str,
                                    session_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Handle appointment status inquiries"""
        # Get patient by phone
        patient = crud.get_patient_by_phone_hash(db, phone_number)

        if not patient:
            return {
                "message": "I couldn't find any appointments associated with this number. If you have an appointment, please call us at [PHONE_NUMBER].",
                "session_data": {"current_flow": "greeting"}
            }

        # Get upcoming appointments
        upcoming_appointments = crud.get_patient_upcoming_appointments(db, patient.id)

        if not upcoming_appointments:
            response = f"Hi {patient.name}! You don't have any upcoming appointments.\n\nWould you like to book a new appointment? Reply 'book' to get started."
        else:
            response = f"Hi {patient.name}! Here are your upcoming appointments:\n\n"

            for apt in upcoming_appointments:
                date_str = apt.start_time.strftime("%A, %B %d, %Y")
                time_str = apt.start_time.strftime("%I:%M %p")
                response += f"📅 {date_str} at {time_str}\n"
                response += f"📝 Reason: {apt.reason}\n"
                response += f"📍 Location: {apt.location.name}\n"
                response += f"ID: #{apt.id}\n\n"

            response += "Need to reschedule? Reply 'reschedule [appointment ID]' or call us."

        return {
            "message": response,
            "session_data": {"current_flow": "greeting"}
        }

    async def handle_prescription_request(self, phone_number: str, message_text: str,
                                        session_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Handle prescription requests"""
        patient = crud.get_patient_by_phone_hash(db, phone_number)
        
        if not patient:
            return {
                "message": "I need to verify your identity first. Please call us at [PHONE_NUMBER] for prescription requests.",
                "session_data": {"current_flow": "greeting"}
            }
        
        response = f"Hi {patient.name}! For prescription requests, please call us at [PHONE_NUMBER] or visit our clinic.\n\nOur pharmacy hours are: Monday-Friday 9AM-6PM, Saturday 9AM-2PM"
        
        return {
            "message": response,
            "session_data": {"current_flow": "greeting"}
        }

    async def handle_general_inquiry(self, phone_number: str, message_text: str,
                                session_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Handle general inquiries"""
        response = """Here's some general information about Dr. Dhingra's Clinic:

        🏥 **Services:** General medicine, consultations, health checkups
        ⏰ **Hours:** Monday-Friday 9AM-6PM, Saturday 9AM-2PM
        📞 **Phone:** [PHONE_NUMBER]
        📍 **Location:** [CLINIC_ADDRESS]

        For specific medical questions, please book an appointment or call us directly.

        How else can I help you today?"""

        return {
            "message": response,
            "session_data": {"current_flow": "greeting"}
        }


class WhatsAppService:
    """Enhanced WhatsApp service with chatbot capabilities"""

    def __init__(self):
        self.phone_id = settings.whatsapp_phone_id
        self.access_token = settings.whatsapp_access_token

        self.enabled = bool(
            self.phone_id and 
            self.access_token and
            self.phone_id != "your_phone_id" and
            self.access_token != "your_token"
        )

        if self.enabled:
            self.client = WhatsApp(
                phone_id=self.phone_id,
                token=self.access_token
            )
            logger.info("✅ WhatsApp Business API - ENABLED")
        else:
            logger.warning("⚠️ WhatsApp Business API not configured - Service disabled")
            self.client = None

        self.chatbot = WhatsAppChatbot()

    async def send_message(self, phone_number: str, message: str) -> Dict[str, Any]:
        """Send a WhatsApp message"""
        if not self.enabled:
            logger.info(f"📱 [SIMULATED] Would send to {phone_number}: {message}")
            return {"success": True, "message": "Message sent (simulated)", "message_id": "sim_" + str(datetime.now().timestamp())}

        try:
            response = self.client.send_message(
                to=phone_number,
                text=message
            )
            return {"success": True, "message": "Message sent successfully", "message_id": response.id}
        except Exception as e:
            logger.error(f"Failed to send WhatsApp message: {str(e)}")
            return {"success": False, "error": str(e)}

    async def handle_webhook(self, webhook_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Handle incoming WhatsApp webhook"""
        try:
            if "entry" not in webhook_data:
                return {"success": False, "error": "Invalid webhook data"}

            for entry in webhook_data["entry"]:
                if "changes" not in entry:
                    continue

                for change in entry["changes"]:
                    if change.get("field") != "messages":
                        continue

                    value = change.get("value", {})
                    messages = value.get("messages", [])

                    for message in messages:
                        await self.process_incoming_message(message, db)

            return {"success": True, "message": "Webhook processed successfully"}

        except Exception as e:
            logger.error(f"Webhook processing error: {str(e)}")
            return {"success": False, "error": str(e)}

    async def process_incoming_message(self, message_data: Dict[str, Any], db: Session):
        """Process individual incoming message"""
        try:
            phone_number = message_data.get("from")
            message_text = ""

            # Extract message text
            if message_data.get("type") == "text":
                message_text = message_data.get("text", {}).get("body", "")
            elif message_data.get("type") == "button":
                message_text = message_data.get("button", {}).get("text", "")
            elif message_data.get("type") == "interactive":
                interactive = message_data.get("interactive", {})
                if "button_reply" in interactive:
                    message_text = interactive["button_reply"].get("title", "")
                elif "list_reply" in interactive:
                    message_text = interactive["list_reply"].get("title", "")

            if not phone_number or not message_text:
                return

            # Get or create WhatsApp session
            session = crud.get_whatsapp_session(db, phone_number)
            if not session:
                session = crud.create_whatsapp_session(db, phone_number)

            # Process message with chatbot
            response = await self.chatbot.process_message(
                phone_number, message_text, session.context_data or {}, db
            )

            # Update session
            crud.update_whatsapp_session(db, session.id, response["session_data"])

            # Send response
            await self.send_message(phone_number, response["message"])

            # Log communication
            crud.create_communication_log(db, schemas.CommunicationCreate(
                patient_id=session.patient_id,
                communication_type="whatsapp",
                direction="inbound",
                content=message_text
            ))

            crud.create_communication_log(db, schemas.CommunicationCreate(
                patient_id=session.patient_id,
                communication_type="whatsapp",
                direction="outbound",
                content=response["message"]
            ))

        except Exception as e:
            logger.error(f"Message processing error: {str(e)}")