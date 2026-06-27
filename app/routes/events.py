"""
Events Module API
- Health programs
- Fitness challenges
- Daily reminders
"""

from datetime import datetime, date, timedelta
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from database import db
from database.models import HealthProgramEvent, FitnessChallenge, DailyReminder

bp = Blueprint('events', __name__, url_prefix='/api/events')


def _send_event_confirmation(
    reminder: DailyReminder,
    action: str = 'created',
    recipient_email: str | None = None,
    recipient_phone: str | None = None,
    confirmation_channel: str = 'both',
):
    """Send event confirmation via email/SMS with flexible routing."""
    try:
        from app import mail
        from services.notification_service import NotificationService

        channel = (confirmation_channel or 'both').strip().lower()
        if channel not in {'email', 'sms', 'both'}:
            channel = 'both'

        # Flexible routing: use whichever contact is provided.
        has_email = bool((recipient_email or '').strip())
        has_phone = bool((recipient_phone or '').strip())

        user_settings = {
            'email_notifications': False,
            'sms_notifications': False,
        }

        if channel == 'email':
            user_settings['email_notifications'] = has_email
            user_settings['sms_notifications'] = (not has_email) and has_phone
        elif channel == 'sms':
            user_settings['sms_notifications'] = has_phone
            user_settings['email_notifications'] = (not has_phone) and has_email
        else:  # both
            user_settings['email_notifications'] = has_email
            user_settings['sms_notifications'] = has_phone

        notification_service = NotificationService(mail)

        reminder_data = {
            'title': f"Event {action.title()}: {reminder.title}",
            'message': (
                f"Your event has been {action}. "
                f"Type: {reminder.reminder_type}. "
                f"Time: {reminder.reminder_time}."
            ),
            'reminder_type': reminder.reminder_type,
        }

        results = notification_service.send_daily_reminder(
            user_email=recipient_email,
            phone=recipient_phone,
            reminder_data=reminder_data,
            user_settings=user_settings,
        )
        results['routing_channel'] = channel
        return results
    except Exception:
        return {'email': False, 'sms': False, 'routing_channel': 'unknown'}


