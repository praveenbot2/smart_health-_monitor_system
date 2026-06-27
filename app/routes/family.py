"""
Family Member Management Module
- Add family members
- Edit family member information
- View family member health history
- Delete family members
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app import db
from database.models import FamilyMember, FamilyVitalSign, FamilyMemberHealthScore, FamilyMemberAlert
from datetime import datetime, timedelta

bp = Blueprint('family', __name__, url_prefix='/api/family')


PARENT_RELATIONS = {'mother', 'father', 'guardian', 'grandmother', 'grandfather'}


@bp.route('/members', methods=['GET'])
@login_required
def get_family_members():
    """Get all family members for current user"""
    members = FamilyMember.query.filter_by(user_id=current_user.id).order_by(
        FamilyMember.created_at.desc()
    ).all()

    enriched_members = []
    for member in members:
        member_data = member.to_dict()
        latest_vital = FamilyVitalSign.query.filter_by(family_member_id=member.id).order_by(
            FamilyVitalSign.recorded_at.desc()
        ).first()
        latest_score = FamilyMemberHealthScore.query.filter_by(family_member_id=member.id).order_by(
            FamilyMemberHealthScore.calculated_at.desc()
        ).first()
        unresolved_alerts_count = FamilyMemberAlert.query.filter_by(
            family_member_id=member.id,
            is_resolved=False
        ).count()

        member_data['latest_vital'] = latest_vital.to_dict() if latest_vital else None
        member_data['latest_health_score'] = latest_score.to_dict() if latest_score else None
        member_data['unresolved_alerts_count'] = unresolved_alerts_count
        member_data['is_parent'] = (member.relation or '').lower() in PARENT_RELATIONS
        enriched_members.append(member_data)
    
    return jsonify({
        'family_members': enriched_members,
        'total': len(members)
    }), 200


@bp.route('/members', methods=['POST'])
@login_required
def add_family_member():
    """Add a new family member"""
    data = request.get_json()
    
    # Validate required fields
    if not data.get('name') or not data.get('relation'):
        return jsonify({'error': 'Name and relation are required'}), 400
    
    # Create family member
    member = FamilyMember(
        user_id=current_user.id,
        name=data.get('name'),
        age=data.get('age'),
        relation=data.get('relation'),
        health_history=data.get('health_history'),
        blood_type=data.get('blood_type'),
        current_medications=data.get('current_medications'),
        chronic_conditions=data.get('chronic_conditions'),
        contact_number=data.get('contact_number')
    )
    
    db.session.add(member)
    db.session.commit()
    
    return jsonify({
        'message': 'Family member added successfully',
        'family_member': member.to_dict()
    }), 201


@bp.route('/members/<int:member_id>', methods=['GET'])
@login_required
def get_family_member(member_id):
    """Get a specific family member"""
    member = FamilyMember.query.filter_by(
        id=member_id,
        user_id=current_user.id
    ).first()
    
    if not member:
        return jsonify({'error': 'Family member not found'}), 404
    
    member_data = member.to_dict()
    latest_vital = FamilyVitalSign.query.filter_by(family_member_id=member.id).order_by(
        FamilyVitalSign.recorded_at.desc()
    ).first()
    latest_score = FamilyMemberHealthScore.query.filter_by(family_member_id=member.id).order_by(
        FamilyMemberHealthScore.calculated_at.desc()
    ).first()
    unresolved_alerts_count = FamilyMemberAlert.query.filter_by(
        family_member_id=member.id,
        is_resolved=False
    ).count()

    member_data['latest_vital'] = latest_vital.to_dict() if latest_vital else None
    member_data['latest_health_score'] = latest_score.to_dict() if latest_score else None
    member_data['unresolved_alerts_count'] = unresolved_alerts_count
    member_data['is_parent'] = (member.relation or '').lower() in PARENT_RELATIONS

    return jsonify({'family_member': member_data}), 200


@bp.route('/members/<int:member_id>', methods=['PUT'])
@login_required
def update_family_member(member_id):
    """Update family member information"""
    member = FamilyMember.query.filter_by(
        id=member_id,
        user_id=current_user.id
    ).first()
    
    if not member:
        return jsonify({'error': 'Family member not found'}), 404
    
    data = request.get_json()
    
    # Update fields
    if 'name' in data:
        member.name = data['name']
    if 'age' in data:
        member.age = data['age']
    if 'relation' in data:
        member.relation = data['relation']
    if 'health_history' in data:
        member.health_history = data['health_history']
    if 'blood_type' in data:
        member.blood_type = data['blood_type']
    if 'current_medications' in data:
        member.current_medications = data['current_medications']
    if 'chronic_conditions' in data:
        member.chronic_conditions = data['chronic_conditions']
    if 'contact_number' in data:
        member.contact_number = data['contact_number']
    
    member.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'message': 'Family member updated successfully',
        'family_member': member.to_dict()
    }), 200


@bp.route('/members/<int:member_id>', methods=['DELETE'])
@login_required
def delete_family_member(member_id):
    """Delete a family member"""
    member = FamilyMember.query.filter_by(
        id=member_id,
        user_id=current_user.id
    ).first()
    
    if not member:
        return jsonify({'error': 'Family member not found'}), 404
    
    db.session.delete(member)
    db.session.commit()
    
    return jsonify({'message': 'Family member deleted successfully'}), 200


@bp.route('/relations', methods=['GET'])
def get_relations():
    """Get list of possible relations"""
    relations = [
        'Mother',
        'Father',
        'Sister',
        'Brother',
        'Spouse',
        'Son',
        'Daughter',
        'Grandmother',
        'Grandfather',
        'Aunt',
        'Uncle',
        'Cousin',
        'Niece',
        'Nephew',
        'Grandchild',
        'In-law',
        'Friend',
        'Guardian',
        'Other'
    ]
    
    return jsonify({'relations': relations}), 200


@bp.route('/members/<int:member_id>/vitals', methods=['POST'])
@login_required
def record_family_member_vitals(member_id):
    """Record vitals for a family member"""
    member = FamilyMember.query.filter_by(id=member_id, user_id=current_user.id).first()
    if not member:
        return jsonify({'error': 'Family member not found'}), 404

    data = request.get_json() or {}

    vital = FamilyVitalSign(
        family_member_id=member.id,
        heart_rate=data.get('heart_rate'),
        blood_pressure_systolic=data.get('blood_pressure_systolic'),
        blood_pressure_diastolic=data.get('blood_pressure_diastolic'),
        oxygen_level=data.get('oxygen_level'),
        temperature=data.get('temperature'),
        weight=data.get('weight'),
        notes=data.get('notes')
    )

    db.session.add(vital)
    db.session.flush()

    _create_family_vital_alerts(member, vital)
    db.session.commit()

    return jsonify({
        'message': 'Vitals recorded successfully',
        'vital': vital.to_dict()
    }), 201


@bp.route('/members/<int:member_id>/vitals', methods=['GET'])
@login_required
def get_family_member_vitals(member_id):
    """Get vitals history for a family member"""
    member = FamilyMember.query.filter_by(id=member_id, user_id=current_user.id).first()
    if not member:
        return jsonify({'error': 'Family member not found'}), 404

    days = request.args.get('days', 30, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)

    vitals = FamilyVitalSign.query.filter(
        FamilyVitalSign.family_member_id == member.id,
        FamilyVitalSign.recorded_at >= start_date
    ).order_by(FamilyVitalSign.recorded_at.desc()).all()

    return jsonify({
        'family_member_id': member.id,
        'vitals': [v.to_dict() for v in vitals],
        'total': len(vitals)
    }), 200


@bp.route('/members/<int:member_id>/health-score/calculate', methods=['POST'])
@login_required
def calculate_family_member_health_score(member_id):
    """Calculate and save health score for a family member"""
    member = FamilyMember.query.filter_by(id=member_id, user_id=current_user.id).first()
    if not member:
        return jsonify({'error': 'Family member not found'}), 404

    latest_vital = FamilyVitalSign.query.filter_by(family_member_id=member.id).order_by(
        FamilyVitalSign.recorded_at.desc()
    ).first()

    if not latest_vital:
        return jsonify({'error': 'No vitals found. Please record vitals first.'}), 400

    cardiovascular_score = _calculate_family_cardiovascular_score(latest_vital)
    respiratory_score = _calculate_family_respiratory_score(latest_vital)
    metabolic_score = _calculate_family_metabolic_score(latest_vital)

    overall_score = round((cardiovascular_score + respiratory_score + metabolic_score) / 3, 2)
    trend = _determine_family_health_trend(member.id, new_score=overall_score)

    score = FamilyMemberHealthScore(
        family_member_id=member.id,
        score=overall_score,
        cardiovascular_score=round(cardiovascular_score, 2),
        respiratory_score=round(respiratory_score, 2),
        metabolic_score=round(metabolic_score, 2),
        trend=trend
    )

    db.session.add(score)
    db.session.flush()

    _create_family_score_alert(member, score)
    db.session.commit()

    return jsonify({
        'message': 'Health score calculated successfully',
        'health_score': score.to_dict()
    }), 201


@bp.route('/members/<int:member_id>/health-score/latest', methods=['GET'])
@login_required
def get_family_member_latest_health_score(member_id):
    """Get latest health score for a family member"""
    member = FamilyMember.query.filter_by(id=member_id, user_id=current_user.id).first()
    if not member:
        return jsonify({'error': 'Family member not found'}), 404

    score = FamilyMemberHealthScore.query.filter_by(family_member_id=member.id).order_by(
        FamilyMemberHealthScore.calculated_at.desc()
    ).first()

    return jsonify({
        'family_member_id': member.id,
        'health_score': score.to_dict() if score else None
    }), 200


@bp.route('/members/<int:member_id>/health-score/history', methods=['GET'])
@login_required
def get_family_member_health_score_history(member_id):
    """Get health score history for a family member"""
    member = FamilyMember.query.filter_by(id=member_id, user_id=current_user.id).first()
    if not member:
        return jsonify({'error': 'Family member not found'}), 404

    days = request.args.get('days', 30, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)

    scores = FamilyMemberHealthScore.query.filter(
        FamilyMemberHealthScore.family_member_id == member.id,
        FamilyMemberHealthScore.calculated_at >= start_date
    ).order_by(FamilyMemberHealthScore.calculated_at.desc()).all()

    return jsonify({
        'family_member_id': member.id,
        'health_scores': [s.to_dict() for s in scores],
        'total': len(scores)
    }), 200


@bp.route('/alerts/parents', methods=['GET'])
@login_required
def get_parent_alerts():
    """Get alerts related to parent family members"""
    include_resolved = request.args.get('include_resolved', 'false').lower() == 'true'

    query = FamilyMemberAlert.query.filter_by(
        user_id=current_user.id,
        is_parent_alert=True
    )
    if not include_resolved:
        query = query.filter_by(is_resolved=False)

    alerts = query.order_by(FamilyMemberAlert.created_at.desc()).all()

    return jsonify({
        'alerts': [
            {
                **alert.to_dict(),
                'family_member_name': alert.family_member.name,
                'relation': alert.family_member.relation
            }
            for alert in alerts
        ],
        'total': len(alerts)
    }), 200


@bp.route('/alerts/<int:alert_id>/read', methods=['POST'])
@login_required
def mark_family_alert_read(alert_id):
    """Mark a family-member alert as read"""
    alert = FamilyMemberAlert.query.filter_by(id=alert_id, user_id=current_user.id).first()
    if not alert:
        return jsonify({'error': 'Alert not found'}), 404

    alert.is_read = True
    db.session.commit()

    return jsonify({'message': 'Alert marked as read'}), 200


@bp.route('/alerts/<int:alert_id>/resolve', methods=['POST'])
@login_required
def resolve_family_alert(alert_id):
    """Resolve a family-member alert"""
    alert = FamilyMemberAlert.query.filter_by(id=alert_id, user_id=current_user.id).first()
    if not alert:
        return jsonify({'error': 'Alert not found'}), 404

    alert.is_resolved = True
    alert.resolved_at = datetime.utcnow()
    db.session.commit()

    return jsonify({'message': 'Alert resolved'}), 200


def _create_family_vital_alerts(member, vital):
    """Create alerts based on family member vital thresholds"""
    issues = []
    severity = 'warning'
    alert_type = 'warning_vitals'

    if vital.heart_rate and (vital.heart_rate < 50 or vital.heart_rate > 120):
        issues.append(f'Heart rate is abnormal ({vital.heart_rate} bpm)')
    if vital.blood_pressure_systolic and vital.blood_pressure_diastolic:
        if vital.blood_pressure_systolic >= 180 or vital.blood_pressure_diastolic >= 120:
            issues.append(f'Blood pressure is critical ({vital.blood_pressure_systolic}/{vital.blood_pressure_diastolic} mmHg)')
            severity = 'critical'
            alert_type = 'critical_vitals'
        elif vital.blood_pressure_systolic >= 140 or vital.blood_pressure_diastolic >= 90:
            issues.append(f'Blood pressure is elevated ({vital.blood_pressure_systolic}/{vital.blood_pressure_diastolic} mmHg)')
    if vital.oxygen_level and vital.oxygen_level < 92:
        issues.append(f'Oxygen level is low ({vital.oxygen_level}%)')
        severity = 'critical'
        alert_type = 'critical_vitals'
    if vital.temperature and (vital.temperature < 35.0 or vital.temperature > 39.0):
        issues.append(f'Temperature is outside safe range ({vital.temperature}°C)')
        if vital.temperature > 39.0:
            severity = 'critical'
            alert_type = 'critical_vitals'

    if not issues:
        return

    is_parent_alert = (member.relation or '').lower() in PARENT_RELATIONS

    alert = FamilyMemberAlert(
        user_id=member.user_id,
        family_member_id=member.id,
        alert_type=alert_type,
        severity=severity,
        title=f'{member.name}: Vital Sign Alert',
        message='; '.join(issues),
        is_parent_alert=is_parent_alert
    )
    db.session.add(alert)


def _create_family_score_alert(member, score):
    """Create alerts when family health score is low"""
    if score.score >= 60:
        return

    is_parent_alert = (member.relation or '').lower() in PARENT_RELATIONS
    severity = 'critical' if score.score < 40 else 'warning'

    alert = FamilyMemberAlert(
        user_id=member.user_id,
        family_member_id=member.id,
        alert_type='low_health_score',
        severity=severity,
        title=f'{member.name}: Low Health Score',
        message=f'Current health score is {score.score}/100 with a {score.trend} trend. Consider medical review.',
        is_parent_alert=is_parent_alert
    )
    db.session.add(alert)


def _calculate_family_cardiovascular_score(vital):
    score = 100.0

    if vital.heart_rate:
        if 60 <= vital.heart_rate <= 100:
            pass
        elif 50 <= vital.heart_rate < 60 or 100 < vital.heart_rate <= 110:
            score -= 10
        else:
            score -= 25

    if vital.blood_pressure_systolic and vital.blood_pressure_diastolic:
        if vital.blood_pressure_systolic < 120 and vital.blood_pressure_diastolic < 80:
            pass
        elif vital.blood_pressure_systolic < 130 and vital.blood_pressure_diastolic < 85:
            score -= 10
        elif vital.blood_pressure_systolic < 140 or vital.blood_pressure_diastolic < 90:
            score -= 20
        else:
            score -= 35

    return max(0.0, score)


def _calculate_family_respiratory_score(vital):
    score = 100.0
    if vital.oxygen_level:
        if vital.oxygen_level >= 95:
            pass
        elif vital.oxygen_level >= 92:
            score -= 15
        else:
            score -= 40

    if vital.temperature and vital.temperature > 38.5:
        score -= 10

    return max(0.0, score)


def _calculate_family_metabolic_score(vital):
    score = 100.0
    bmi_proxy = member_bmi_placeholder(vital.weight) if vital.weight else None
    if bmi_proxy:
        if bmi_proxy < 18.5 or bmi_proxy > 30:
            score -= 20
        elif bmi_proxy > 25:
            score -= 10
    return max(0.0, score)


def _determine_family_health_trend(member_id, new_score):
    recent_scores = FamilyMemberHealthScore.query.filter_by(family_member_id=member_id).order_by(
        FamilyMemberHealthScore.calculated_at.desc()
    ).limit(2).all()

    if not recent_scores:
        return 'stable'

    previous_score = recent_scores[0].score
    diff = new_score - previous_score

    if diff > 5:
        return 'improving'
    if diff < -5:
        return 'declining'
    return 'stable'


def member_bmi_placeholder(weight):
    """Use weight-only proxy when family member height is unavailable."""
    if weight is None:
        return None
    # Assumes average adult height to derive a rough proxy BMI used only for scoring trend consistency.
    return round(weight / (1.65 ** 2), 1)
