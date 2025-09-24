from typing import Optional, Dict, Any, List
import asyncio
import aiofiles
import base64
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
import jinja2
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition


class ModernEmailService:
    def __init__(self):
        sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
        self.sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
        self.sender_email = os.getenv("SENDER_EMAIL", "dummy@thecodingskool.com")
        self.enabled = bool(self.sendgrid_api_key)
        
        if not self.enabled:
            print("⚠️  SENDGRID_API_KEY not found - Email service disabled")
        
        self.sg = SendGridAPIClient(api_key=sendgrid_api_key)
        self.sender_email = os.getenv("SENDER_EMAIL", "noreply@dhingraclinic.com")
        
        # Initialize Jinja2 templates (create template directory if needed)
        template_path = "app/templates/email"
        if not os.path.exists(template_path):
            os.makedirs(template_path, exist_ok=True)
            
        self.template_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_path)
        )
    async def send_prescription_email(self, to_email: str, patient_name: str, 
                                    document_path: str, message: Optional[str] = None):
        """Send prescription via email"""
        if not self.enabled:
            return {"success": False, "message": "Email service not configured"}
        
        print(f"📧 Would send prescription to {to_email} for {patient_name}")
        return {"success": True, "message": "Email sent successfully (simulated)"}
    
    async def send_appointment_reminder(self, to_email: str, patient_name: str, 
                                        appointment_time: str, location: str, doctor_name: str = "Dr. Dhingra"):
        """Send appointment reminder"""
        if not self.enabled:
            return {"success": False, "message": "Email service not configured"}
        
        print(f"📧 Would send reminder to {to_email} for {patient_name}")
        return {"success": True, "message": "Reminder sent successfully (simulated)"}

    
    async def send_templated_email(
        self, 
        to_email: str, 
        template_name: str, 
        context: Dict[str, Any],
        attachments: Optional[List[str]] = None
    ):
        """Modern templated email sending with async file handling"""
        try:
            # Load template asynchronously
            template = self.template_env.get_template(f"{template_name}.html")
            html_content = template.render(**context)
            
            mail = Mail(
                from_email=self.sender_email,
                to_emails=to_email,
                subject=context.get("subject", "Dr. Dhingra's Clinic"),
                html_content=html_content
            )
            
            # Handle attachments asynchronously
            if attachments:
                for attachment_path in attachments:
                    await self._add_attachment(mail, attachment_path)
            
            response = await asyncio.to_thread(self.sg.send, mail)
            return {"success": True, "message": "Email sent successfully"}
            
        except Exception as e:
            return {"success": False, "message": f"Failed to send email: {str(e)}"}
    
    async def _add_attachment(self, mail: Mail, file_path: str):
        """Add attachment to email asynchronously"""
        try:
            async with aiofiles.open(file_path, 'rb') as f:
                data = await f.read()
                
            encoded_file = base64.b64encode(data).decode()
            file_name = Path(file_path).name
            
            # Determine MIME type based on extension
            file_extension = Path(file_path).suffix.lower()
            mime_types = {
                '.pdf': 'application/pdf',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.doc': 'application/msword',
                '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                '.txt': 'text/plain'
            }
            file_type = mime_types.get(file_extension, 'application/octet-stream')
            
            attachment = Attachment(
                FileContent(encoded_file),
                FileName(file_name),
                FileType(file_type),
                Disposition("attachment")
            )
            
            # Initialize attachment list if needed
            if not hasattr(mail, 'attachment') or mail.attachment is None:
                mail.attachment = []
            elif not isinstance(mail.attachment, list):
                mail.attachment = [mail.attachment]
                
            mail.attachment.append(attachment)
            
        except Exception as e:
            print(f"Error adding attachment {file_path}: {str(e)}")

    async def send_prescription_email(self, to_email: str, patient_name: str, 
                                    document_path: str, message: Optional[str] = None):
        """Send prescription via email with attachment using SendGrid"""
        try:
            # Create email content
            subject = f"Prescription for {patient_name} - Dr. Dhingra's Clinic"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background-color: #0B4D6B; color: white; padding: 20px; text-align: center;">
                        <h1 style="margin: 0;">Dr. Dhingra's Clinic</h1>
                        <p style="margin: 5px 0 0 0;">Prescription Delivery</p>
                    </div>
                    
                    <div style="padding: 30px 20px;">
                        <h2 style="color: #0B4D6B;">Dear {patient_name},</h2>
                        
                        <p>We hope this email finds you in good health.</p>
                        
                        <p>Please find your prescription attached to this email. This prescription has been prepared by our medical team specifically for you.</p>
                        
                        {f'<div style="background-color: #E6F3F8; padding: 15px; border-left: 4px solid #2196F3; margin: 20px 0;"><p style="margin: 0;"><strong>Additional Note:</strong><br>{message}</p></div>' if message else ''}
                        
                        <div style="background-color: #FFF3CD; padding: 15px; border: 1px solid #FFE69C; border-radius: 5px; margin: 20px 0;">
                            <p style="margin: 0;"><strong>Important Instructions:</strong></p>
                            <ul style="margin: 10px 0;">
                                <li>Follow the prescribed dosage carefully</li>
                                <li>Complete the full course of medication</li>
                                <li>Contact us if you experience any side effects</li>
                                <li>Keep this prescription for your records</li>
                            </ul>
                        </div>
                        
                        <p>If you have any questions about your prescription or need to schedule a follow-up appointment, please don't hesitate to contact us.</p>
                        
                        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #DDD;">
                            <p><strong>Best regards,</strong><br>
                            Dr. Dhingra's Clinic Team</p>
                            
                            <p style="font-size: 12px; color: #666; margin-top: 20px;">
                                <strong>Contact Information:</strong><br>
                                📞 Phone: [Your Phone Number]<br>
                                📧 Email: [Your Email]<br>
                                📍 Address: [Your Clinic Address]
                            </p>
                        </div>
                    </div>
                    
                    <div style="background-color: #F8F9FA; padding: 15px; text-align: center; font-size: 12px; color: #666;">
                        <p style="margin: 0;">This is an automated message from Dr. Dhingra's Clinic management system.</p>
                        <p style="margin: 5px 0 0 0;">Please do not reply to this email.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Create plain text version
            plain_content = f"""
            Dear {patient_name},
            
            Please find your prescription attached to this email.
            
            {message or ''}
            
            Important Instructions:
            - Follow the prescribed dosage carefully
            - Complete the full course of medication
            - Contact us if you experience any side effects
            - Keep this prescription for your records
            
            Best regards,
            Dr. Dhingra's Clinic Team
            """
            
            # Create the email
            mail = Mail(
                from_email=self.sender_email,
                to_emails=to_email,
                subject=subject,
                plain_text_content=plain_content,
                html_content=html_content
            )
            
            # Add attachment if file exists
            if document_path and os.path.exists(document_path):
                await self._add_attachment(mail, document_path)
            
            # Send email
            response = await asyncio.to_thread(self.sg.send, mail)
            
            if response.status_code in [200, 202]:
                return {"success": True, "message": "Email sent successfully via SendGrid"}
            else:
                return {"success": False, "message": f"SendGrid error: {response.status_code} - {response.body}"}
                
        except Exception as e:
            return {"success": False, "message": f"Failed to send email: {str(e)}"}
    
    async def send_appointment_reminder(self, to_email: str, patient_name: str, 
                                      appointment_time: str, location: str, doctor_name: str = "Dr. Dhingra"):
        """Send appointment reminder email"""
        try:
            subject = f"Appointment Reminder - {appointment_time}"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background-color: #2196F3; color: white; padding: 20px; text-align: center;">
                        <h1 style="margin: 0;">Dr. Dhingra's Clinic</h1>
                        <p style="margin: 5px 0 0 0;">Appointment Reminder</p>
                    </div>
                    
                    <div style="padding: 30px 20px;">
                        <h2 style="color: #0B4D6B;">Dear {patient_name},</h2>
                        
                        <p>This is a friendly reminder about your upcoming appointment.</p>
                        
                        <div style="background-color: #E6F3F8; padding: 20px; border-left: 4px solid #2196F3; margin: 20px 0;">
                            <h3 style="margin: 0 0 10px 0; color: #0B4D6B;">Appointment Details:</h3>
                            <p style="margin: 5px 0;"><strong>Date & Time:</strong> {appointment_time}</p>
                            <p style="margin: 5px 0;"><strong>Location:</strong> {location}</p>
                            <p style="margin: 5px 0;"><strong>Doctor:</strong> {doctor_name}</p>
                        </div>
                        
                        <div style="background-color: #D4EDDA; padding: 15px; border: 1px solid #C3E6CB; border-radius: 5px; margin: 20px 0;">
                            <p style="margin: 0;"><strong>Please remember to:</strong></p>
                            <ul style="margin: 10px 0;">
                                <li>Arrive 15 minutes early</li>
                                <li>Bring your insurance card and ID</li>
                                <li>Bring any previous medical records</li>
                                <li>Prepare a list of current medications</li>
                            </ul>
                        </div>
                        
                        <p>If you need to reschedule or cancel your appointment, please contact us as soon as possible.</p>
                        
                        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #DDD;">
                            <p><strong>Best regards,</strong><br>
                            Dr. Dhingra's Clinic Team</p>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
            
            plain_content = f"""
            Dear {patient_name},
            
            This is a reminder about your upcoming appointment:
            
            Date & Time: {appointment_time}
            Location: {location}
            Doctor: {doctor_name}
            
            Please arrive 15 minutes early and bring your insurance card and ID.
            
            Best regards,
            Dr. Dhingra's Clinic Team
            """
            
            mail = Mail(
                from_email=self.sender_email,
                to_emails=to_email,
                subject=subject,
                plain_text_content=plain_content,
                html_content=html_content
            )
            
            response = await asyncio.to_thread(self.sg.send, mail)
            
            if response.status_code in [200, 202]:
                return {"success": True, "message": "Reminder email sent successfully"}
            else:
                return {"success": False, "message": f"SendGrid error: {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "message": f"Failed to send reminder: {str(e)}"}


# Create singleton instance
email_service = ModernEmailService()