def _seed_defaults_if_empty(user_id: int):
    """Create starter event/challenge/reminders for first-time users."""
    has_any = (
        HealthProgramEvent.query.filter_by(user_id=user_id).first()
        or FitnessChallenge.query.filter_by(user_id=user_id).first()
        or DailyReminder.query.filter_by(user_id=user_id).first()
    )
    if has_any:
        return

    now = datetime.utcnow()

    programs = [
        HealthProgramEvent(
            user_id=user_id,
            title='Morning Yoga Session',
            description='30-minute guided yoga for flexibility and stress relief.',
            event_type='yoga',
            start_datetime=now + timedelta(days=1, hours=6),
            end_datetime=now + timedelta(days=1, hours=7),
            location='Community Wellness Hall',
            is_virtual=False,
        ),
        HealthProgramEvent(
            user_id=user_id,
            title='Community Health Camp',
            description='Free vitals checkup, BMI screening, and diet counseling.',
            event_type='camp',
            start_datetime=now + timedelta(days=3, hours=9),
            end_datetime=now + timedelta(days=3, hours=13),
            location='City Health Center',
            is_virtual=False,
        ),
        HealthProgramEvent(
            user_id=user_id,
            title='Evening Meditation Program',
            description='Mindfulness and breathing exercises to improve mental wellness.',
            event_type='meditation',
            start_datetime=now + timedelta(days=2, hours=18),
            end_datetime=now + timedelta(days=2, hours=19),
            location='Virtual',
            is_virtual=True,
        ),
        HealthProgramEvent(
            user_id=user_id,
            title='Weekend Zumba Fitness',
            description='Fun cardio dance workout to boost endurance.',
            event_type='fitness',
            start_datetime=now + timedelta(days=4, hours=7),
            end_datetime=now + timedelta(days=4, hours=8),
            location='Community Sports Club',
            is_virtual=False,
        ),
        HealthProgramEvent(
            user_id=user_id,
            title='Cycling for Heart Health',
            description='Group cycling session focused on cardiovascular fitness.',
            event_type='fitness',
            start_datetime=now + timedelta(days=5, hours=6),
            end_datetime=now + timedelta(days=5, hours=7),
            location='Riverside Track',
            is_virtual=False,
        ),
        HealthProgramEvent(
            user_id=user_id,
            title='Strength & Mobility Basics',
            description='Light strength training and mobility drills for all levels.',
            event_type='fitness',
            start_datetime=now + timedelta(days=6, hours=17),
            end_datetime=now + timedelta(days=6, hours=18),
            location='Virtual',
            is_virtual=True,
        ),
        HealthProgramEvent(
            user_id=user_id,
            title='Healthy Cooking Workshop',
            description='Practical nutrition and meal-prep tips for healthy living.',
            event_type='wellness',
            start_datetime=now + timedelta(days=7, hours=11),
            end_datetime=now + timedelta(days=7, hours=12),
            location='City Wellness Center',
            is_virtual=False,
        ),
    ]

    challenges = [
        FitnessChallenge(
            user_id=user_id,
            title='10,000 Steps Challenge',
            description='Hit 10,000 steps daily for better heart health.',
            target_value=10000,
            current_value=0,
            unit='steps',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            is_active=True,
        ),
        FitnessChallenge(
            user_id=user_id,
            title='Hydration Goal Challenge',
            description='Drink at least 8 glasses of water per day.',
            target_value=8,
            current_value=0,
            unit='glasses',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=14),
            is_active=True,
        ),
        FitnessChallenge(
            user_id=user_id,
            title='Meditation Streak Challenge',
            description='Complete a 15-minute meditation daily.',
            target_value=14,
            current_value=0,
            unit='days',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=14),
            is_active=True,
        ),
    ]

    reminders = [
        DailyReminder(
            user_id=user_id,
            title='Morning Walk Reminder',
            reminder_type='steps',
            message='Take a 20-minute walk and start your step goal early.',
            reminder_time='07:00',
            is_enabled=True,
        ),
        DailyReminder(
            user_id=user_id,
            title='Meditation Break',
            reminder_type='meditation',
            message='Take 10 minutes for mindful breathing and reset.',
            reminder_time='20:00',
            is_enabled=True,
        ),
        DailyReminder(
            user_id=user_id,
            title='Hydration Reminder',
            reminder_type='wellness',
            message='Drink a glass of water and stay hydrated.',
            reminder_time='11:00',
            is_enabled=True,
        ),
        DailyReminder(
            user_id=user_id,
            title='Stretch Break',
            reminder_type='fitness',
            message='Stand up, stretch for 5 minutes, and relax your posture.',
            reminder_time='16:00',
            is_enabled=True,
        ),
        DailyReminder(
            user_id=user_id,
            title='Sleep Hygiene Reminder',
            reminder_type='wellness',
            message='Prepare for sleep: reduce screen time and unwind.',
            reminder_time='22:00',
            is_enabled=True,
        ),
    ]

    for item in programs:
        db.session.add(item)
    for item in challenges:
        db.session.add(item)
    for item in reminders:
        db.session.add(item)

    db.session.commit()


def _resolve_confirmation_contacts(data: dict) -> tuple[str, str]:
        """Resolve confirmation delivery targets from the request or current profile."""
        email = (data.get('confirmation_email') or '').strip()
        phone = (data.get('confirmation_phone') or '').strip()

        if not email:
            email = (getattr(current_user, 'email', '') or '').strip()

        if not phone:
            phone = (getattr(current_user, 'phone', '') or '').strip()

        return email, phone


