# app/services/whatsapp_service.py - Fixed version with proper imports and rate limiting

import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import logging
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from ..config import get_settings
from ..database import get_db
from .. import models, schemas, crud

logger = logging.getLogger(__name__)


class WhatsAppChatbot:
    # --- MESSAGE IMPROVEMENTS IMPLEMENTED: Enhanced formatting and buttons for user clarity ---
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
            "general_inquiry": self.handle_general_inquiry,
            "view_appointment": self.handle_view_appointment # Added for viewing details
        }

        self.booking_steps = [
            "collect_name",
            "confirm_name",
            "collect_dob",
            "confirm_dob",
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

    # --- Twilio Template Configuration (Using Content SIDs) ---
    TWILIO_TEMPLATE_MAP = {
        # Main Menu (Quick Reply Template) - Used for all greeting scenarios
        "main_menu": "HX6b5090f45b65017fa3daef3891546e9e", # Friendly name: dr_atul_greeting_menu
        
        # Key Utility Notifications
        "session_timeout_notification": "HX531f659e8dc4109c88724fe46495cdb3", 
        "appointment_reminder": "HXdbad01a1384577e2b67ec5189f3e4601", 
        "appointment_cancelled": "HX32e6abae32b235a26a52af860c3d1314",
        "go_back": "HX4bfdf8320c91e8f40095b0a49816a297", 
        
        # Confirmation Flow (Yes/No)
        "confirmation_yes_no": "HXd98dddd02075ca508627e934b3810d3e", # Friendly name: dr_atul_confirmation_yes_no
    }

    def _get_template_message(self, template_key: str, parameters: List[str] = None) -> Dict[str, Any]:
        """Generates a structured dict for sending a Twilio template message.

        Note: Twilio requires an approved template name and optional body parameters.
        """
        if parameters is None:
            parameters = []
            
        template_name = self.TWILIO_TEMPLATE_MAP.get(template_key, template_key)
        
        return {
            "type": "template",
            "name": template_name,
            "language": {"code": "en"}, # Hardcoded language for simplicity
            "components": [{
                "type": "body",
                "parameters": [{"type": "text", "text": p} for p in parameters]
            }]
        }

    def _wrap_message_with_back_button(self, message_text: str) -> str:
        """Wraps a text message with a 'Reply menu to go back.' instruction."""
        if isinstance(message_text, dict): 
             # If it's a dict (an existing interactive message), we just return the text
             return message_text.get("body", {}).get("text", "(Message content)")
             
        return f"{message_text}\n\nReply 'menu' to go back."

    async def process_message(self, phone_number: str, message_text: str, 
                            session_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Process incoming WhatsApp message with rate limiting"""
        
        # --- Session Timeout Check ---
        last_activity_str = session_data.get("__last_activity")
        current_flow = session_data.get("current_flow")
        
        # Only check timeout if not currently in the greeting flow
        if last_activity_str and current_flow != "greeting":
            last_activity = datetime.fromisoformat(last_activity_str)
            # Use UTC now() if last_activity is timezone-aware (which it should be, using isoformat())
            # We use a hardcoded 15 minutes timeout
            timeout_threshold = datetime.now(last_activity.tzinfo) - timedelta(minutes=15)
            
            # *** CORRECTED INDENTATION FOR THIS INNER BLOCK ***
            if last_activity < timeout_threshold:
                logger.info(f"User {phone_number} session timed out ({last_activity_str}). Resetting flow.")
                
                # Reset flow and send notification
                session_data["current_flow"] = "greeting"
                session_data.pop("current_step", None) # Clear any sub-step
                
                # Send the approved template for out-of-session notification
                timeout_template = self._get_template_message(
                    "session_timeout_notification", 
                    parameters=["15 minutes"]
                )
                
                # Return ONLY the template message, ensuring compliance. The user must reply 'hi' to get the menu.
                return {
                    "message": timeout_template,
                    "session_data": session_data
                }
        
        # End Session Timeout Check

        message_lower = message_text.lower().strip()

        # --- Add Reset/Menu Logic START ---
        if message_lower in ["menu", "hi", "hello"]:
            logger.info(f"User {phone_number} requested menu/reset.")
            cleaned_session_data = {
                "patient_id": session_data.get("patient_id"),
                "patient_name": session_data.get("patient_name")
            }
            cleaned_session_data = {k: v for k, v in cleaned_session_data.items() if v is not None}
            cleaned_session_data["current_flow"] = "greeting"
            
            # Call handle_greeting directly to generate the menu
            # Pass a dummy message as handle_greeting might try to parse it initially
            greeting_response = await self.handle_greeting(phone_number, "", cleaned_session_data, db)
            
            # Template messages cannot be modified, so we simply return the template-based greeting response.
            return greeting_response
        # --- Add Reset/Menu Logic END ---
        
        current_flow = session_data.get("current_flow", "greeting")

        if current_flow in self.flows:
            return await self.flows[current_flow](phone_number, message_text, session_data, db)
        else:
            return await self.handle_greeting(phone_number, message_text, session_data, db)

    async def handle_greeting(self, phone_number: str, message_text: str,
                            session_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Handle initial greeting, check patient status, and present contextual menu WITH INTERACTIVE BUTTONS."""
        
        # NOTE: message_text is now an ID like 'view_apt' or 'book_new', not a keyword.
        # If message_text is empty, it's the first greeting, and we should just show the menu.

        next_flow = "greeting"
        next_step = None
        response_message: Any = ""

        # Check if patient exists
        patient = crud.get_patient_by_phone_hash(db, phone_number)

        # --- Define Poster Image URL (replace with your public URL) ---
        # I am leaving this blank as I cannot find a stable public URL.
        # Example: "https.://your-server.com/images/clinic_banner.png"
        CLINIC_IMAGE_URL = ""
        
        # Create the header dictionary ONLY if the URL is set
        header = {
            "type": "image",
            "image": {"link": CLINIC_IMAGE_URL}
        } if CLINIC_IMAGE_URL else None

        if patient:
            # Patient exists, check for upcoming appointments
            upcoming_appointments = crud.get_patient_upcoming_appointments(db, patient.id)

            if upcoming_appointments:
                # --- Scenario C: Existing Patient with Upcoming Appointment ---
                apt = upcoming_appointments[0]
                date_str = apt.start_time.strftime("%A, %B %d")
                time_str = apt.start_time.strftime("%I:%M %p")
                session_data['active_appointment_id'] = apt.id

                # Check if user made a selection
                if message_text == "view_appointment":
                    next_flow = "view_appointment"
                    # The view_appointment handler will take over
                    response_message = "Loading appointment details..."
                elif message_text == "cancel_appointment":
                    next_flow = "cancel_appointment"
                    # The cancel_appointment handler will take over
                    response_message = "Loading cancellation options..."
                elif message_text == "book_new_appointment":
                    next_flow = "appointment_booking"
                    session_data["patient_id"] = patient.id
                    session_data["patient_name"] = patient.name
                    next_step = "collect_reason"
                    response_message = await self.start_appointment_booking(phone_number, session_data, db)
                elif message_text == "main_menu":
                    # User wants the main menu, fall through to Scenario B's menu
                    pass
                else:
                    # No valid selection, or first time seeing menu: show the menu using text options for reliability
                    menu_body = (
                        f"*Hi {patient.name}!* 👋\nWe see you have an upcoming appointment on *{date_str}* at *{time_str}* (ID: `#{apt.id}`).\n\nWhat would you like to do today?"
                        "\n\n*Please reply with the number for your choice:*\n"
                        "1. View Details (Reply: `view_appointment`)"
                        "\n2. Cancel Appointment (Reply: `cancel_appointment`)"
                        "\n3. Book Another (Reply: `book_new_appointment`)"
                    )
                    response_message = menu_body

                # If user selected 'main_menu', we intentionally skip the logic above and land here
                if message_text == "main_menu":
                    next_flow = "greeting"
                    # Show the general menu using the approved Quick Reply template
                    response_message = self._get_template_message("main_menu")

            else:
                # --- Scenario B: Existing Patient, No Upcoming Appointment ---
                
                if message_text == "book_appointment":
                    next_flow = "appointment_booking"
                    session_data["patient_id"] = patient.id
                    session_data["patient_name"] = patient.name
                    next_step = "collect_reason"
                    response_message = await self.start_appointment_booking(phone_number, session_data, db)
                elif message_text == "prescription_request":
                    next_flow = "prescription_request"
                    # This handler will generate its own text response
                    response_message = "Loading prescription info..."
                elif message_text == "general_inquiry":
                    next_flow = "general_inquiry"
                    # This handler will generate its own text response
                    response_message = "Loading general info..."
                else:
                # Show the menu using the approved Quick Reply template
                # The template handles the fixed text and buttons; no dynamic parameters needed here.
                    response_message = self._get_template_message("main_menu")

        else:
            # --- Scenario A: New Number ---
            
            if message_text == "book_appointment_new":
                next_flow = "appointment_booking"
                next_step = "collect_name"
                response_message = await self.start_appointment_booking(phone_number, session_data, db)
            elif message_text == "general_inquiry_new":
                next_flow = "general_inquiry"
                response_message = "Loading general info..."
            elif message_text == "staff_transfer_new":
                response_message = "Okay, I'll connect you with our staff. Please hold on...\n\n*⏰ Our office hours are: *\n• Monday-Friday: 9AM - 6PM\n• Saturday: 9AM - 2PM"
                next_flow = "staff_transfer"
            else:
                # Show the menu using the approved Quick Reply template
                response_message = self._get_template_message("main_menu")

        # Update session data
        session_data["current_flow"] = next_flow
        if next_step:
            session_data["current_step"] = next_step
        else:
            session_data.pop("current_step", None)

        # If the flow logic already generated a specific response (like starting booking or transfer),
        # use that. Otherwise, use the menu response (which is now a dict) constructed earlier.
        final_response = response_message

        # Check if we are moving to a flow that generates its own message
        # If so, we need to call that handler to get the *actual* message to send
        if next_flow == "view_appointment":
            return await self.handle_view_appointment(phone_number, message_text, session_data, db)
        # TODO: Add 'cancel_appointment' handler call when it's created
        elif next_flow == "prescription_request":
            return await self.handle_prescription_request(phone_number, message_text, session_data, db)
        elif next_flow == "general_inquiry":
            return await self.handle_general_inquiry(phone_number, message_text, session_data, db)

        return {
            "message": final_response,
            "session_data": session_data
        }

    async def start_appointment_booking(self, phone_number: str,
                                      session_data: Dict[str, Any], db: Session) -> Dict[str, Any]: # CHANGED return type to Dict[str, Any]
        """Start the appointment booking process with rate limiting"""
        
        # Check appointment booking rate limit (2 per day)
        if not self.rate_limiter.check_appointment_booking_limit(phone_number, daily_limit=2):
            # Wrap booking limit message with back button
            response_message = self._wrap_message_with_back_button(
                "⚠️ You have reached the daily limit for appointment bookings. Please try again tomorrow."
            )
            return {"message": response_message, "session_data": {"current_flow": "greeting"}}
        
        # Check if user already has an active appointment
        if crud.has_active_appointment(db, phone_number):
            # Wrap active appointment message with back button
            response_message = self._wrap_message_with_back_button(
                 "⚠️ You already have an active appointment. Please wait for it to be completed or cancelled before booking a new one."
            )
            return {"message": response_message, "session_data": {"current_flow": "greeting"}}
        
        # Check if patient exists
        patient = crud.get_patient_by_phone_hash(db, phone_number)

        if patient:
            session_data["patient_id"] = patient.id
            session_data["patient_name"] = patient.name
            session_data["current_step"] = "collect_reason"
            # Wrap collect_reason prompt with back button
            response_message = self._wrap_message_with_back_button(
                f"*Hi {patient.name}!* I'll help you book an appointment.\n\nWhat's the *reason* for your visit?"
            )
            return {"message": response_message, "session_data": session_data}
        else:
            session_data["current_step"] = "collect_name"
            # Wrap collect_name prompt with back button
            response_message = self._wrap_message_with_back_button(
                "I'll help you book an appointment! First, I need some information.\n\nWhat's your *full name*?"
            )
            return {"message": response_message, "session_data": session_data}

    async def handle_appointment_booking(self, phone_number: str, message_text: str,
                                       session_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Handle appointment booking flow"""
        current_step = session_data.get("current_step", "collect_name")

        if current_step == "collect_name":
            return await self.collect_name(phone_number, message_text, session_data, db)
        elif current_step == "confirm_name":
            return await self.confirm_name(phone_number, message_text, session_data, db)
        elif current_step == "collect_dob":
            return await self.collect_dob(phone_number, message_text, session_data, db)
        elif current_step == "confirm_dob":
            # This step will be created next
            return await self.confirm_dob(phone_number, message_text, session_data, db)
        elif current_step == "collect_reason":
            return await self.collect_reason(phone_number, message_text, session_data, db)
        elif current_step == "show_available_slots":
            return await self.show_available_slots(phone_number, message_text, session_data, db)
        elif current_step == "confirm_booking":
            return await self.confirm_booking(phone_number, message_text, session_data, db)

        # Fallback error message (with Go Back button)
        error_message = self._wrap_message_with_back_button(
             "😕 I'm sorry, I didn't understand. Let's start over."
        )
        return {
            "message": error_message,
            "session_data": {"current_flow": "greeting"}
        }

    async def confirm_name(self, phone_number: str, message_text: str,
                         session_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Confirms the patient name or re-prompts for input."""
        name = session_data.get("patient_name", "your name")
        
        if message_text == "yes_confirm":
            # Name confirmed, proceed to DOB collection
            session_data["current_step"] = "collect_dob"
            response_message = self._wrap_message_with_back_button(
                f"Great, thanks *{name}*. Now I need your date of birth (DD/MM/YYYY)."
            )
        elif message_text == "no_confirm":
            # Name rejected, re-prompt for name
            session_data["current_step"] = "collect_name"
            response_message = self._wrap_message_with_back_button(
                "Okay, please enter your *full name* again."
            )
        else:
            # Invalid input, re-prompt confirmation using template
            response_message = self._get_template_message(
                "confirmation_yes_no", 
                parameters=["Full Name", name] # Variable 1: Full Name, Variable 2: John Smith
            )
        
        return {
            "message": response_message,
            "session_data": session_data
        }


    async def collect_name(self, phone_number: str, message_text: str,
                        session_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Collect patient name"""
        name = message_text.strip().title()
        if len(name) < 2:
            # Wrap validation error with back button
            error_message = self._wrap_message_with_back_button(
                "⚠️ Please provide your *full name* (at least 2 characters)."
            )
            return {
                "message": error_message,
                "session_data": session_data
            }

        session_data["patient_name"] = name
        session_data["current_step"] = "confirm_name"

        # Send confirmation prompt using text menu for reliability
        confirmation_message = (
            f"You entered: *{name}*. Is this correct?"
            "\n\n*Please reply with the number for your choice:*\n"
            "1. Yes, that is correct (Reply: `yes_name`)"
            "\n2. No, let me re-enter my name (Reply: `no_name`)"
        )
        response_message = self._wrap_message_with_back_button(confirmation_message)
        return {
            "message": response_message,
            "session_data": session_data
        }

    async def confirm_dob(self, phone_number: str, message_text: str,
                         session_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Confirms the patient DOB or re-prompts for input."""
        dob_iso = session_data.get("date_of_birth", datetime.now().isoformat())
        dob_display = datetime.fromisoformat(dob_iso).strftime("%d/%m/%Y")
        
        if message_text == "yes_confirm":
            # DOB confirmed, proceed to Reason collection
            session_data["current_step"] = "collect_reason"
            response_message = self._wrap_message_with_back_button(
                "Perfect! Now, what's the *reason* for your visit? (e.g., General checkup, Specific symptoms)"
            )
        elif message_text == "no_confirm":
            # DOB rejected, re-prompt for DOB
            session_data["current_step"] = "collect_dob"
            response_message = self._wrap_message_with_back_button(
                "Okay, please enter your *Date of Birth* again in the format DD/MM/YYYY:"
            )
        else:
            # Invalid input, re-prompt confirmation using template
            response_message = self._get_template_message(
                "confirmation_yes_no", 
                parameters=["Date of Birth", dob_display] # Variable 1: Date of Birth, Variable 2: DD/MM/YYYY
            )
        
        return {
            "message": response_message,
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
            session_data["current_step"] = "confirm_dob"
            
            # Send confirmation prompt using text menu for reliability
            dob_display = dob.strftime("%d/%m/%Y")
            confirmation_message = (
                f"You entered DOB: *{dob_display}*. Is this correct?"
                "\n\n*Please reply with the number for your choice:*\n"
                "1. Yes, that is correct (Reply: `yes_dob`)"
                "\n2. No, let me re-enter my DOB (Reply: `no_dob`)"
            )
            response_message = self._wrap_message_with_back_button(confirmation_message)
            
            return {
                "message": response_message,
                "session_data": session_data
            }

        except (ValueError, IndexError):
            # Wrap validation error with back button
            error_message = self._wrap_message_with_back_button(
                "⚠️ Please enter a valid date of birth in *DD/MM/YYYY* format (e.g., 15/03/1990):"
            )
            return {
                "message": error_message,
                "session_data": session_data
            }

    async def collect_reason(self, phone_number: str, message_text: str,
                        session_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Collect appointment reason"""
        reason = message_text.strip()
        if len(reason) < 3:
            # Wrap validation error with back button
            error_message = self._wrap_message_with_back_button(
                "⚠️ Please provide a brief *reason* for your visit (at least 3 characters)."
            )
            return {
                "message": error_message,
                "session_data": session_data
            }

        session_data["appointment_reason"] = reason
        session_data["current_step"] = "show_available_slots"

        return await self.show_available_slots(phone_number, "", session_data, db)

    async def show_available_slots(self, phone_number: str, message_text: str,
                                session_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Prepare data for an interactive List Message showing available slots."""
        # Get available slots for the next 7 days
        fetched_slots_data = crud.get_available_appointment_slots(db, days_ahead=7)

        if not fetched_slots_data:
            # Return plain text if no slots found
            return {
                "message": "*Sorry!* 😥 There are no available online booking slots in the next 7 days.\n\nPlease call the clinic at [PHONE_NUMBER] directly to schedule.",
                "session_data": {"current_flow": "greeting"} # Reset flow
            }

        # Limit to 10 slots for WhatsApp List Message constraint
        slots_to_display = fetched_slots_data[:10]

        # Prepare List Message structure
        list_items = []
        slot_details_map = {} # Store full slot details accessible by ID
        for i, slot_data in enumerate(slots_to_display):
            slot_id = f"slot_{i+1}" # Unique ID for the list item payload
            date_obj = slot_data["date"]
            time_obj = slot_data["time"]
            date_str = date_obj.strftime("%a, %b %d") # Short day format
            time_str = time_obj.strftime("%I:%M %p")
            list_items.append({
                "id": slot_id,
                "title": f"{date_str} at {time_str}",
                # "description": f"Location ID: {slot_data['location_id']}" # Optional description
            })
            # Store the data needed for booking later
            slot_details_map[slot_id] = {
                "date": date_obj.isoformat(),
                "time": time_obj.isoformat(),
                "location_id": slot_data["location_id"]
            }
        
        interactive_message = {
            "type": "list",
            "body": "*Available slots – choose below* 👇\n(Tap one of the options to pick your time)",
            "action": {
                "button": "Choose a time slot", # Button text that opens the list
                "sections": [
                    {
                        "title": "Available Times",
                        "rows": list_items
                    }
                ]
            }
        }

        # Store the mapping and set next step
        session_data["slot_details_map"] = slot_details_map
        session_data["current_step"] = "confirm_booking"
        # Remove old available_slots if it exists
        session_data.pop("available_slots", None)

        return {
            "message": interactive_message, # Pass the structured data
            "session_data": session_data
        }

    async def confirm_booking(self, phone_number: str, message_text: str,
                            session_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Confirm appointment booking using slot ID from interactive message reply."""
        # If 'hi', 'hello', or 'menu' is sent, it is handled by the global flow reset in process_message
        try:
            selected_slot_id = message_text.strip() # The reply should be the slot ID, e.g., 'slot_1'
            slot_details_map = session_data.get("slot_details_map", {})

            if selected_slot_id not in slot_details_map:
                logger.warning(f"Invalid slot ID '{selected_slot_id}' received from {phone_number}. Available map keys: {list(slot_details_map.keys())}")
                # Regenerate the list message as the previous one might be outdated or invalid
                await self.show_available_slots(phone_number, "", session_data, db)
                # The show_available_slots function returns the dict, so we can return it directly
                # Make sure the message informs the user to try again
                updated_response = await self.show_available_slots(phone_number, "", session_data, db)
                updated_response["message"]["body"] = "⚠️ Sorry, that wasn't a valid selection. Please choose a time slot again from the list below: 👇"
                return updated_response

            selected_slot_details = slot_details_map[selected_slot_id]

            # Create or get patient
            patient_id = session_data.get("patient_id")
            patient_name = session_data.get("patient_name") # Get name for success message
            if not patient_id:
                # Create new patient
                patient_data = schemas.PatientCreate(
                    name=patient_name,
                    phone_number=phone_number, # Use the raw phone number from WhatsApp
                    date_of_birth=datetime.fromisoformat(session_data["date_of_birth"]).date(),
                    whatsapp_number=phone_number, # Store raw number here too
                    whatsapp_opt_in=True,
                    preferred_communication="whatsapp",
                    consent_to_treatment=True,  # Assumed consent for booking
                    hipaa_authorization=True   # Assumed authorization
                )
                patient = crud.create_patient_from_whatsapp(db, patient_data)
                patient_id = patient.id
            elif not patient_name:
                 # If patient existed but name wasn't in session, fetch it
                 patient = crud.get_patient(db, patient_id=patient_id)
                 patient_name = patient.name if patient else "Valued Patient"

            # Create appointment with validation
            # Combine ISO date string and ISO time string correctly
            appointment_start_str = f"{selected_slot_details['date']}T{selected_slot_details['time'].split('T')[1]}"
            appointment_start = datetime.fromisoformat(appointment_start_str)
            
            # Fetch appointment duration from schedule or use default (e.g., 30 mins)
            # TODO: Need to fetch schedule for the day/location to get actual duration
            duration_minutes = 30 # Defaulting to 30 mins for now
            appointment_end = appointment_start + timedelta(minutes=duration_minutes)

            appointment_data = schemas.AppointmentCreate(
                patient_id=patient_id,
                location_id=selected_slot_details["location_id"],
                start_time=appointment_start,
                end_time=appointment_end,
                reason=session_data["appointment_reason"],
                appointment_type="consultation" # Or determine dynamically?
            )

            # Use the validation function that includes rate limiting
            appointment = crud.create_appointment_with_validation(db, appointment_data, phone_number)

            # Success message using fetched/stored patient name
            date_str = appointment_start.strftime("%A, %B %d, %Y")
            time_str = appointment_start.strftime("%I:%M %p")
            location = crud.get_location(db, location_id=appointment.location_id)
            location_name = location.name if location else "Clinic"

            # Define clinic phone number (replace placeholder)
            clinic_phone = "[PHONE_NUMBER]" # TODO: Replace with actual number if available in settings, or hardcode

            # Format confirmation as a button message with Main Menu option
            confirmation_text = f"""✅ *Appointment Confirmed!*\n\n📅 *Date:* {date_str}\n⏰ *Time:* {time_str}\n📍 *Location:* {location_name}\n👤 *Patient:* {patient_name}\n📝 *Reason:* {session_data['appointment_reason']}\n*Appointment ID:* `#{appointment.id}`\n\nYou'll receive a reminder 1 day before.\nNeed to change it? Reply *Cancel {appointment.id}* or call us at {clinic_phone}.\n\nThank you for choosing *Dr. Dhingra’s Clinic*. 🏥"""
            response = {
                "type": "button",
                "body": {"text": confirmation_text},
                "action": {
                    "buttons": [
                        {"type": "reply", "reply": {"id": "menu", "title": "⬅️ Go Back"}}
                    ]
                }
            }
            
            # Clean up session data after successful booking
            final_session_data = {
                "current_flow": "greeting", 
                # Keep patient_id and name if they exist?
                "patient_id": patient_id,
                "patient_name": patient_name
            }
            # Remove booking-specific keys
            final_session_data.pop('active_appointment_id', None)
            final_session_data.pop('slot_details_map', None)
            final_session_data.pop('appointment_reason', None)
            final_session_data.pop('date_of_birth', None) # If they were a new patient
            final_session_data.pop('current_step', None)

            return {
                "message": response,
                "session_data": final_session_data
            }

        except HTTPException as e:
            logger.error(f"HTTPException during booking confirmation for {phone_number}: {e.detail}")
            # Provide a user-friendly error
            error_message = f"⚠️ *Booking Failed:* {e.detail}"
            if "limit" in e.detail.lower():
                 error_message += " Please try again tomorrow or call the clinic."
            else:
                 error_message += " Please try selecting a slot again or call the clinic."
            # Wrap booking failure message with back button
            error_response = self._wrap_message_with_back_button(error_message)
            return {
                "message": error_response,
                "session_data": {"current_flow": "greeting"} # Reset flow on failure
            }
        except (KeyError, IndexError) as e: # Catch errors if session data is missing
            logger.error(f"Session data error during booking confirmation for {phone_number}: {e}")
            # Wrap session error message with back button
            error_response = self._wrap_message_with_back_button(
                "😕 Sorry, something went wrong with your booking session. Let's start over."
            )
            return {
                "message": error_response,
                "session_data": {"current_flow": "greeting"}
            }
        except Exception as e: # Catch any other unexpected errors
            logger.error(f"Unexpected error during booking confirmation for {phone_number}: {e}", exc_info=True)
            # Wrap unexpected error message with back button
            error_response = self._wrap_message_with_back_button(
                "😕 An unexpected error occurred. Please try booking again later or call the clinic."
            )
            return {
                "message": error_response,
                "session_data": {"current_flow": "greeting"}
            }

    async def handle_view_appointment(self, phone_number: str, message_text: str,
                                    session_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Handle viewing details of an upcoming appointment."""
        # If the user sent a non-menu button ID, but we are in this flow, re-prompt
        if message_text.lower().strip() not in ["view_appointment", "main_menu", "menu", "cancel_appointment"]:
            re_prompt = self._wrap_message_with_back_button("Please use the buttons provided to continue or use the 'Go Back' button to return to the menu.")
            return {"message": re_prompt, "session_data": session_data}

        appointment_id = session_data.get('active_appointment_id')

        if not appointment_id:
            # This shouldn't typically happen if called from the correct flow
            logger.warning(f"handle_view_appointment called for {phone_number} without active_appointment_id in session.")
            # Wrap view appointment error with back button
            error_response = self._wrap_message_with_back_button(
                 "😕 Sorry, I lost track of which appointment you wanted to view. Please start again from the main menu."
            )
            return {
                "message": error_response,
                "session_data": {"current_flow": "greeting"}
            }

        appointment = crud.get_appointment(db, appointment_id=appointment_id)

        if not appointment:
            logger.warning(f"Appointment ID {appointment_id} not found when viewing details for {phone_number}.")
            # Wrap view appointment error with back button
            error_response = self._wrap_message_with_back_button(
                 "😕 Sorry, I couldn't find that appointment. It might have been cancelled. Please check the main menu for options."
            )
            return {
                "message": error_response,
                "session_data": {"current_flow": "greeting"}
            }
        
        # Check if the appointment actually belongs to this user (optional but good practice)
        patient = crud.get_patient_by_phone_hash(db, phone_number)
        if not patient or appointment.patient_id != patient.id:
            logger.error(f"Security check failed: User {phone_number} tried to view appointment {appointment_id} belonging to patient {appointment.patient_id}.")
            # Wrap view appointment error with back button
            error_response = self._wrap_message_with_back_button(
                "😕 Sorry, I couldn't retrieve the details for that appointment."
            )
            return {
                "message": error_response,
                "session_data": {"current_flow": "greeting"}
            }

        # Format the details
        date_str = appointment.start_time.strftime("%A, %B %d, %Y")
        time_str = appointment.start_time.strftime("%I:%M %p")
        location_name = appointment.location.name if appointment.location else "Clinic"
        reason = appointment.reason or "Not specified"

        # Wrap view appointment details with back button
        details_text = f"""🔍 Appointment Details (ID: #{appointment.id}):

        📅 Date: {date_str}
        ⏰ Time: {time_str}
        📍 Location: {location_name}
        👤 Patient: {patient.name}
        📝 Reason: {reason}
        🚦 Status: {appointment.status.capitalize()}

        Reply 'Cancel {appointment.id}' to cancel this appointment."""
        response = self._wrap_message_with_back_button(details_text)

        # Reset flow back to greeting, but keep appointment ID in case they want to cancel next
        session_data["current_flow"] = "greeting"
        # session_data.pop('active_appointment_id', None) # Remove ID after viewing? Or keep for cancel?

        return {
            "message": response,
            "session_data": session_data
        }

    async def handle_appointment_inquiry(self, phone_number: str, message_text: str,
                                    session_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Handle appointment status inquiries"""
        # Get patient by phone
        patient = crud.get_patient_by_phone_hash(db, phone_number)

        if not patient:
            # Wrap inquiry error with back button
            error_response = self._wrap_message_with_back_button(
                "😕 I couldn't find any appointments associated with this number. If you have an appointment, please call us at *[PHONE_NUMBER]*."
            )
            return {
                "message": error_response,
                "session_data": {"current_flow": "greeting"}
            }

        # Get upcoming appointments
        upcoming_appointments = crud.get_patient_upcoming_appointments(db, patient.id)

        if not upcoming_appointments:
            # Wrap inquiry response (no appointments) with back button
            response_text = f"*Hi {patient.name}!* You don't have any upcoming appointments.\n\nWould you like to book a new one? Reply *'book'* to get started."
            response = self._wrap_message_with_back_button(response_text)
        else:
            response = f"Hi {patient.name}! Here are your upcoming appointments:\\n\\n"

            for apt in upcoming_appointments:
                date_str = apt.start_time.strftime("%A, %B %d, %Y")
                time_str = apt.start_time.strftime("%I:%M %p")
                response += f"📅 {date_str} at {time_str}\\n"
                response += f"📝 Reason: {apt.reason}\\n"
                response += f"📍 Location: {apt.location.name}\\n"
                response += f"ID: #{apt.id}\\n\\n"

            response += "Need to change one? Reply *'Cancel [ID]'* or call us at *[PHONE_NUMBER]*."

        # Wrap inquiry response (has appointments) with back button
        final_response = self._wrap_message_with_back_button(response)
        return {
            "message": final_response,
            "session_data": {"current_flow": "greeting"}
        }

    async def handle_prescription_request(self, phone_number: str, message_text: str,
                                        session_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Handle prescription requests"""
        patient = crud.get_patient_by_phone_hash(db, phone_number)
        
        if not patient:
            # Wrap prescription error with back button
            error_response = self._wrap_message_with_back_button(
                "🔒 For your security, I need to verify your identity first. Please call us at *[PHONE_NUMBER]* for prescription requests."
            )
            return {
                "message": error_response,
                "session_data": {"current_flow": "greeting"}
            }
        
        # Wrap prescription response with back button
        response_text = f"*Hi {patient.name}!* For prescription requests, please call us at *[PHONE_NUMBER]* or visit our clinic.\n\n*Pharmacy Hours:*\n• Monday-Friday: 9AM - 6PM\n• Saturday: 9AM - 2PM"
        response = self._wrap_message_with_back_button(response_text)
        
        return {
            "message": response,
            "session_data": {"current_flow": "greeting"}
        }

    async def handle_general_inquiry(self, phone_number: str, message_text: str,
                                session_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Handle general inquiries"""
        # Wrap general inquiry response with back button
        response_text = ("Here's some general information about *Dr. Dhingra's Clinic*:\n\n"
                    "🏥 *Services:* General medicine, consultations, health checkups\n"
                    "⏰ *Hours:* Monday-Friday 9AM-6PM, Saturday 9AM-2PM\n"
                    "📞 *Phone:* [PHONE_NUMBER]\n"
                    "📍 *Location:* [CLINIC_ADDRESS]\n\n"
                    "For specific medical questions, please book an appointment or call us directly.")
        response = self._wrap_message_with_back_button(response_text)

        return {
            "message": response,
            "session_data": {"current_flow": "greeting"}
        }


class WhatsAppService:
    """Twilio-based WhatsApp service"""

    def __init__(self):
        settings = get_settings()
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.from_number = os.getenv("TWILIO_WHATSAPP_FROM")

        self.enabled = bool(self.account_sid and self.auth_token and self.from_number)

        if self.enabled:
            self.client = Client(self.account_sid, self.auth_token)
            logger.info("✅ Twilio WhatsApp Service - ENABLED")
        else:
            logger.warning("⚠️ Twilio WhatsApp not configured - Service disabled")
            self.client = None

        self.chatbot = WhatsAppChatbot()

    async def send_message(self, phone_number: str, message_content: Any) -> Dict[str, Any]:
        """Send a WhatsApp message, handling both text and interactive types."""
        if not self.enabled:
            logger.info(f"📱 [SIMULATED] Would send to {phone_number}: {json.dumps(message_content) if isinstance(message_content, dict) else message_content}")
            return {"success": True, "message": "Message sent (simulated)", "message_id": "sim_" + str(datetime.now().timestamp())}

        # Prepare recipient number format
        if not phone_number.startswith('whatsapp:'):
            to_number = f"whatsapp:{phone_number}"
        else:
            to_number = phone_number

        message_params = {
            "from_": self.from_number,
            "to": to_number
        }

        try:
            if isinstance(message_content, str):
                # Send plain text message
                message_params["body"] = message_content
                logger.debug(f"Sending TEXT message to {to_number}: {message_content}")

            elif isinstance(message_content, dict) and message_content.get("type") == "template":
                # Send template message using ContentSid and ContentVariables (as per Twilio docs)
                template = message_content
                message_params["content_sid"] = template["name"]

                # Extract body parameters correctly
                body_params = []
                components_list = template.get("components", [])
                for component in components_list:
                    if component.get("type") == "body":
                        body_params = [p.get("text") for p in component.get("parameters", []) if p.get("type") == "text"]
                        break
                
                # Use the correct 'content_variables' parameter
                # Twilio expects variables keyed by number, e.g., {"1": "value1", "2": "value2"}
                variables_dict = {str(i+1): param for i, param in enumerate(body_params)}
                # ONLY add content_variables parameter if variables actually exist
                if variables_dict:
                    message_params["content_variables"] = json.dumps(variables_dict)
                    logger.debug(f"Sending TEMPLATE message {template['name']} to {to_number} with ContentVariables: {message_params['content_variables']}")
                else:
                    logger.debug(f"Sending TEMPLATE message {template['name']} to {to_number} with ContentSid ONLY (no variables).")
                
            elif isinstance(message_content, dict) and message_content.get("type") in ["list", "button"]:
                # WARNING: The 'list' and 'button' types rely on non-standard 'persistent_action' and are likely to fail.
                # We keep the code here, but rely on the new text menus instead.
                interactive_data = {
                    "type": message_content["type"],
                    "header": message_content.get("header"), # Optional
                    # Ensure the body text is correctly extracted from the nested dictionary structure (e.g., {"body": {"text": "..."}})
                    "body": {"text": message_content.get("body", {}).get("text", "Please make a selection.")},
                    "footer": message_content.get("footer"), # Optional
                    "action": message_content["action"]
                }
                # persistent_action expects a JSON string within a list, prefixed with 'whatsapp:'
                message_params["persistent_action"] = [f"whatsapp:{json.dumps(interactive_data)}"]
                # Fallback body text is still needed for the main message body parameter
                message_params["body"] = interactive_data["body"]["text"]
                logger.debug(f"Sending INTERACTIVE message via persistent_action to {to_number}: {message_params['persistent_action']}")

            else:
                logger.error(f"Unknown message content type for {to_number}: {type(message_content)}")
                return {"success": False, "error": "Invalid message content type"}

            # Create the message using Twilio client
            sent_message = self.client.messages.create(**message_params)
            
            return {"success": True, "message": "Message sent successfully", "message_id": sent_message.sid}
        
        except TwilioRestException as e:
            logger.error(f"Twilio API Error sending to {to_number}: {e}")
            return {"success": False, "error": f"Twilio Error: {e.status} - {e.msg}"}
        except Exception as e:
            logger.error(f"General Error sending WhatsApp message to {to_number}: {e}", exc_info=True)
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
                    # Get the ID of the clicked button
                    message_text = interactive["button_reply"].get("id", "")
                elif "list_reply" in interactive:
                    # Get the ID of the clicked list item
                    message_text = interactive["list_reply"].get("id", "")

            if not phone_number or not message_text:
                return

            # Get or create WhatsApp session
            session = crud.get_whatsapp_session(db, phone_number)
            if not session:
                session = crud.create_whatsapp_session(db, phone_number)

            # Prepare context data with last activity for timeout check
            context_data = session.context_data or {}
            # Pass the last_activity timestamp (which is automatically updated by the DB/CRUD layer)
            context_data["__last_activity"] = session.last_activity.isoformat()

            # Process message with chatbot
            response = await self.chatbot.process_message(
                phone_number, message_text, context_data, db
            )

            # Update session
            crud.update_whatsapp_session(db, session.id, response["session_data"])

            # Send response
            await self.send_message(phone_number, response["message"])

            # Log communication
            crud.create_communication_log(db, schemas.CommunicationLogCreate(
                patient_id=session.patient_id,
                communication_type="whatsapp",
                direction="inbound",
                content=message_text
            ))

            # Convert dict messages to JSON string for logging
            log_content = json.dumps(response["message"]) if isinstance(response["message"], dict) else response["message"]
            crud.create_communication_log(db, schemas.CommunicationLogCreate(
                patient_id=session.patient_id,
                communication_type="whatsapp",
                direction="outbound",
                content=log_content
            ))

        except Exception as e:
            logger.error(f"Message processing error: {str(e)}")

whatsapp_service = WhatsAppService()