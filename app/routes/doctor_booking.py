"""
Doctor Booking System with Slot Management
- View available doctors with specializations
- Check available appointment slots
- Book appointments
- Cancel bookings
- Manage doctor schedules
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app import db
from database.models import User, DoctorProfile, Appointment, HealthPrediction, Alert
from datetime import datetime, timedelta
import json

bp = Blueprint('doctor_booking', __name__, url_prefix='/api/doctor-booking')


@bp.route('/doctors', methods=['GET'])
@login_required
def list_doctors():
    """
    Get list of available doctors
    
    Query params:
    - specialization: filter by specialty (optional)
    - rating_min: minimum rating (optional)
    """
    try:
        specialization = request.args.get('specialization', '').lower()
        rating_min = request.args.get('rating_min', 0, type=float)
        
        query = User.query.filter_by(role='doctor', is_active=True)
        doctors = query.all()
        
        doctors_list = []
        for doctor in doctors:
            if hasattr(doctor, 'doctor_profile') and doctor.doctor_profile:
                profile = doctor.doctor_profile
                
                # Filter by specialization
                if specialization and profile.specialization.lower() != specialization:
                    continue
                
                # Filter by rating
                if profile.rating < rating_min:
                    continue
                
                doctor_data = {
                    'id': doctor.id,
                    'name': doctor.full_name,
                    'email': doctor.email,
                    'phone': doctor.phone,
                    'specialization': profile.specialization,
                    'qualification': profile.qualification,
                    'experience_years': profile.experience_years,
                    'consultation_fee': profile.consultation_fee,
                    'rating': profile.rating,
                    'total_consultations': profile.total_consultations,
                    'available_days': profile.available_days,
                    'available_time_start': profile.available_time_start.isoformat() if profile.available_time_start else None,
                    'available_time_end': profile.available_time_end.isoformat() if profile.available_time_end else None
                }
                doctors_list.append(doctor_data)
        
        return jsonify({
            'doctors': doctors_list,
            'count': len(doctors_list),
            'success': True
        }), 200
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@bp.route('/doctors/<int:doctor_id>', methods=['GET'])
@login_required
def get_doctor_details(doctor_id):
    """Get detailed doctor information"""
    try:
        doctor = User.query.filter_by(id=doctor_id, role='doctor').first()
        
        if not doctor or not doctor.is_active:
            return jsonify({'error': 'Doctor not found', 'success': False}), 404
        
        profile = doctor.doctor_profile
        if not profile:
            return jsonify({'error': 'Doctor profile not found', 'success': False}), 404
        
        doctor_data = {
            'id': doctor.id,
            'name': doctor.full_name,
            'email': doctor.email,
            'phone': doctor.phone,
            'address': doctor.address,
            'specialization': profile.specialization,
            'qualification': profile.qualification,
            'license_number': profile.license_number,
            'experience_years': profile.experience_years,
            'consultation_fee': profile.consultation_fee,
            'rating': profile.rating,
            'total_consultations': profile.total_consultations,
            'available_days': profile.available_days,
            'available_time': {
                'start': profile.available_time_start.isoformat() if profile.available_time_start else None,
                'end': profile.available_time_end.isoformat() if profile.available_time_end else None
            }
        }
        
        return jsonify({
            'doctor': doctor_data,
            'success': True
        }), 200
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@bp.route('/doctors/recommend', methods=['GET'])
@login_required
def get_recommended_doctors():
    """
    Get intelligently recommended doctors based on patient's health risk
    """
    try:
        # Get patient's latest health risk
        latest_prediction = HealthPrediction.query.filter_by(patient_id=current_user.id).order_by(
            HealthPrediction.predicted_at.desc()
        ).first()
        
        # Map risk levels to recommended specializations
        specialization_map = {
            'low': ['General Practitioner', 'Preventive Medicine'],
            'medium': ['Cardiologist', 'Internist', 'General Practitioner'],
            'high': ['Cardiologist', 'Internist', 'Endocrinologist', 'Pulmonologist'],
            'critical': ['Cardiologist', 'Internist', 'Emergency Medicine']
        }
        
        risk_level = latest_prediction.risk_level if latest_prediction else 'medium'
        recommended_specs = specialization_map.get(risk_level.lower(), ['General Practitioner'])
        
        # Get doctors with recommended specializations
        doctors_list = []
        for spec in recommended_specs:
            doctors = User.query.filter_by(role='doctor', is_active=True).all()
            for doctor in doctors:
                if hasattr(doctor, 'doctor_profile') and doctor.doctor_profile:
                    if doctor.doctor_profile.specialization == spec:
                        doctor_data = {
                            'id': doctor.id,
                            'name': doctor.full_name,
                            'specialization': doctor.doctor_profile.specialization,
                            'experience_years': doctor.doctor_profile.experience_years,
                            'consultation_fee': doctor.doctor_profile.consultation_fee,
                            'rating': doctor.doctor_profile.rating,
                            'recommendation_reason': f'Recommended for your {risk_level} risk profile'
                        }
                        if doctor_data not in doctors_list:
                            doctors_list.append(doctor_data)
        
        return jsonify({
            'patient_risk_level': risk_level,
            'recommended_doctors': doctors_list,
            'success': True
        }), 200
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@bp.route('/slots/<int:doctor_id>', methods=['GET'])
@login_required
def get_available_slots(doctor_id):
    """
    Get available appointment slots for a doctor
    
    Query params:
    - date: specific date in YYYY-MM-DD format (optional, defaults to next 7 days)
    - days: number of days to show slots for
    """
    try:
        doctor = User.query.filter_by(id=doctor_id, role='doctor').first()
        if not doctor or not doctor.is_active:
            return jsonify({'error': 'Doctor not found', 'success': False}), 404
        
        profile = doctor.doctor_profile
        if not profile:
            return jsonify({'error': 'Doctor profile not found', 'success': False}), 404
        
        # Get date parameters
        start_date_str = request.args.get('date')
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        else:
            start_date = datetime.now().date()
        
        days = request.args.get('days', 7, type=int)
        
        # Generate slots
        slots = []
        available_days = json.loads(profile.available_days) if isinstance(profile.available_days, str) else profile.available_days or []
        
        time_start = profile.available_time_start or datetime.strptime('09:00', '%H:%M').time()
        time_end = profile.available_time_end or datetime.strptime('17:00', '%H:%M').time()
        
        # Slot duration (30 minutes)
        slot_duration = 30
        
        for i in range(days):
            current_date = start_date + timedelta(days=i)
            
            # Check if doctor works on this day
            day_name = current_date.strftime('%A')
            if available_days and day_name not in available_days:
                continue
            
            # Generate time slots
            current_time = datetime.combine(current_date, time_start)
            end_time = datetime.combine(current_date, time_end)
            
            while current_time < end_time:
                # Check if slot is already booked
                existing_appointment = Appointment.query.filter_by(
                    doctor_id=doctor_id,
                    status='scheduled'
                ).filter(
                    Appointment.appointment_date == current_time
                ).first()
                
                if not existing_appointment:
                    slots.append({
                        'datetime': current_time.isoformat(),
                        'date': current_date.isoformat(),
                        'time': current_time.strftime('%H:%M'),
                        'available': True,
                        'fee': profile.consultation_fee
                    })
                
                current_time += timedelta(minutes=slot_duration)
        
        return jsonify({
            'doctor_id': doctor_id,
            'doctor_name': doctor.full_name,
            'slots': slots,
            'count': len(slots),
            'success': True
        }), 200
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@bp.route('/book', methods=['POST'])
@login_required
def book_appointment():
    """
    Book an appointment
    
    Expected JSON:
    {
        "doctor_id": 5,
        "appointment_datetime": "2025-03-15T10:30:00",
        "reason": "Health checkup",
        "urgency": "normal"  # normal, urgent, emergency
    }
    """
    try:
        data = request.get_json()
        doctor_id = data.get('doctor_id')
        appointment_datetime_str = data.get('appointment_datetime')
        reason = data.get('reason', 'Consultation')
        urgency = data.get('urgency', 'normal')
        
        if not doctor_id or not appointment_datetime_str:
            return jsonify({'error': 'Doctor ID and appointment datetime required', 'success': False}), 400
        
        # Validate doctor exists
        doctor = User.query.filter_by(id=doctor_id, role='doctor').first()
        if not doctor or not doctor.is_active:
            return jsonify({'error': 'Doctor not found', 'success': False}), 404
        
        # Parse appointment datetime
        appointment_dt = datetime.fromisoformat(appointment_datetime_str)
        
        # Check if slot is available
        existing = Appointment.query.filter_by(
            doctor_id=doctor_id,
            appointment_date=appointment_dt,
            status='scheduled'
        ).first()
        
        if existing:
            return jsonify({'error': 'Slot already booked', 'success': False}), 409
        
        # Create appointment
        appointment = Appointment(
            patient_id=current_user.id,
            doctor_id=doctor_id,
            appointment_date=appointment_dt,
            duration_minutes=30,
            status='scheduled',
            reason=reason,
            urgency=urgency,
            created_at=datetime.utcnow()
        )
        
        db.session.add(appointment)
        db.session.commit()
        
        # Create reminder alert
        alert = Alert(
            patient_id=current_user.id,
            alert_type='appointment_scheduled',
            severity='info',
            title='Appointment Confirmed',
            message=f'Your appointment with {doctor.full_name} on {appointment_dt.strftime("%Y-%m-%d %H:%M")} has been confirmed.'
        )
        db.session.add(alert)
        db.session.commit()
        
        return jsonify({
            'message': 'Appointment booked successfully',
            'appointment_id': appointment.id,
            'appointment': {
                'id': appointment.id,
                'doctor_name': doctor.full_name,
                'appointment_date': appointment_dt.isoformat(),
                'reason': reason,
                'status': 'scheduled'
            },
            'success': True
        }), 201
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@bp.route('/appointments', methods=['GET'])
@login_required
def get_appointments():
    """
    Get user's appointments
    
    Query params:
    - status: filter by status (scheduled, completed, cancelled)
    - future_only: boolean, only future appointments
    """
    try:
        status = request.args.get('status', '')
        future_only = request.args.get('future_only', 'true').lower() == 'true'
        
        query = Appointment.query.filter_by(patient_id=current_user.id)
        
        if status:
            query = query.filter_by(status=status)
        
        if future_only:
            query = query.filter(Appointment.appointment_date >= datetime.utcnow())
        
        appointments = query.order_by(Appointment.appointment_date.desc()).all()
        
        appointments_data = []
        for appt in appointments:
            doctor = User.query.get(appt.doctor_id)
            appointments_data.append({
                'id': appt.id,
                'doctor_name': doctor.full_name if doctor else 'Unknown',
                'doctor_specialization': doctor.doctor_profile.specialization if doctor and hasattr(doctor, 'doctor_profile') else None,
                'appointment_date': appt.appointment_date.isoformat(),
                'reason': appt.reason,
                'status': appt.status,
                'urgency': appt.urgency,
                'created_at': appt.created_at.isoformat()
            })
        
        return jsonify({
            'appointments': appointments_data,
            'count': len(appointments_data),
            'success': True
        }), 200
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@bp.route('/appointments/<int:appointment_id>', methods=['GET'])
@login_required
def get_appointment_details(appointment_id):
    """Get detailed appointment information"""
    try:
        appointment = Appointment.query.get(appointment_id)
        
        if not appointment:
            return jsonify({'error': 'Appointment not found', 'success': False}), 404
        
        if appointment.patient_id != current_user.id:
            return jsonify({'error': 'Unauthorized', 'success': False}), 403
        
        doctor = User.query.get(appointment.doctor_id)
        
        return jsonify({
            'appointment': {
                'id': appointment.id,
                'doctor_name': doctor.full_name if doctor else 'Unknown',
                'doctor_phone': doctor.phone if doctor else None,
                'doctor_specialization': doctor.doctor_profile.specialization if doctor and hasattr(doctor, 'doctor_profile') else None,
                'appointment_date': appointment.appointment_date.isoformat(),
                'duration_minutes': appointment.duration_minutes,
                'reason': appointment.reason,
                'status': appointment.status,
                'urgency': appointment.urgency,
                'notes': appointment.notes,
                'created_at': appointment.created_at.isoformat()
            },
            'success': True
        }), 200
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@bp.route('/appointments/<int:appointment_id>/cancel', methods=['POST'])
@login_required
def cancel_appointment(appointment_id):
    """
    Cancel an appointment
    
    Expected JSON (optional):
    {
        "reason": "Unable to attend"
    }
    """
    try:
        appointment = Appointment.query.get(appointment_id)
        
        if not appointment:
            return jsonify({'error': 'Appointment not found', 'success': False}), 404
        
        if appointment.patient_id != current_user.id:
            return jsonify({'error': 'Unauthorized', 'success': False}), 403
        
        if appointment.status == 'cancelled':
            return jsonify({'error': 'Appointment already cancelled', 'success': False}), 400
        
        if appointment.appointment_date < datetime.utcnow():
            return jsonify({'error': 'Cannot cancel past appointments', 'success': False}), 400
        
        # Cancel appointment
        appointment.status = 'cancelled'
        db.session.commit()
        
        # Create cancellation alert
        doctor = User.query.get(appointment.doctor_id)
        alert = Alert(
            patient_id=current_user.id,
            alert_type='appointment_cancelled',
            severity='info',
            title='Appointment Cancelled',
            message=f'Your appointment with {doctor.full_name} on {appointment.appointment_date.strftime("%Y-%m-%d %H:%M")} has been cancelled.'
        )
        db.session.add(alert)
        db.session.commit()
        
        return jsonify({
            'message': 'Appointment cancelled successfully',
            'success': True
        }), 200
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@bp.route('/appointments/<int:appointment_id>/reschedule', methods=['POST'])
@login_required
def reschedule_appointment(appointment_id):
    """
    Reschedule an appointment to a new time
    
    Expected JSON:
    {
        "new_appointment_datetime": "2025-03-20T14:00:00"
    }
    """
    try:
        appointment = Appointment.query.get(appointment_id)
        
        if not appointment:
            return jsonify({'error': 'Appointment not found', 'success': False}), 404
        
        if appointment.patient_id != current_user.id:
            return jsonify({'error': 'Unauthorized', 'success': False}), 403
        
        if appointment.status != 'scheduled':
            return jsonify({'error': 'Can only reschedule scheduled appointments', 'success': False}), 400
        
        data = request.get_json()
        new_datetime_str = data.get('new_appointment_datetime')
        
        if not new_datetime_str:
            return jsonify({'error': 'New appointment datetime required', 'success': False}), 400
        
        new_datetime = datetime.fromisoformat(new_datetime_str)
        
        if new_datetime <= datetime.utcnow():
            return jsonify({'error': 'New appointment time must be in the future', 'success': False}), 400
        
        # Check if new slot is available
        existing = Appointment.query.filter_by(
            doctor_id=appointment.doctor_id,
            appointment_date=new_datetime,
            status='scheduled'
        ).first()
        
        if existing:
            return jsonify({'error': 'New slot is already booked', 'success': False}), 409
        
        # Update appointment
        appointment.appointment_date = new_datetime
        db.session.commit()
        
        doctor = User.query.get(appointment.doctor_id)
        
        return jsonify({
            'message': 'Appointment rescheduled successfully',
            'appointment': {
                'id': appointment.id,
                'doctor_name': doctor.full_name,
                'new_appointment_date': new_datetime.isoformat(),
                'status': appointment.status
            },
            'success': True
        }), 200
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500
