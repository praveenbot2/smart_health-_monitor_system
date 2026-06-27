"""
Notification Service
Handle various types of notifications (email, SMS, push, etc.)
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
from flask_mail import Message
from flask import current_app
import os
import importlib


class NotificationService:
    """Service for sending notifications"""
    
    def __init__(self, mail_instance=None):
        """Initialize notification service"""
        self.mail = mail_instance
        # SMS configuration
        self.sms_enabled = os.getenv('SMS_ENABLED', 'false').lower() == 'true'
        self.sms_provider = os.getenv('SMS_PROVIDER', 'twilio').lower()
        self.sms_api_key = os.getenv('SMS_API_KEY')
        self.sms_sender = os.getenv('SMS_SENDER', 'SmartHealth')
        self.twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.twilio_phone_number = os.getenv('TWILIO_PHONE_NUMBER')
    
    def send_email(self, recipient: str, subject: str, body: str, html: str = None) -> bool:
        """
        Send email notification
        
        Args:
            recipient: Email address
            subject: Email subject
            body: Plain text body
            html: Optional HTML body
            
        Returns:
            True if successful, False otherwise
        """
        if not recipient:
            print("Email notification skipped: recipient email is missing")
            return False

        mail_username = os.getenv('MAIL_USERNAME', '')
        mail_password = os.getenv('MAIL_PASSWORD', '')
        placeholder_values = {'', 'your-email@gmail.com', 'your-app-password'}
        if mail_username in placeholder_values or mail_password in placeholder_values:
            print(
                "Email notification (not sent - mail credentials not configured). "
                "Set MAIL_USERNAME and MAIL_PASSWORD in .env (use Gmail App Password if using Gmail)."
            )
            return False

        if not self.mail:
            print(f"Email notification (not sent - mail not configured): {subject} to {recipient}")
            return False
        
        try:
            msg = Message(
                subject=subject,
                recipients=[recipient],
                body=body,
                html=html
            )
            self.mail.send(msg)
            return True
        except Exception as e:
            print(f"Error sending email: {e}")
            if '535' in str(e) or 'BadCredentials' in str(e):
                print(
                    "Email auth failed (SMTP 535). "
                    "If using Gmail, enable 2-Step Verification and use an App Password in MAIL_PASSWORD."
                )
            return False
    
    def send_alert_notification(self, user_email: str, alert_type: str, message: str, severity: str) -> bool:
        """
        Send notification for a health alert
        
        Args:
            user_email: User email address
            alert_type: Type of alert
            message: Alert message
            severity: Severity level
            
        Returns:
            True if successful
        """
        subject = f"Health Alert: {alert_type.replace('_', ' ').title()}"
        
        body = f"""
Dear User,

A health alert has been detected:

Alert Type: {alert_type}
Severity: {severity.upper()}
Message: {message}
Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

Please review your health dashboard for more details.

Best regards,
Smart Health Monitor Team
        """
        
        html = f"""
<html>
<body>
    <h2>Health Alert Notification</h2>
    <p>A health alert has been detected:</p>
    <ul>
        <li><strong>Alert Type:</strong> {alert_type}</li>
        <li><strong>Severity:</strong> <span style="color: {'red' if severity == 'high' or severity == 'critical' else 'orange'}">
            {severity.upper()}</span></li>
        <li><strong>Message:</strong> {message}</li>
        <li><strong>Time:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</li>
    </ul>
    <p>Please review your health dashboard for more details.</p>
    <p>Best regards,<br>Smart Health Monitor Team</p>
</body>
</html>
        """
        
        return self.send_email(user_email, subject, body, html)
    
    def send_appointment_reminder(self, user_email: str, appointment_data: Dict) -> bool:
        """
        Send appointment reminder notification
        
        Args:
            user_email: User email address
            appointment_data: Dictionary with appointment details
            
        Returns:
            True if successful
        """
        subject = "Appointment Reminder"
        
        body = f"""
Dear User,

This is a reminder for your upcoming appointment:

Doctor: {appointment_data.get('doctor_name', 'N/A')}
Date: {appointment_data.get('date', 'N/A')}
Time: {appointment_data.get('time', 'N/A')}
Reason: {appointment_data.get('reason', 'General consultation')}

Please arrive 15 minutes early.

Best regards,
Smart Health Monitor Team
        """
        
        return self.send_email(user_email, subject, body)
    
    def send_sms(self, phone_number: str, message: str) -> bool:
        """
        Send SMS notification
        
        Args:
            phone_number: Recipient phone number
            message: SMS message text
            
        Returns:
            True if successful, False otherwise
        """
        if not phone_number:
            return False

        if not self.sms_enabled:
            print(
                "SMS notification (not sent - SMS not configured). "
                "Set SMS_ENABLED=true and Twilio credentials in .env. "
                f"Message preview: {message[:50]}... to {phone_number}"
            )
            return False
        
        try:
            if self.sms_provider == 'twilio':
                if not all([self.twilio_account_sid, self.twilio_auth_token, self.twilio_phone_number]):
                    print(
                        "SMS notification (not sent - missing Twilio credentials). "
                        "Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_PHONE_NUMBER in .env"
                    )
                    return False

                try:
                    twilio_rest = importlib.import_module('twilio.rest')
                    Client = getattr(twilio_rest, 'Client')
                except Exception:
                    print("SMS notification (not sent - twilio package not installed)")
                    return False

                client = Client(self.twilio_account_sid, self.twilio_auth_token)
                client.messages.create(
                    body=message,
                    from_=self.twilio_phone_number,
                    to=phone_number,
                )

                print(f"SMS notification sent via Twilio to {phone_number}")
                return True

            print(f"SMS notification (not sent - unsupported provider '{self.sms_provider}')")
            return False
        except Exception as e:
            print(f"Error sending SMS: {e}")
            return False
    
    def send_daily_reminder(self, user_email: str, phone: Optional[str], reminder_data: Dict, user_settings: Dict) -> Dict[str, bool]:
        """
        Send daily reminder notification via email and/or SMS
        
        Args:
            user_email: User email address
            phone: User phone number (optional)
            reminder_data: Dictionary with reminder details
            user_settings: Dictionary with user notification preferences
            
        Returns:
            Dictionary with success status for each channel
        """
        title = reminder_data.get('title', 'Daily Reminder')
        message = reminder_data.get('message', '')
        reminder_type = reminder_data.get('reminder_type', 'wellness')
        
        results = {'email': False, 'sms': False}
        
        # Send email notification if enabled
        if user_settings.get('email_notifications', True):
            subject = f"🔔 {title}"
            
            body = f"""
