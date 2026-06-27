"""
Module 2: Real-Time Vital Monitoring
- Live heart rate tracking
- Blood pressure monitoring
- Oxygen level monitoring
- IoT data simulation
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from flask_socketio import emit
from app import db, socketio
from database.models import VitalSign, Alert
from datetime import datetime, timedelta
import random
import json
from config import Config

bp = Blueprint('vitals', __name__, url_prefix='/api/vitals')

@bp.route('/record', methods=['POST'])
@login_required
def record_vitals():
    """Record vital signs"""
    data = request.get_json()
    
    patient_id = data.get('patient_id', current_user.id)
    
    # Check permission
    if current_user.role not in ['admin', 'doctor'] and patient_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    vital = VitalSign(
        patient_id=patient_id,
        heart_rate=data.get('heart_rate'),
        blood_pressure_systolic=data.get('blood_pressure_systolic'),
        blood_pressure_diastolic=data.get('blood_pressure_diastolic'),
        oxygen_level=data.get('oxygen_level'),
        temperature=data.get('temperature'),
        source=data.get('source', 'manual')
    )
    
    db.session.add(vital)
    db.session.commit()
    
    # Check for critical values and create alerts
    check_critical_vitals(vital)
    
    # Emit real-time update via WebSocket
    socketio.emit('vital_update', {
        'patient_id': patient_id,
        'data': vital.to_dict()
    }, room=f'patient_{patient_id}')
    
    return jsonify({
        'message': 'Vital signs recorded successfully',
        'vital': vital.to_dict()
    }), 201


@bp.route('/history', methods=['GET'])
@login_required
def get_vitals_history():
    """Get vital signs history"""
    patient_id = request.args.get('patient_id', current_user.id, type=int)
    
    # Check permission
    if current_user.role not in ['admin', 'doctor'] and patient_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    days = request.args.get('days', 7, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)
    
    vitals = VitalSign.query.filter(
        VitalSign.patient_id == patient_id,
        VitalSign.recorded_at >= start_date
    ).order_by(VitalSign.recorded_at.desc()).all()
    
    return jsonify({
        'vitals': [v.to_dict() for v in vitals]
    }), 200


@bp.route('/latest', methods=['GET'])
@login_required
def get_latest_vitals():
    """Get latest vital signs"""
    patient_id = request.args.get('patient_id', current_user.id, type=int)
    
    # Check permission
    if current_user.role not in ['admin', 'doctor'] and patient_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    vital = VitalSign.query.filter_by(patient_id=patient_id).order_by(
        VitalSign.recorded_at.desc()
    ).first()
    
    if not vital:
        return jsonify({'vital': None}), 200
    
    return jsonify({'vital': vital.to_dict()}), 200


@bp.route('/simulate', methods=['POST'])
@login_required
def simulate_iot_data():
    """Simulate IoT device data for testing"""
    data = request.get_json()
    patient_id = data.get('patient_id', current_user.id)
    
    # Check permission
    if current_user.role not in ['admin', 'doctor'] and patient_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Generate realistic vital signs with some variation
    vital = VitalSign(
        patient_id=patient_id,
        heart_rate=random.randint(60, 100) + random.randint(-10, 10),
        blood_pressure_systolic=random.randint(110, 130) + random.randint(-10, 10),
        blood_pressure_diastolic=random.randint(70, 85) + random.randint(-5, 5),
        oxygen_level=round(random.uniform(95, 99.5), 1),
        temperature=round(random.uniform(36.2, 37.1), 1),
        source='iot_device'
    )
    
    db.session.add(vital)
    db.session.commit()
    
    # Check for critical values
    check_critical_vitals(vital)
    
    # Emit real-time update
    socketio.emit('vital_update', {
        'patient_id': patient_id,
        'data': vital.to_dict()
    }, room=f'patient_{patient_id}')
    
    return jsonify({
        'message': 'IoT data simulated successfully',
        'vital': vital.to_dict()
    }), 201


@bp.route('/statistics', methods=['GET'])
@login_required
def get_vitals_statistics():
    """Get vital signs statistics"""
    patient_id = request.args.get('patient_id', current_user.id, type=int)
    
    # Check permission
    if current_user.role not in ['admin', 'doctor'] and patient_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    days = request.args.get('days', 7, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)
    
    vitals = VitalSign.query.filter(
        VitalSign.patient_id == patient_id,
        VitalSign.recorded_at >= start_date
    ).all()
    
    if not vitals:
        return jsonify({'statistics': None}), 200
    
    # Calculate statistics
    stats = {
        'heart_rate': calculate_stats([v.heart_rate for v in vitals if v.heart_rate]),
        'blood_pressure_systolic': calculate_stats([v.blood_pressure_systolic for v in vitals if v.blood_pressure_systolic]),
        'blood_pressure_diastolic': calculate_stats([v.blood_pressure_diastolic for v in vitals if v.blood_pressure_diastolic]),
        'oxygen_level': calculate_stats([v.oxygen_level for v in vitals if v.oxygen_level]),
        'temperature': calculate_stats([v.temperature for v in vitals if v.temperature]),
        'total_readings': len(vitals),
        'period_days': days
    }
    
    return jsonify({'statistics': stats}), 200


def calculate_stats(values):
    """Calculate min, max, average for a list of values"""
    if not values:
        return None
    return {
        'min': round(min(values), 2),
        'max': round(max(values), 2),
        'average': round(sum(values) / len(values), 2),
        'count': len(values)
    }


def check_critical_vitals(vital):
    """Check if vital signs are critical and create alerts"""
    ranges = Config.VITAL_RANGES
    critical_issues = []
    
    if vital.heart_rate:
        hr_range = ranges['heart_rate']
        if vital.heart_rate < hr_range['critical_min'] or vital.heart_rate > hr_range['critical_max']:
            critical_issues.append(f"Heart rate: {vital.heart_rate} bpm (Critical)")
    
    if vital.blood_pressure_systolic:
        bp_sys_range = ranges['blood_pressure_systolic']
        if vital.blood_pressure_systolic < bp_sys_range['critical_min'] or vital.blood_pressure_systolic > bp_sys_range['critical_max']:
            critical_issues.append(f"Systolic BP: {vital.blood_pressure_systolic} mmHg (Critical)")
    
    if vital.blood_pressure_diastolic:
        bp_dias_range = ranges['blood_pressure_diastolic']
        if vital.blood_pressure_diastolic < bp_dias_range['critical_min'] or vital.blood_pressure_diastolic > bp_dias_range['critical_max']:
            critical_issues.append(f"Diastolic BP: {vital.blood_pressure_diastolic} mmHg (Critical)")
    
    if vital.oxygen_level:
        o2_range = ranges['oxygen_level']
        if vital.oxygen_level < o2_range['critical_min']:
            critical_issues.append(f"Oxygen level: {vital.oxygen_level}% (Critical)")
    
    if vital.temperature:
        temp_range = ranges['temperature']
        if vital.temperature < temp_range['critical_min'] or vital.temperature > temp_range['critical_max']:
            critical_issues.append(f"Temperature: {vital.temperature}°C (Critical)")
    
    # Create alert if critical issues found
    if critical_issues:
        alert = Alert(
            patient_id=vital.patient_id,
            alert_type='critical_vitals',
            severity='critical',
            title='Critical Vital Signs Detected',
            message=f"Critical vital signs detected: {', '.join(critical_issues)}. Immediate medical attention recommended."
        )
        db.session.add(alert)
        db.session.commit()
        
        # Emit alert notification
        socketio.emit('critical_alert', {
            'patient_id': vital.patient_id,
            'alert': alert.to_dict()
        }, room=f'patient_{vital.patient_id}')


# WebSocket events
@socketio.on('join_monitoring')
def handle_join_monitoring(data):
    """Join a patient's monitoring room"""
    from flask_socketio import join_room
    patient_id = data.get('patient_id')
    if patient_id:
        join_room(f'patient_{patient_id}')
        emit('joined', {'message': f'Joined monitoring for patient {patient_id}'})


@socketio.on('leave_monitoring')
def handle_leave_monitoring(data):
    """Leave a patient's monitoring room"""
    from flask_socketio import leave_room
    patient_id = data.get('patient_id')
    if patient_id:
        leave_room(f'patient_{patient_id}')
        emit('left', {'message': f'Left monitoring for patient {patient_id}'})
