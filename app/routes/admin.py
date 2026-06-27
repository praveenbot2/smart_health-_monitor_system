"""
Module 10: Administrative Analytics & Monitoring
- User statistics
- Risk distribution
- Appointment analytics
- System performance insights
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app import db
from database.models import User, VitalSign, HealthPrediction, Appointment, Alert, MedicalReport
from datetime import datetime, timedelta
from sqlalchemy import func, and_
from services.patient_seed_service import seed_patients as seed_random_patients

bp = Blueprint('admin', __name__, url_prefix='/api/admin')


@bp.route('/patients/seed', methods=['POST'])
@login_required
def seed_patients_endpoint():
    """Admin-only endpoint to persist random patient + vital + prediction data."""
    try:
        if current_user.role != 'admin':
            return jsonify({'error': 'Only admin users can seed patient data'}), 403

        payload = request.get_json(silent=True) or {}
        count = payload.get('count', request.args.get('count', 10))

        try:
            count = int(count)
        except (TypeError, ValueError):
            return jsonify({'error': 'count must be an integer'}), 400

        if count < 10:
            return jsonify({'error': 'count must be 10 or more'}), 400

        result = seed_random_patients(count=count)

        return jsonify({
            'message': f'{result["created"]} patient records seeded successfully',
            'result': result,
            'success': True
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e), 'success': False}), 500

@bp.route('/dashboard', methods=['GET'])
@login_required
def get_dashboard_stats():
    """Get comprehensive dashboard statistics"""
    stats = {
        'users': get_user_statistics(),
        'vitals': get_vital_statistics(),
        'risks': get_risk_distribution(),
        'appointments': get_appointment_analytics(),
        'alerts': get_alert_statistics(),
        'reports': get_report_statistics(),
        'system': get_system_performance()
    }
    
    return jsonify({'dashboard': stats}), 200


@bp.route('/users/statistics', methods=['GET'])
def user_statistics():
    """Get user statistics"""
    stats = get_user_statistics()
    return jsonify({'statistics': stats}), 200


@bp.route('/users/list', methods=['GET'])
def list_all_users():
    """Get list of all users"""
    role = request.args.get('role')
    is_active = request.args.get('is_active')
    
    query = User.query
    
    if role:
        query = query.filter_by(role=role)
    
    if is_active is not None:
        query = query.filter_by(is_active=is_active.lower() == 'true')
    
    users = query.order_by(User.created_at.desc()).all()
    
    return jsonify({
        'users': [u.to_dict() for u in users],
        'total': len(users)
    }), 200


@bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
def toggle_user_status(user_id):
    """Activate or deactivate user"""
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    user.is_active = not user.is_active
    db.session.commit()
    
    return jsonify({
        'message': f'User {"activated" if user.is_active else "deactivated"} successfully',
        'user': user.to_dict()
    }), 200


@bp.route('/risks/distribution', methods=['GET'])
def risk_distribution():
    """Get risk level distribution"""
    stats = get_risk_distribution()
    return jsonify({'distribution': stats}), 200


@bp.route('/risks/high-risk-patients', methods=['GET'])
def high_risk_patients():
    """Get list of high-risk patients"""
    # Get latest prediction for each patient
    subquery = db.session.query(
        HealthPrediction.patient_id,
        func.max(HealthPrediction.predicted_at).label('max_date')
    ).group_by(HealthPrediction.patient_id).subquery()
    
    high_risk_predictions = db.session.query(HealthPrediction).join(
        subquery,
        and_(
            HealthPrediction.patient_id == subquery.c.patient_id,
            HealthPrediction.predicted_at == subquery.c.max_date
        )
    ).filter(HealthPrediction.risk_level == 'high').all()
    
    patients = []
    for pred in high_risk_predictions:
        patient_data = pred.patient.to_dict()
        patient_data['latest_prediction'] = pred.to_dict()
        patients.append(patient_data)
    
    return jsonify({
        'high_risk_patients': patients,
        'total': len(patients)
    }), 200


@bp.route('/appointments/analytics', methods=['GET'])
def appointment_analytics():
    """Get appointment analytics"""
    stats = get_appointment_analytics()
    return jsonify({'analytics': stats}), 200


@bp.route('/alerts/statistics', methods=['GET'])
def alert_statistics():
    """Get alert statistics"""
    stats = get_alert_statistics()
    return jsonify({'statistics': stats}), 200


@bp.route('/reports/statistics', methods=['GET'])
def report_statistics():
    """Get report generation statistics"""
    stats = get_report_statistics()
    return jsonify({'statistics': stats}), 200


@bp.route('/vitals/analytics', methods=['GET'])
def vitals_analytics():
    """Get vital signs analytics"""
    days = request.args.get('days', 30, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)
    
    vitals = VitalSign.query.filter(
        VitalSign.recorded_at >= start_date
    ).all()
    
    analytics = {
        'total_readings': len(vitals),
        'by_source': {
            'manual': len([v for v in vitals if v.source == 'manual']),
            'iot_device': len([v for v in vitals if v.source == 'iot_device'])
        },
        'daily_average': round(len(vitals) / days, 2) if days > 0 else 0,
        'period_days': days
    }
    
    return jsonify({'analytics': analytics}), 200


@bp.route('/system/performance', methods=['GET'])
def system_performance():
    """Get system performance metrics"""
    stats = get_system_performance()
    return jsonify({'performance': stats}), 200


@bp.route('/trends/weekly', methods=['GET'])
def weekly_trends():
    """Get weekly trends for various metrics"""
    weeks = request.args.get('weeks', 12, type=int)
    
    trends = {
        'new_users': get_weekly_new_users(weeks),
        'appointments': get_weekly_appointments(weeks),
        'predictions': get_weekly_predictions(weeks),
        'alerts': get_weekly_alerts(weeks)
    }
    
    return jsonify({'trends': trends}), 200


# Helper functions

def get_user_statistics():
    """Calculate user statistics"""
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    
    users_by_role = {
        'patients': User.query.filter_by(role='patient').count(),
        'doctors': User.query.filter_by(role='doctor').count(),
        'admins': User.query.filter_by(role='admin').count()
    }
    
    # New users last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    new_users_30d = User.query.filter(User.created_at >= thirty_days_ago).count()
    
    return {
        'total_users': total_users,
        'active_users': active_users,
        'inactive_users': total_users - active_users,
        'by_role': users_by_role,
        'new_users_last_30_days': new_users_30d
    }


def get_vital_statistics():
    """Calculate vital signs statistics"""
    total_vitals = VitalSign.query.count()
    
    # Last 24 hours
    yesterday = datetime.utcnow() - timedelta(days=1)
    vitals_24h = VitalSign.query.filter(VitalSign.recorded_at >= yesterday).count()
    
    # By source
    manual = VitalSign.query.filter_by(source='manual').count()
    iot = VitalSign.query.filter_by(source='iot_device').count()
    
    return {
        'total_readings': total_vitals,
        'last_24_hours': vitals_24h,
        'by_source': {
            'manual': manual,
            'iot_device': iot
        }
    }


def get_risk_distribution():
    """Get risk level distribution"""
    # Get latest prediction for each patient
    subquery = db.session.query(
        HealthPrediction.patient_id,
        func.max(HealthPrediction.predicted_at).label('max_date')
    ).group_by(HealthPrediction.patient_id).subquery()
    
    latest_predictions = db.session.query(HealthPrediction).join(
        subquery,
        and_(
            HealthPrediction.patient_id == subquery.c.patient_id,
            HealthPrediction.predicted_at == subquery.c.max_date
        )
    ).all()
    
    distribution = {
        'low': 0,
        'medium': 0,
        'high': 0,
        'total': len(latest_predictions)
    }
    
    for pred in latest_predictions:
        distribution[pred.risk_level] += 1
    
    # Calculate percentages
    if distribution['total'] > 0:
        distribution['percentages'] = {
            'low': round(distribution['low'] / distribution['total'] * 100, 2),
            'medium': round(distribution['medium'] / distribution['total'] * 100, 2),
            'high': round(distribution['high'] / distribution['total'] * 100, 2)
        }
    
    return distribution


def get_appointment_analytics():
    """Calculate appointment analytics"""
    total = Appointment.query.count()
    scheduled = Appointment.query.filter_by(status='scheduled').count()
    completed = Appointment.query.filter_by(status='completed').count()
    cancelled = Appointment.query.filter_by(status='cancelled').count()
    
    # Upcoming appointments
    upcoming = Appointment.query.filter(
        Appointment.appointment_date >= datetime.utcnow(),
        Appointment.status == 'scheduled'
    ).count()
    
    # Appointments by urgency
    by_urgency = {
        'normal': Appointment.query.filter_by(urgency='normal').count(),
        'urgent': Appointment.query.filter_by(urgency='urgent').count(),
        'emergency': Appointment.query.filter_by(urgency='emergency').count()
    }
    
    return {
        'total_appointments': total,
        'by_status': {
            'scheduled': scheduled,
            'completed': completed,
            'cancelled': cancelled
        },
        'upcoming': upcoming,
        'by_urgency': by_urgency
    }


def get_alert_statistics():
    """Calculate alert statistics"""
    total = Alert.query.count()
    unread = Alert.query.filter_by(is_read=False).count()
    unresolved = Alert.query.filter_by(is_resolved=False).count()
    
    by_severity = {
        'info': Alert.query.filter_by(severity='info').count(),
        'warning': Alert.query.filter_by(severity='warning').count(),
        'critical': Alert.query.filter_by(severity='critical').count()
    }
    
    # Critical unresolved
    critical_unresolved = Alert.query.filter_by(
        severity='critical',
        is_resolved=False
    ).count()
    
    return {
        'total_alerts': total,
        'unread': unread,
        'unresolved': unresolved,
        'by_severity': by_severity,
        'critical_unresolved': critical_unresolved
    }


def get_report_statistics():
    """Calculate report statistics"""
    total = MedicalReport.query.count()
    
    by_type = {}
    for report_type in ['health_summary', 'risk_assessment', 'vitals_report']:
        by_type[report_type] = MedicalReport.query.filter_by(report_type=report_type).count()
    
    # Last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent = MedicalReport.query.filter(MedicalReport.generated_at >= thirty_days_ago).count()
    
    return {
        'total_reports': total,
        'by_type': by_type,
        'generated_last_30_days': recent
    }


def get_system_performance():
    """Calculate system performance metrics"""
    # Database record counts
    db_stats = {
        'users': User.query.count(),
        'vitals': VitalSign.query.count(),
        'predictions': HealthPrediction.query.count(),
        'appointments': Appointment.query.count(),
        'alerts': Alert.query.count(),
        'reports': MedicalReport.query.count()
    }
    
    # Activity in last 24 hours
    yesterday = datetime.utcnow() - timedelta(days=1)
    activity_24h = {
        'new_vitals': VitalSign.query.filter(VitalSign.recorded_at >= yesterday).count(),
        'new_predictions': HealthPrediction.query.filter(HealthPrediction.predicted_at >= yesterday).count(),
        'new_appointments': Appointment.query.filter(Appointment.created_at >= yesterday).count(),
        'new_alerts': Alert.query.filter(Alert.created_at >= yesterday).count()
    }
    
    return {
        'database_records': db_stats,
        'activity_last_24h': activity_24h,
        'timestamp': datetime.utcnow().isoformat()
    }


def get_weekly_new_users(weeks):
    """Get weekly new user counts"""
    weekly_data = []
    
    for i in range(weeks):
        week_start = datetime.utcnow() - timedelta(weeks=i+1)
        week_end = datetime.utcnow() - timedelta(weeks=i)
        
        count = User.query.filter(
            User.created_at >= week_start,
            User.created_at < week_end
        ).count()
        
        weekly_data.append({
            'week': f'Week {weeks - i}',
            'count': count
        })
    
    return weekly_data[::-1]


def get_weekly_appointments(weeks):
    """Get weekly appointment counts"""
    weekly_data = []
    
    for i in range(weeks):
        week_start = datetime.utcnow() - timedelta(weeks=i+1)
        week_end = datetime.utcnow() - timedelta(weeks=i)
        
        count = Appointment.query.filter(
            Appointment.created_at >= week_start,
            Appointment.created_at < week_end
        ).count()
        
        weekly_data.append({
            'week': f'Week {weeks - i}',
            'count': count
        })
    
    return weekly_data[::-1]


def get_weekly_predictions(weeks):
    """Get weekly prediction counts"""
    weekly_data = []
    
    for i in range(weeks):
        week_start = datetime.utcnow() - timedelta(weeks=i+1)
        week_end = datetime.utcnow() - timedelta(weeks=i)
        
        count = HealthPrediction.query.filter(
            HealthPrediction.predicted_at >= week_start,
            HealthPrediction.predicted_at < week_end
        ).count()
        
        weekly_data.append({
            'week': f'Week {weeks - i}',
            'count': count
        })
    
    return weekly_data[::-1]


def get_weekly_alerts(weeks):
    """Get weekly alert counts"""
    weekly_data = []
    
    for i in range(weeks):
        week_start = datetime.utcnow() - timedelta(weeks=i+1)
        week_end = datetime.utcnow() - timedelta(weeks=i)
        
        count = Alert.query.filter(
            Alert.created_at >= week_start,
            Alert.created_at < week_end
        ).count()
        
        weekly_data.append({
            'week': f'Week {weeks - i}',
            'count': count
        })
    
    return weekly_data[::-1]
