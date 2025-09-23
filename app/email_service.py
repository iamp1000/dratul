import sendgrid
from sendgrid.helpers.mail import Mail
from config import settings # We would add SENDGRID_API_KEY to our config
import logging

logger = logging.getLogger(__name__)

def send_email(to_email: str, subject: str, html_content: str):
    """Sends a transactional email using SendGrid."""
    if "YOUR_KEY" in settings.SENDGRID_API_KEY:
        logger.warning("SendGrid API Key not set. Skipping email.")
        print(f"--- MOCK EMAIL --- \nTO: {to_email}\nSUBJECT: {subject}\n{'-'*20}\n{html_content}")
        return False
    
    sg = sendgrid.SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
    message = Mail(
        from_email='no-reply@drdhingraclinic.com', # A verified sender
        to_emails=to_email,
        subject=subject,
        html_content=html_content
    )
    try:
        response = sg.send(message)
        logger.info(f"Email sent to {to_email}. Status: {response.status_code}")
        return True
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return False

def send_appointment_confirmation_email(patient_email: str, patient_name: str, appointment_time: str, location: str):
    """Sends a standardized appointment confirmation email."""
    subject = f"Appointment Confirmed: {appointment_time}"
    html_content = f"""
    <h2>Appointment Confirmation</h2>
    <p>Dear {patient_name},</p>
    <p>This email confirms your appointment with Dr. Atul Dhingra at the <strong>{location}</strong> on:</p>
    <h3>{appointment_time}</h3>
    <p>We look forward to seeing you.</p>
    """
    return send_email(patient_email, subject, html_content)
