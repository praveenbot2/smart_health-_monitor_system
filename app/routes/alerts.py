"""
Risk-Based Alerts & Notifications System
- Real-time alert generation based on vital signs
- Risk level-based alert categorization
- Email and in-app notifications
- Alert management and resolution
- Emergency response system
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app import db, mail
from database.models import Alert, User, VitalSign, HealthPrediction
from flask_mail import Message
from datetime import datetime, timedelta
import threading
import json

bp = Blueprint('alerts', __name__, url_prefix='/api/alerts')


# Alert thresholds and risk criteria
ALERT_TRIGGERS = {
    'critical': {
        'heart_rate': {'min': 40, 'max': 120},
        'blood_pressure_systolic': {'max': 180},
        'blood_pressure_diastolic': {'max': 120},
        'temperature': {'max': 39.5},
        'oxygen_saturation': {'min': 90}
    },
    'high': {
        'heart_rate': {'min': 50, 'max': 110},
        'blood_pressure_systolic': {'max': 160},
        'blood_pressure_diastolic': {'max': 100},
        'temperature': {'max': 38.5},
        'oxygen_saturation': {'min': 95}
    },
    'medium': {
        'heart_rate': {'min': 60, 'max': 100},
        'blood_pressure_systolic': {'max': 140},
        'blood_pressure_diastolic': {'max': 90},
        'temperature': {'max': 37.5},
        'oxygen_saturation': {'min': 95}
    }
}


@bp.route('/list', methods=['GET'])
@login_required
def get_alerts():
    """
    Get alerts for current user
    
    Query params:
    - severity: filter by severity (info, warning, critical)
    - is_read: filter by read status (true/false)
    - is_resolved: filter by resolved status (true/false)
    - alert_type: filter by type (vital_alert, risk_alert, appointment_reminder, etc.)
    - limit: max results (default: 50)
    """
    try:
        severity = request.args.get('severity', '')
        is_read = request.args.get('is_read', '')
        is_resolved = request.args.get('is_resolved', '')
        alert_type = request.args.get('alert_type', '')
        limit = request.args.get('limit', 50, type=int)
        
        # Build query
        if current_user.role == 'admin':
            alerts_query = Alert.query
        else:
            alerts_query = Alert.query.filter_by(patient_id=current_user.id)
        
        # Apply filters
        if severity:
            alerts_query = alerts_query.filter_by(severity=severity)
        
        if is_read:
            alerts_query = alerts_query.filter_by(is_read=is_read.lower() == 'true')
        
        if is_resolved:
            alerts_query = alerts_query.filter_by(is_resolved=is_resolved.lower() == 'true')
        
        if alert_type:
            alerts_query = alerts_query.filter_by(alert_type=alert_type)
        
        alerts = alerts_query.order_by(Alert.created_at.desc()).limit(limit).all()
        
        alerts_data = [alert.to_dict() for alert in alerts]
        
        return jsonify({
            'alerts': alerts_data,
            'count': len(alerts_data),
            'success': True
        }), 200
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@bp.route('/unread-count', methods=['GET'])
@login_required
def get_unread_count():
    """Get count of unread alerts"""
    try:
        count = Alert.query.filter_by(
            patient_id=current_user.id,
            is_read=False
        ).count()
        
        return jsonify({'unread_count': count, 'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@bp.route('/<int:alert_id>', methods=['GET'])
@login_required
def get_alert_details(alert_id):
    """Get detailed alert information"""
    try:
        alert = Alert.query.get(alert_id)
        
        if not alert:
            return jsonify({'error': 'Alert not found', 'success': False}), 404
        
        if alert.patient_id != current_user.id and current_user.role != 'admin':
            return jsonify({'error': 'Unauthorized', 'success': False}), 403
        
        return jsonify({
            'alert': alert.to_dict(),
            'success': True
        }), 200
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@bp.route('/<int:alert_id>/read', methods=['POST'])
@login_required
def mark_as_read(alert_id):
    """Mark alert as read"""
    try:
        alert = Alert.query.get(alert_id)
        
        if not alert:
            return jsonify({'error': 'Alert not found', 'success': False}), 404
        
        if alert.patient_id != current_user.id and current_user.role != 'admin':
            return jsonify({'error': 'Unauthorized', 'success': False}), 403
        
        alert.is_read = True
        db.session.commit()
        
        return jsonify({
            'message': 'Alert marked as read',
            'success': True
        }), 200
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@bp.route('/<int:alert_id>/resolve', methods=['POST'])
@login_required
def resolve_alert(alert_id):
    """Mark alert as resolved"""
    try:
        alert = Alert.query.get(alert_id)
        
        if not alert:
            return jsonify({'error': 'Alert not found', 'success': False}), 404
        
        if alert.patient_id != current_user.id and current_user.role != 'admin':
            return jsonify({'error': 'Unauthorized', 'success': False}), 403
        
        alert.is_resolved = True
        alert.resolved_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Alert resolved',
            'success': True
        }), 200
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@bp.route('/bulk/read', methods=['POST'])
@login_required
def mark_multiple_as_read():
    """Mark multiple alerts as read"""
    try:
        data = request.get_json()
        alert_ids = data.get('alert_ids', [])
        
        if not alert_ids:
            return jsonify({'error': 'No alert IDs provided', 'success': False}), 400
        
        Alert.query.filter(
            Alert.id.in_(alert_ids),
            Alert.patient_id == current_user.id
        ).update({'is_read': True})
        db.session.commit()
        
        return jsonify({
            'message': f'Marked {len(alert_ids)} alerts as read',
            'success': True
        }), 200
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@bp.route('/check-vital-alerts/<int:patient_id>', methods=['POST'])
@login_required
def check_vital_sign_alerts(patient_id):
    """
    Check and create alerts based on vital signs
    This is called when new vital signs are recorded
    """
    try:
        # Check permission for patient data
        if current_user.role not in ['admin', 'doctor'] and patient_id != current_user.id:
            return jsonify({'error': 'Unauthorized', 'success': False}), 403
        
        # Get latest vital signs
        patient = User.query.get(patient_id)
        if not patient:
            return jsonify({'error': 'Patient not found', 'success': False}), 404
        
        vital = VitalSign.query.filter_by(patient_id=patient_id).order_by(
            VitalSign.timestamp.desc()
        ).first()
        
        if not vital:
            return jsonify({'alerts_created': 0, 'success': True}), 200
        
        created_alerts = []
        
        # Check vital signs against thresholds
        vitals_check = {
            'heart_rate': vital.heart_rate,
            'blood_pressure_systolic': vital.blood_pressure_systolic,
            'blood_pressure_diastolic': vital.blood_pressure_diastolic,
            'temperature': vital.temperature,
            'oxygen_saturation': vital.oxygen_saturation
        }
        
        # Determine alert severity
        alert_severity = 'info'
        alert_details = []
        
        for severity_level in ['critical', 'high', 'medium']:
            for vital_name, vital_value in vitals_check.items():
                if vital_value is None:
                    continue
                
                thresholds = ALERT_TRIGGERS[severity_level].get(vital_name)
                if not thresholds:
                    continue
                
                # Check against thresholds
                if 'min' in thresholds and vital_value < thresholds['min']:
                    alert_severity = severity_level
                    alert_details.append(f"{vital_name} is too low: {vital_value}")
                
                if 'max' in thresholds and vital_value > thresholds['max']:
                    alert_severity = severity_level
                    alert_details.append(f"{vital_name} is too high: {vital_value}")
        
        # Create alert if needed
        if alert_details:
            alert = Alert(
                patient_id=patient_id,
                alert_type='vital_alert',
                severity=alert_severity,
                title=f'{alert_severity.capitalize()} Vital Alert for {patient.full_name}',
                message=' | '.join(alert_details),
                is_read=False,
                is_resolved=False
            )
            
            db.session.add(alert)
            db.session.commit()
            
            created_alerts.append({
                'type': 'vital_alert',
                'severity': alert_severity,
                'message': ' | '.join(alert_details)
            })
            
            # Send email notification if critical
            if alert_severity == 'critical':
                send_critical_alert_email(patient, alert_details)
        
        return jsonify({
            'alerts_created': len(created_alerts),
            'alerts': created_alerts,
            'success': True
        }), 201
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@bp.route('/check-risk-alerts/<int:patient_id>', methods=['POST'])
@login_required
def check_health_risk_alerts(patient_id):
    """
    Check and create alerts based on health risk predictions
    """
    try:
        # Check permission
        if current_user.role not in ['admin', 'doctor'] and patient_id != current_user.id:
            return jsonify({'error': 'Unauthorized', 'success': False}), 403
        
        patient = User.query.get(patient_id)
        if not patient:
            return jsonify({'error': 'Patient not found', 'success': False}), 404
        
        # Get latest health prediction
        prediction = HealthPrediction.query.filter_by(patient_id=patient_id).order_by(
            HealthPrediction.predicted_at.desc()
        ).first()
        
        if not prediction:
            return jsonify({'alerts_created': 0, 'success': True}), 200
        
        created_alerts = []
        
        # Map risk level to alert severity
        risk_to_severity = {
            'low': 'info',
            'medium': 'warning',
            'high': 'critical',
            'critical': 'critical'
        }
        
        severity = risk_to_severity.get(prediction.risk_level, 'warning')
        
        # Create alert
        alert_messages = {
            'low': 'Your health is good. Continue with healthy lifestyle habits.',
            'medium': 'Your health shows moderate risk. Please monitor your vitals regularly and consult a doctor.',
            'high': 'High health risk detected. Please schedule an appointment with a specialist immediately.',
            'critical': 'Critical health risk detected! Seek immediate medical attention.'
        }
        
        alert = Alert(
            patient_id=patient_id,
            alert_type='risk_alert',
            severity=severity,
            title=f'Health Risk Assessment: {prediction.risk_level.upper()} Risk',
            message=alert_messages.get(prediction.risk_level, 'Health risk assessment completed'),
            is_read=False,
            is_resolved=False
        )
        
        db.session.add(alert)
        db.session.commit()
        
        created_alerts.append({
            'type': 'risk_alert',
            'severity': severity,
            'risk_level': prediction.risk_level,
            'risk_score': prediction.risk_score
        })
        
        # Send email for high/critical risk
        if severity == 'critical':
            send_risk_alert_email(patient, prediction.risk_level, prediction.risk_score)
        
        return jsonify({
            'alerts_created': len(created_alerts),
            'alerts': created_alerts,
            'success': True
        }), 201
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@bp.route('/emergency-contacts', methods=['GET'])
@login_required
def get_emergency_contacts():
    """Get emergency contact information"""
    try:
        # Would retrieve emergency contacts from user profile
        # For now, returning placeholder
        return jsonify({
            'emergency_contacts': [
                {'name': 'Emergency Services', 'phone': '911', 'type': 'Emergency'},
                {'name': 'Doctor on Call', 'phone': 'Listed in appointments', 'type': 'Medical'}
            ],
            'success': True
        }), 200
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@bp.route('/health-summary', methods=['GET'])
@login_required
def get_health_summary():
    """Get health summary with recent alerts and concerns"""
    try:
        patient_id = current_user.id
        
        # Get recent alerts
        recent_alerts = Alert.query.filter_by(patient_id=patient_id).order_by(
            Alert.created_at.desc()
        ).limit(5).all()
        
        # Get critical alert count
        critical_count = Alert.query.filter_by(
            patient_id=patient_id,
            severity='critical',
            is_resolved=False
        ).count()
        
        # Get latest prediction
        prediction = HealthPrediction.query.filter_by(patient_id=patient_id).order_by(
            HealthPrediction.predicted_at.desc()
        ).first()
        
        # Get latest vitals
        vital = VitalSign.query.filter_by(patient_id=patient_id).order_by(
            VitalSign.timestamp.desc()
        ).first()
        
        summary = {
            'active_alerts': critical_count,
            'recent_alerts': [a.to_dict() for a in recent_alerts],
            'health_risk_level': prediction.risk_level if prediction else 'unknown',
            'health_risk_score': prediction.risk_score if prediction else 0,
            'last_vital_check': vital.timestamp.isoformat() if vital else None,
            'status': 'Monitoring' if critical_count == 0 else 'Requires Attention'
        }
        
        return jsonify({
            'summary': summary,
            'success': True
        }), 200
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


# Helper functions
def send_critical_alert_email(patient, alert_details):
    """Send email for critical alerts"""
    try:
        msg = Message(
            subject='⚠️ CRITICAL HEALTH ALERT',
            recipients=[patient.email],
            html=f"""
            <h2>Critical Health Alert</h2>
            <p>Dear {patient.full_name},</p>
            <p>We have detected critical changes in your vital signs:</p>
            <ul>
                {''.join([f'<li>{detail}</li>' for detail in alert_details])}
            </ul>
            <p><strong>Action Required:</strong> Please seek immediate medical attention or contact emergency services if needed.</p>
            <p>Log in to your Smart Health Monitor dashboard for more information.</p>
            """
        )
        mail.send(msg)
    except Exception as e:
        print(f"Error sending alert email: {e}")


def send_risk_alert_email(patient, risk_level, risk_score):
    """Send email for high/critical risk alerts"""
    try:
        recommendations = {
            'high': 'Please schedule an appointment with a doctor and monitor your health closely.',
            'critical': 'Seek immediate medical attention. This is a health emergency.'
        }
        
        msg = Message(
            subject=f'Health Risk Assessment: {risk_level.upper()} RISK',
            recipients=[patient.email],
            html=f"""
            <h2>Health Risk Assessment Results</h2>
            <p>Dear {patient.full_name},</p>
            <p>Your latest health assessment shows a <strong>{risk_level.upper()}</strong> risk level (Score: {risk_score}).</p>
            <p><strong>Recommendation:</strong> {recommendations.get(risk_level, 'Continue monitoring your health.')}</p>
            <p>Visit your dashboard for detailed recommendations and doctor suggestions.</p>
            """
        )
        mail.send(msg)
    except Exception as e:
        print(f"Error sending risk alert email: {e}")

@login_required
def resolve_alert(alert_id):
    """Resolve alert"""
    alert = Alert.query.get(alert_id)
    
    if not alert:
        return jsonify({'error': 'Alert not found'}), 404
    
    # Check permission
    if current_user.role not in ['admin'] and alert.patient_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    alert.is_resolved = True
    alert.resolved_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'message': 'Alert resolved'}), 200


@bp.route('/create', methods=['POST'])
def create_alert():
    """Create manual alert"""
    data = request.get_json()
    
    required_fields = ['patient_id', 'alert_type', 'severity', 'title', 'message']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Validate patient exists
    patient = User.query.get(data['patient_id'])
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    
    alert = Alert(
        patient_id=data['patient_id'],
        alert_type=data['alert_type'],
        severity=data['severity'],
        title=data['title'],
        message=data['message']
    )
    
    db.session.add(alert)
    db.session.commit()
    
    # Send email for critical alerts
    if alert.severity == 'critical':
        send_alert_email(alert)
    
    return jsonify({
        'message': 'Alert created successfully',
        'alert': alert.to_dict()
    }), 201


@bp.route('/<int:alert_id>', methods=['DELETE'])
@login_required
def delete_alert(alert_id):
    """Delete alert"""
    alert = Alert.query.get(alert_id)
    
    if not alert:
        return jsonify({'error': 'Alert not found'}), 404
    
    # Check permission
    if current_user.role not in ['admin'] and alert.patient_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    db.session.delete(alert)
    db.session.commit()
    
    return jsonify({'message': 'Alert deleted'}), 200


@bp.route('/critical', methods=['GET'])
@login_required
def get_critical_alerts():
    """Get critical unresolved alerts"""
    if current_user.role == 'admin':
        alerts = Alert.query.filter_by(
            severity='critical',
            is_resolved=False
        )
    else:
        alerts = Alert.query.filter_by(
            patient_id=current_user.id,
            severity='critical',
            is_resolved=False
        )
    
    alerts = alerts.order_by(Alert.created_at.desc()).all()
    
    return jsonify({
        'critical_alerts': [a.to_dict() for a in alerts]
    }), 200


@bp.route('/emergency-suggestions', methods=['GET'])
@login_required
def get_emergency_suggestions():
    """Get emergency response suggestions"""
    patient_id = request.args.get('patient_id', current_user.id, type=int)
    
    # Check permission
    if current_user.role not in ['admin', 'doctor'] and patient_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get recent critical alerts
    recent_alerts = Alert.query.filter(
        Alert.patient_id == patient_id,
        Alert.severity == 'critical',
        Alert.created_at >= datetime.utcnow() - timedelta(hours=24)
    ).all()
    
    if not recent_alerts:
        return jsonify({
            'suggestions': [],
            'emergency_level': 'none'
        }), 200
    
    # Determine emergency level
    emergency_level = 'moderate'
    suggestions = []
    
    for alert in recent_alerts:
        if 'critical_vitals' in alert.alert_type:
            emergency_level = 'severe'
            suggestions.extend(get_critical_vitals_suggestions(alert))
        elif 'high_risk' in alert.alert_type:
            if emergency_level != 'severe':
                emergency_level = 'high'
            suggestions.extend(get_high_risk_suggestions(alert))
    
    # Add general emergency suggestions
    if emergency_level == 'severe':
        suggestions.insert(0, {
            'priority': 1,
            'action': 'Call Emergency Services',
            'description': 'Call 911 or your local emergency number immediately',
            'icon': '🚨'
        })
        suggestions.insert(1, {
            'priority': 2,
            'action': 'Seek Immediate Medical Attention',
            'description': 'Go to the nearest emergency room',
            'icon': '🏥'
        })
    
    return jsonify({
        'suggestions': suggestions[:10],  # Top 10
        'emergency_level': emergency_level,
        'alert_count': len(recent_alerts)
    }), 200


@bp.route('/mark-all-read', methods=['POST'])
@login_required
def mark_all_read():
    """Mark all alerts as read"""
    Alert.query.filter_by(
        patient_id=current_user.id,
        is_read=False
    ).update({'is_read': True})
    
    db.session.commit()
    
    return jsonify({'message': 'All alerts marked as read'}), 200


def send_alert_email(alert):
    """Send alert notification email"""
    try:
        patient = User.query.get(alert.patient_id)
        if not patient or not patient.email:
            return
        
        msg = Message(
            subject=f'🚨 Health Alert: {alert.title}',
            recipients=[patient.email],
            body=f"""