Hello!

This is your daily reminder:

{title}
Type: {reminder_type.title()}

{message}

Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

Stay healthy!
Smart Health Monitor Team
            """
            
            html = f"""
<html>
<body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px; background: linear-gradient(135deg, #fff 0%, #fff4fa 100%);">
        <div style="background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
            <h2 style="color: #e24582; margin-top: 0;">🔔 {title}</h2>
            <p style="background: #fff8fc; padding: 15px; border-left: 4px solid #ff7eb3; border-radius: 4px; margin: 20px 0;">
                <strong>{message}</strong>
            </p>
            <div style="color: #666; font-size: 14px; margin-top: 20px;">
                <p><strong>Type:</strong> {reminder_type.title()}</p>
                <p><strong>Time:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
            </div>
            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #f0f0f0; color: #999; font-size: 12px;">
                <p>Stay healthy! 💪<br>Smart Health Monitor Team</p>
            </div>
        </div>
    </div>
</body>
</html>
            """
            
            results['email'] = self.send_email(user_email, subject, body, html)
        
        # Send SMS notification if enabled and phone available
        if user_settings.get('sms_notifications', False) and phone:
            sms_text = f"{title}\n\n{message}\n\nStay healthy! - Smart Health Monitor"
            results['sms'] = self.send_sms(phone, sms_text)
        
        return results
    
    def send_report_notification(self, user_email: str, report_title: str, report_link: str = None) -> bool:
        """
        Send notification when a new report is available
        
        Args:
            user_email: User email address
            report_title: Title of the report
            report_link: Optional link to access the report
            
        Returns:
            True if successful
        """
        subject = "New Health Report Available"
        
        body = f"""
Dear User,

A new health report is now available:

Report: {report_title}
Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

{f'View report: {report_link}' if report_link else 'Login to your dashboard to view the report.'}

Best regards,
Smart Health Monitor Team
        """
        
        return self.send_email(user_email, subject, body)
    
    def send_welcome_email(self, user_email: str, username: str) -> bool:
        """
        Send welcome email to new users
        
        Args:
            user_email: User email address
            username: Username
            
        Returns:
            True if successful
        """
        subject = "Welcome to Smart Health Monitor"
        
        body = f"""
Dear {username},

Welcome to Smart Health Monitor!

Your account has been successfully created. You can now:
- Monitor your vital signs in real-time
- Track your health scores
- Get AI-powered health predictions
- Schedule appointments with doctors
- Receive personalized health recommendations

Login to your dashboard to get started!

Best regards,
Smart Health Monitor Team
        """
        
        html = f"""
<html>
<body>
    <h2>Welcome to Smart Health Monitor!</h2>
    <p>Dear {username},</p>
    <p>Your account has been successfully created. You can now:</p>
    <ul>
        <li>Monitor your vital signs in real-time</li>
        <li>Track your health scores</li>
        <li>Get AI-powered health predictions</li>
        <li>Schedule appointments with doctors</li>
        <li>Receive personalized health recommendations</li>
    </ul>
    <p>Login to your dashboard to get started!</p>
    <p>Best regards,<br>Smart Health Monitor Team</p>
</body>
</html>
        """
        
        return self.send_email(user_email, subject, body, html)
    
    def send_password_reset(self, user_email: str, reset_token: str, reset_link: str) -> bool:
        """
        Send password reset notification
        
        Args:
            user_email: User email address
            reset_token: Password reset token
            reset_link: Link to reset password
            
        Returns:
            True if successful
        """
        subject = "Password Reset Request"
        
        body = f"""
Dear User,

A password reset has been requested for your account.

Click the link below to reset your password:
{reset_link}

This link will expire in 1 hour.

If you did not request this, please ignore this email.

Best regards,
Smart Health Monitor Team
        """
        
        return self.send_email(user_email, subject, body)
    
    @staticmethod
    def send_push_notification(user_id: int, title: str, message: str) -> bool:
        """
        Send push notification (placeholder for future implementation)
        
        Args:
            user_id: User ID
            title: Notification title
            message: Notification message
            
        Returns:
            True if successful
        """
        # This would integrate with a push notification service
        # like Firebase Cloud Messaging, OneSignal, etc.
        print(f"Push notification to user {user_id}: {title} - {message}")
        return True


# Singleton instance
_notification_service = None

def get_notification_service(mail_instance=None):
    """Get or create notification service instance"""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService(mail_instance)
    return _notification_service
