"""
Module 7: Smart Appointment Scheduling
- Time slot booking
- Conflict prevention
- Appointment tracking
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app import db
from database.models import Appointment, User, DoctorProfile, Alert
from datetime import datetime, timedelta
import json

bp = Blueprint('appointments', __name__, url_prefix='/api/appointments')

@bp.route('/book', methods=['POST'])
@login_required
def book_appointment():
    """Book a new appointment"""
    data = request.get_json()
    
    required_fields = ['doctor_id', 'appointment_date']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    patient_id = data.get('patient_id', current_user.id)
    
    # Check permission
    if current_user.role not in ['admin'] and patient_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Validate doctor exists
    doctor = User.query.filter_by(id=data['doctor_id'], role='doctor').first()
    if not doctor:
        return jsonify({'error': 'Doctor not found'}), 404
    
    # Parse appointment datetime
    try:
        appointment_date = datetime.fromisoformat(data['appointment_date'].replace('Z', '+00:00'))
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use ISO format'}), 400
    
    # Check if appointment is in the future
    if appointment_date < datetime.utcnow():
        return jsonify({'error': 'Appointment must be in the future'}), 400
    
    # Check for conflicts
    duration = data.get('duration_minutes', 30)
    conflict = check_appointment_conflict(
        data['doctor_id'],
        appointment_date,
        duration
    )
    
    if conflict:
        return jsonify({
            'error': 'Time slot not available',
            'conflict': conflict.to_dict()
        }), 409
    
    # Create appointment
    appointment = Appointment(
        patient_id=patient_id,
        doctor_id=data['doctor_id'],
        appointment_date=appointment_date,
        duration_minutes=duration,
        reason=data.get('reason'),
        urgency=data.get('urgency', 'normal'),
        status='scheduled'
    )
    
    db.session.add(appointment)
    db.session.commit()
    
    # Create reminder alert
    create_appointment_reminder(appointment)
    
    return jsonify({
        'message': 'Appointment booked successfully',
        'appointment': appointment.to_dict()
    }), 201


@bp.route('/list', methods=['GET'])
@login_required
def get_appointments():
    """Get appointments list"""
    if current_user.role == 'patient':
        appointments = Appointment.query.filter_by(patient_id=current_user.id)
    elif current_user.role == 'doctor':
        appointments = Appointment.query.filter_by(doctor_id=current_user.id)
    else:  # admin
        appointments = Appointment.query
    
    # Filter by status
    status = request.args.get('status')
    if status:
        appointments = appointments.filter_by(status=status)
    
    # Filter by date range
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if start_date:
        start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        appointments = appointments.filter(Appointment.appointment_date >= start)
    
    if end_date:
        end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        appointments = appointments.filter(Appointment.appointment_date <= end)
    
    appointments = appointments.order_by(Appointment.appointment_date.desc()).all()
    
    return jsonify({
        'appointments': [a.to_dict() for a in appointments]
    }), 200


@bp.route('/<int:appointment_id>', methods=['GET'])
@login_required
def get_appointment(appointment_id):
    """Get appointment details"""
    appointment = Appointment.query.get(appointment_id)
    
    if not appointment:
        return jsonify({'error': 'Appointment not found'}), 404
    
    # Check permission
    if (current_user.role == 'patient' and appointment.patient_id != current_user.id) or \
       (current_user.role == 'doctor' and appointment.doctor_id != current_user.id):
        return jsonify({'error': 'Unauthorized'}), 403
    
    return jsonify({'appointment': appointment.to_dict()}), 200


@bp.route('/<int:appointment_id>', methods=['PUT'])
@login_required
def update_appointment(appointment_id):
    """Update appointment"""
    appointment = Appointment.query.get(appointment_id)
    
    if not appointment:
        return jsonify({'error': 'Appointment not found'}), 404
    
    # Check permission
    if current_user.role not in ['admin'] and \
       appointment.patient_id != current_user.id and \
       appointment.doctor_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    # Update allowed fields
    if 'status' in data:
        appointment.status = data['status']
    
    if 'notes' in data:
        appointment.notes = data['notes']
    
    if 'reason' in data:
        appointment.reason = data['reason']
    
    # Only allow rescheduling if not completed
    if 'appointment_date' in data and appointment.status != 'completed':
        try:
            new_date = datetime.fromisoformat(data['appointment_date'].replace('Z', '+00:00'))
            
            # Check for conflicts
            conflict = check_appointment_conflict(
                appointment.doctor_id,
                new_date,
                appointment.duration_minutes,
                exclude_id=appointment_id
            )
            
            if conflict:
                return jsonify({
                    'error': 'Time slot not available',
                    'conflict': conflict.to_dict()
                }), 409
            
            appointment.appointment_date = new_date
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400
    
    db.session.commit()
    
    return jsonify({
        'message': 'Appointment updated successfully',
        'appointment': appointment.to_dict()
    }), 200


@bp.route('/<int:appointment_id>', methods=['DELETE'])
@login_required
def cancel_appointment(appointment_id):
    """Cancel appointment"""
    appointment = Appointment.query.get(appointment_id)
    
    if not appointment:
        return jsonify({'error': 'Appointment not found'}), 404
    
    # Check permission
    if current_user.role not in ['admin'] and \
       appointment.patient_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    appointment.status = 'cancelled'
    db.session.commit()
    
    return jsonify({'message': 'Appointment cancelled successfully'}), 200


@bp.route('/available-slots', methods=['GET'])
@login_required
def get_available_slots():
    """Get available time slots for a doctor"""
    doctor_id = request.args.get('doctor_id', type=int)
    date_str = request.args.get('date')
    
    if not doctor_id or not date_str:
        return jsonify({'error': 'doctor_id and date required'}), 400
    
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    
    # Get doctor's profile
    doctor = User.query.get(doctor_id)
    if not doctor or doctor.role != 'doctor':
        return jsonify({'error': 'Doctor not found'}), 404
    
    # Get doctor's appointments for the day
    start_datetime = datetime.combine(date, datetime.min.time())
    end_datetime = datetime.combine(date, datetime.max.time())
    
    appointments = Appointment.query.filter(
        Appointment.doctor_id == doctor_id,
        Appointment.appointment_date >= start_datetime,
        Appointment.appointment_date <= end_datetime,
        Appointment.status == 'scheduled'
    ).all()
    
    # Generate available slots (9 AM to 5 PM, 30-minute slots)
    slots = []
    current_time = datetime.combine(date, datetime.min.time().replace(hour=9))
    end_time = datetime.combine(date, datetime.min.time().replace(hour=17))
    
    while current_time < end_time:
        # Check if slot is available
        is_available = True
        for apt in appointments:
            if (current_time >= apt.appointment_date and 
                current_time < apt.appointment_date + timedelta(minutes=apt.duration_minutes)):
                is_available = False
                break
        
        slots.append({
            'time': current_time.isoformat(),
            'available': is_available
        })
        
        current_time += timedelta(minutes=30)
    
    return jsonify({'slots': slots}), 200


@bp.route('/upcoming', methods=['GET'])
@login_required
def get_upcoming_appointments():
    """Get upcoming appointments"""
    if current_user.role == 'patient':
        appointments = Appointment.query.filter(
            Appointment.patient_id == current_user.id,
            Appointment.appointment_date >= datetime.utcnow(),
            Appointment.status == 'scheduled'
        )
    elif current_user.role == 'doctor':
        appointments = Appointment.query.filter(
            Appointment.doctor_id == current_user.id,
            Appointment.appointment_date >= datetime.utcnow(),
            Appointment.status == 'scheduled'
        )
    else:
        appointments = Appointment.query.filter(
            Appointment.appointment_date >= datetime.utcnow(),
            Appointment.status == 'scheduled'
        )
    
    appointments = appointments.order_by(Appointment.appointment_date.asc()).limit(5).all()
    
    return jsonify({
        'appointments': [a.to_dict() for a in appointments]
    }), 200


def check_appointment_conflict(doctor_id, appointment_date, duration_minutes, exclude_id=None):
    """Check if there's a scheduling conflict"""
    end_time = appointment_date + timedelta(minutes=duration_minutes)
    
    query = Appointment.query.filter(
        Appointment.doctor_id == doctor_id,
        Appointment.status == 'scheduled'
    )
    
    if exclude_id:
        query = query.filter(Appointment.id != exclude_id)
    
    # Check for overlapping appointments
    conflicts = query.filter(
        or_(
            and_(
                Appointment.appointment_date <= appointment_date,
                Appointment.appointment_date + timedelta(minutes=Appointment.duration_minutes) > appointment_date
            ),
            and_(
                Appointment.appointment_date < end_time,
                Appointment.appointment_date >= appointment_date
            )
        )
    ).first()
    
    return conflicts


def create_appointment_reminder(appointment):
    """Create reminder alert for appointment"""
    # Create alert 24 hours before appointment
    reminder_alert = Alert(
        patient_id=appointment.patient_id,
        alert_type='appointment_reminder',
        severity='info',
        title='Appointment Reminder',
        message=f"You have an appointment with Dr. {appointment.doctor.full_name} on {appointment.appointment_date.strftime('%Y-%m-%d %H:%M')}."
    )
    
    db.session.add(reminder_alert)
    db.session.commit()
