from pywa import WhatsApp
from typing import Optional
import os
from ..config import settings

class WhatsAppService:
    def __init__(self):
        # Initialize WhatsApp client
        self.wa = WhatsApp(
            phone_id=settings.whatsapp_phone_id,
            token=settings.whatsapp_access_token
        )
        
        # SET THE ENABLED FLAG - THIS WAS MISSING!
        self.enabled = bool(settings.whatsapp_phone_id and 
                           settings.whatsapp_access_token and 
                           settings.whatsapp_phone_id != "your_phone_id")
        
        if not self.enabled:
            print("⚠️ WhatsApp not configured - Service disabled")
        else:
            print("✅ WhatsApp Service - ENABLED")
    
    async def send_prescription(self, to_number: str, patient_name: str, document_path: str, message: Optional[str] = None):
        """Send prescription to patient via WhatsApp"""
        if not self.enabled:
            print(f"📱 [SIMULATED] Would send prescription to {to_number} for {patient_name}")
            return {"success": True, "message": "WhatsApp sent successfully (simulated)"}
        
        try:
            # Send document
            self.wa.send_document(
                to=to_number,
                document=document_path,
                caption=f"Hi {patient_name}, here's your prescription from the clinic. {message or ''}"
            )
            return {"success": True, "message": "Prescription sent successfully"}
        except Exception as e:
            return {"success": False, "message": f"Failed to send: {str(e)}"}
    
    async def send_appointment_reminder(self, to_number: str, patient_name: str, appointment_time: str, location: str):
        """Send appointment reminder"""
        if not self.enabled:
            print(f"📱 [SIMULATED] Would send reminder to {to_number} for {patient_name}")
            return {"success": True, "message": "WhatsApp sent successfully (simulated)"}
        
        try:
            message = f"Hi {patient_name}, this is a reminder for your appointment on {appointment_time} at {location}."
            
            self.wa.send_message(
                to=to_number,
                text=message
            )
            return {"success": True}
        except Exception as e:
            return {"success": False, "message": str(e)}

whatsapp_service = WhatsAppService()