Dear {patient.full_name},

{alert.message}

Alert Details:
- Type: {alert.alert_type}
- Severity: {alert.severity.upper()}
- Time: {alert.created_at.strftime('%Y-%m-%d %H:%M:%S')}

Please take appropriate action and consult with a healthcare professional if needed.

This is an automated message from Smart Health Monitor System.

Best regards,
Smart Health Monitor Team
            """
        )
        
        # Send email in background thread
        thread = threading.Thread(target=send_async_email, args=(msg,))
        thread.start()
        
    except Exception as e:
        print(f"Error sending alert email: {e}")


def send_async_email(msg):
    """Send email asynchronously"""
    try:
        mail.send(msg)
    except Exception as e:
        print(f"Failed to send email: {e}")


def get_critical_vitals_suggestions(alert):
    """Get suggestions for critical vital signs"""
    suggestions = [
        {
            'priority': 3,
            'action': 'Monitor Vital Signs',
            'description': 'Check vital signs every 15 minutes',
            'icon': '📊'
        },
        {
            'priority': 4,
            'action': 'Stay Calm',
            'description': 'Try to remain calm and rest',
            'icon': '🧘'
        },
        {
            'priority': 5,
            'action': 'Contact Doctor',
            'description': 'Call your primary care physician',
            'icon': '📞'
        },
        {
            'priority': 6,
            'action': 'Prepare Medical History',
            'description': 'Have your medical records ready',
            'icon': '📋'
        }
    ]
    
    return suggestions


def get_high_risk_suggestions(alert):
    """Get suggestions for high risk predictions"""
    suggestions = [
        {
            'priority': 3,
            'action': 'Schedule Medical Consultation',
            'description': 'Book an appointment with a specialist',
            'icon': '👨‍⚕️'
        },
        {
            'priority': 4,
            'action': 'Lifestyle Modifications',
            'description': 'Follow recommended lifestyle changes',
            'icon': '🥗'
        },
        {
            'priority': 5,
            'action': 'Regular Monitoring',
            'description': 'Monitor health parameters daily',
            'icon': '📈'
        },
        {
            'priority': 6,
            'action': 'Medication Review',
            'description': 'Review current medications with doctor',
            'icon': '💊'
        }
    ]
    
    return suggestions