@bp.route('/overview', methods=['GET'])
@login_required
def get_events_overview():
    """Get programs, challenges, and reminders in one call."""
    try:
        _seed_defaults_if_empty(current_user.id)

        programs = HealthProgramEvent.query.filter_by(user_id=current_user.id).order_by(HealthProgramEvent.start_datetime.asc()).all()
        challenges = FitnessChallenge.query.filter_by(user_id=current_user.id).order_by(FitnessChallenge.created_at.desc()).all()
        reminders = DailyReminder.query.filter_by(user_id=current_user.id).order_by(DailyReminder.reminder_time.asc()).all()

        return jsonify({
            'success': True,
            'programs': [p.to_dict() for p in programs],
            'challenges': [c.to_dict() for c in challenges],
            'reminders': [r.to_dict() for r in reminders],
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/programs', methods=['POST'])
@login_required
def create_program():
    """Create a health event/program."""
    try:
        data = request.get_json() or {}

        if not data.get('title') or not data.get('start_datetime'):
            return jsonify({'success': False, 'error': 'title and start_datetime are required'}), 400

        start_dt = datetime.fromisoformat(data['start_datetime'])
        end_dt = datetime.fromisoformat(data['end_datetime']) if data.get('end_datetime') else None

        program = HealthProgramEvent(
            user_id=current_user.id,
            title=data['title'],
            description=data.get('description'),
            event_type=data.get('event_type', 'program'),
            start_datetime=start_dt,
            end_datetime=end_dt,
            location=data.get('location'),
            is_virtual=bool(data.get('is_virtual', False)),
        )

        db.session.add(program)
        db.session.commit()

        return jsonify({'success': True, 'program': program.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/challenges', methods=['POST'])
@login_required
def create_challenge():
    """Create a fitness challenge."""
    try:
        data = request.get_json() or {}
        title = data.get('title', '').strip()
        if not title:
            return jsonify({'success': False, 'error': 'title is required'}), 400

        challenge = FitnessChallenge(
            user_id=current_user.id,
            title=title,
            description=data.get('description', ''),
            target_value=int(data.get('target_value', 10000)),
            current_value=int(data.get('current_value', 0)),
            unit=data.get('unit', 'steps'),
            start_date=date.fromisoformat(data.get('start_date')) if data.get('start_date') else date.today(),
            end_date=date.fromisoformat(data.get('end_date')) if data.get('end_date') else (date.today() + timedelta(days=30)),
            is_active=True,
        )

        db.session.add(challenge)
        db.session.commit()

        return jsonify({'success': True, 'challenge': challenge.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/challenges/<int:challenge_id>/progress', methods=['POST'])
@login_required
def update_challenge_progress(challenge_id):
    """Update progress for a user challenge."""
    try:
        challenge = FitnessChallenge.query.filter_by(id=challenge_id, user_id=current_user.id).first()
        if not challenge:
            return jsonify({'success': False, 'error': 'Challenge not found'}), 404

        data = request.get_json() or {}
        add_value = int(data.get('add_value', 0))
        current_value = data.get('current_value')

        if current_value is not None:
            challenge.current_value = max(0, int(current_value))
        else:
            challenge.current_value = max(0, challenge.current_value + add_value)

        if challenge.current_value >= challenge.target_value:
            challenge.current_value = challenge.target_value
            challenge.is_active = False
            challenge.completed_at = datetime.utcnow()

        db.session.commit()
        return jsonify({'success': True, 'challenge': challenge.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/reminders', methods=['POST'])
@login_required
def create_reminder():
    """Create a daily reminder."""
    try:
        data = request.get_json() or {}
        if not data.get('title'):
            return jsonify({'success': False, 'error': 'title is required'}), 400

        send_confirmation = bool(data.get('send_confirmation', True))
        confirmation_email, confirmation_phone = _resolve_confirmation_contacts(data)
        confirmation_channel = (data.get('confirmation_channel') or 'both').strip().lower()

        if confirmation_channel not in {'email', 'sms', 'both'}:
            return jsonify({
                'success': False,
                'error': 'Invalid confirmation_channel. Use email, sms, or both',
            }), 400

        if send_confirmation and not confirmation_email and not confirmation_phone:
            return jsonify({
                'success': False,
                'error': 'No email or phone number is available for confirmation notifications',
            }), 400

        reminder = DailyReminder(
            user_id=current_user.id,
            title=data['title'],
            reminder_type=data.get('reminder_type', 'wellness'),
            message=data.get('message'),
            reminder_time=data.get('reminder_time', '08:00'),
            days_of_week=data.get('days_of_week', 'Mon,Tue,Wed,Thu,Fri,Sat,Sun'),
            is_enabled=bool(data.get('is_enabled', True)),
        )

        db.session.add(reminder)
        db.session.commit()

        notification_results = (
            _send_event_confirmation(
                reminder,
                action='created',
                recipient_email=confirmation_email,
                recipient_phone=confirmation_phone,
                confirmation_channel=confirmation_channel,
            )
            if send_confirmation
            else {'email': False, 'sms': False}
        )

        return jsonify({
            'success': True,
            'reminder': reminder.to_dict(),
            'confirmation_notification': notification_results,
            'confirmation_channel': confirmation_channel,
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/reminders/upcoming', methods=['GET'])
@login_required
def get_upcoming_reminders():
    """Get upcoming reminders for the current user."""
    try:
        hours_ahead = int(request.args.get('hours', 24))
        
        from services.reminder_scheduler import ReminderScheduler
        scheduler = ReminderScheduler()
        
        upcoming = scheduler.get_upcoming_reminders(current_user.id, hours_ahead)
        
        return jsonify({
            'success': True,
            'upcoming': upcoming,
            'hours_ahead': hours_ahead
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/reminders/check-due', methods=['POST'])
@login_required
def check_due_reminders():
    """Check and send all due reminders (admin/system endpoint)."""
    try:
        # Only allow admins or system to call this
        if current_user.role not in ['admin', 'system']:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        from app import mail
        from services.notification_service import NotificationService
        from services.reminder_scheduler import ReminderScheduler
        
        notification_service = NotificationService(mail)
        scheduler = ReminderScheduler(notification_service)
        
        results = scheduler.check_and_send_due_reminders()
        
        return jsonify({
            'success': True,
            'results': results,
            'count': len(results)
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/reminders/<int:reminder_id>', methods=['PUT'])
@login_required
def update_reminder(reminder_id):
    """Update daily reminder settings."""
    try:
        reminder = DailyReminder.query.filter_by(id=reminder_id, user_id=current_user.id).first()
        if not reminder:
            return jsonify({'success': False, 'error': 'Reminder not found'}), 404

        data = request.get_json() or {}

        send_confirmation = bool(data.get('send_confirmation', True))
        confirmation_email, confirmation_phone = _resolve_confirmation_contacts(data)
        confirmation_channel = (data.get('confirmation_channel') or 'both').strip().lower()

        if confirmation_channel not in {'email', 'sms', 'both'}:
            return jsonify({
                'success': False,
                'error': 'Invalid confirmation_channel. Use email, sms, or both',
            }), 400

        if send_confirmation and not confirmation_email and not confirmation_phone:
            return jsonify({
                'success': False,
                'error': 'No email or phone number is available for confirmation notifications',
            }), 400

        for field in ['title', 'reminder_type', 'message', 'reminder_time', 'days_of_week', 'is_enabled']:
            if field in data:
                setattr(reminder, field, data[field])

        db.session.commit()

        notification_results = (
            _send_event_confirmation(
                reminder,
                action='updated',
                recipient_email=confirmation_email,
                recipient_phone=confirmation_phone,
                confirmation_channel=confirmation_channel,
            )
            if send_confirmation
            else {'email': False, 'sms': False}
        )

        return jsonify({
            'success': True,
            'reminder': reminder.to_dict(),
            'confirmation_notification': notification_results,
            'confirmation_channel': confirmation_channel,
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/reminders/<int:reminder_id>', methods=['DELETE'])
@login_required
def delete_reminder(reminder_id):
    """Delete a daily reminder."""
    try:
        reminder = DailyReminder.query.filter_by(id=reminder_id, user_id=current_user.id).first()
        if not reminder:
            return jsonify({'success': False, 'error': 'Reminder not found'}), 404

        db.session.delete(reminder)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Reminder deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/reminders/<int:reminder_id>/trigger', methods=['POST'])
@login_required
def trigger_reminder(reminder_id):
    """Manually trigger a reminder notification (for testing or immediate sending)."""
    try:
        reminder = DailyReminder.query.filter_by(id=reminder_id, user_id=current_user.id).first()
        if not reminder:
            return jsonify({'success': False, 'error': 'Reminder not found'}), 404
        
        # Import notification service
        from app import mail
        from services.notification_service import NotificationService
        from services.reminder_scheduler import ReminderScheduler
        
        notification_service = NotificationService(mail)
        scheduler = ReminderScheduler(notification_service)
        
        result = scheduler.send_reminder_notification(reminder)
        
        return jsonify(result), 200 if result.get('success') else 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

