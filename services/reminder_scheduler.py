"""
Reminder Scheduler Service
Checks for due reminders and sends notifications
"""

from datetime import datetime, timedelta, time as dt_time
from typing import List, Dict, Any
import pytz
from database import db
from database.models import DailyReminder, User, UserSettings
from services.notification_service import NotificationService
from flask import current_app


class ReminderScheduler:
    """Service for scheduling and sending reminder notifications"""
    
    def __init__(self, notification_service: NotificationService = None):
        """Initialize scheduler"""
        self.notification_service = notification_service
    
    def _is_reminder_due(self, reminder: DailyReminder, current_time: datetime) -> bool:
        """
        Check if a reminder is due to be sent
        
        Args:
            reminder: DailyReminder instance
            current_time: Current datetime
            
        Returns:
            True if reminder should be sent
        """
        if not reminder.is_enabled:
            return False
        
        # Check if reminder was already sent today
        if reminder.last_sent_at:
            today_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
            if reminder.last_sent_at >= today_start:
                return False  # Already sent today
        
        # Check day of week
        current_day = current_time.strftime('%a')  # Mon, Tue, etc.
        days_list = reminder.days_of_week.split(',')
        if current_day not in days_list:
            return False
        
        # Check time
        try:
            reminder_hour, reminder_minute = map(int, reminder.reminder_time.split(':'))
            reminder_time = dt_time(reminder_hour, reminder_minute)
            current_time_only = current_time.time()
            
            # Allow a 5-minute window for sending
            time_diff_minutes = (current_time_only.hour * 60 + current_time_only.minute) - \
                              (reminder_time.hour * 60 + reminder_time.minute)
            
            return 0 <= time_diff_minutes <= 5
        except Exception as e:
            print(f"Error parsing reminder time: {e}")
            return False
    
    def send_reminder_notification(self, reminder: DailyReminder) -> Dict[str, Any]:
        """
        Send notification for a specific reminder
        
        Args:
            reminder: DailyReminder instance
            
        Returns:
            Dictionary with notification results
        """
        try:
            user = User.query.get(reminder.user_id)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            settings = user.settings
            if not settings:
                # Create default settings if not exists
                settings = UserSettings(
                    user_id=user.id,
                    email_notifications=True,
                    sms_notifications=False
                )
                db.session.add(settings)
                db.session.commit()
            
            # Prepare reminder data
            reminder_data = {
                'title': reminder.title,
                'message': reminder.message or 'Time for your wellness routine!',
                'reminder_type': reminder.reminder_type
            }
            
            # Prepare user settings
            user_settings = {
                'email_notifications': settings.email_notifications,
                'sms_notifications': settings.sms_notifications
            }
            
            # Send notifications
            if self.notification_service:
                results = self.notification_service.send_daily_reminder(
                    user_email=user.email,
                    phone=user.phone,
                    reminder_data=reminder_data,
                    user_settings=user_settings
                )
            else:
                results = {'email': False, 'sms': False}
                print(f"Notification service not available. Would have sent reminder: {reminder.title}")
            
            # Update reminder tracking
            reminder.last_sent_at = datetime.utcnow()
            reminder.notification_count += 1
            db.session.commit()
            
            return {
                'success': True,
                'reminder_id': reminder.id,
                'user_id': user.id,
                'results': results,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    def check_and_send_due_reminders(self) -> List[Dict[str, Any]]:
        """
        Check all reminders and send notifications for due ones
        
        Returns:
            List of notification results
        """
        try:
            current_time = datetime.utcnow()
            
            # Get all enabled reminders
            reminders = DailyReminder.query.filter_by(is_enabled=True).all()
            
            results = []
            for reminder in reminders:
                if self._is_reminder_due(reminder, current_time):
                    result = self.send_reminder_notification(reminder)
                    results.append(result)
            
            return results
        except Exception as e:
            print(f"Error checking due reminders: {e}")
            return [{'success': False, 'error': str(e)}]
    
    def get_upcoming_reminders(self, user_id: int, hours_ahead: int = 24) -> List[Dict[str, Any]]:
        """
        Get list of upcoming reminders for a user
        
        Args:
            user_id: User ID
            hours_ahead: How many hours ahead to check
            
        Returns:
            List of upcoming reminder info
        """
        try:
            reminders = DailyReminder.query.filter_by(
                user_id=user_id,
                is_enabled=True
            ).order_by(DailyReminder.reminder_time).all()
            
            current_time = datetime.utcnow()
            upcoming = []
            
            for reminder in reminders:
                try:
                    hour, minute = map(int, reminder.reminder_time.split(':'))
                    next_reminder_time = current_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    
                    # If time has passed today, schedule for tomorrow
                    if next_reminder_time <= current_time:
                        next_reminder_time += timedelta(days=1)
                    
                    time_until = (next_reminder_time - current_time).total_seconds() / 3600
                    
                    if time_until <= hours_ahead:
                        upcoming.append({
                            'id': reminder.id,
                            'title': reminder.title,
                            'reminder_time': reminder.reminder_time,
                            'next_trigger': next_reminder_time.isoformat(),
                            'hours_until': round(time_until, 1),
                            'last_sent_at': reminder.last_sent_at.isoformat() if reminder.last_sent_at else None
                        })
                except Exception as e:
                    print(f"Error processing reminder {reminder.id}: {e}")
                    continue
            
            return upcoming
        except Exception as e:
            print(f"Error getting upcoming reminders: {e}")
            return []
