"""
Module 4: Dynamic Health Score & Trend Analysis
- Health score (0–100)
- Weekly trend graph
- Future risk forecasting
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app import db
from database.models import HealthScore, VitalSign, HealthPrediction, User
from datetime import datetime, timedelta
import json

bp = Blueprint('health_score', __name__, url_prefix='/api/health-score')

@bp.route('/calculate', methods=['POST'])
@login_required
def calculate_health_score():
    """Calculate health score for a patient"""
    data = request.get_json()
    patient_id = data.get('patient_id', current_user.id)
    
    # Check permission
    if current_user.role not in ['admin', 'doctor'] and patient_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get latest vitals
    latest_vital = VitalSign.query.filter_by(patient_id=patient_id).order_by(
        VitalSign.recorded_at.desc()
    ).first()
    
    # Get latest prediction
    latest_prediction = HealthPrediction.query.filter_by(patient_id=patient_id).order_by(
        HealthPrediction.predicted_at.desc()
    ).first()
    
    # Calculate component scores
    cardiovascular_score = calculate_cardiovascular_score(latest_vital)
    respiratory_score = calculate_respiratory_score(latest_vital)
    metabolic_score = calculate_metabolic_score(latest_prediction)
    
    # Calculate overall score (0-100)
    overall_score = (cardiovascular_score + respiratory_score + metabolic_score) / 3
    
    # Determine trend
    trend = determine_trend(patient_id)
    
    # Save health score
    health_score = HealthScore(
        patient_id=patient_id,
        score=round(overall_score, 2),
        cardiovascular_score=round(cardiovascular_score, 2),
        respiratory_score=round(respiratory_score, 2),
        metabolic_score=round(metabolic_score, 2),
        trend=trend
    )
    
    db.session.add(health_score)
    db.session.commit()
    
    return jsonify({
        'message': 'Health score calculated successfully',
        'health_score': health_score.to_dict()
    }), 201


@bp.route('/history', methods=['GET'])
@login_required
def get_health_score_history():
    """Get health score history"""
    patient_id = request.args.get('patient_id', current_user.id, type=int)
    
    # Check permission
    if current_user.role not in ['admin', 'doctor'] and patient_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    days = request.args.get('days', 30, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)
    
    scores = HealthScore.query.filter(
        HealthScore.patient_id == patient_id,
        HealthScore.calculated_at >= start_date
    ).order_by(HealthScore.calculated_at.asc()).all()
    
    return jsonify({
        'health_scores': [s.to_dict() for s in scores]
    }), 200


@bp.route('/latest', methods=['GET'])
@login_required
def get_latest_health_score():
    """Get latest health score"""
    patient_id = request.args.get('patient_id', current_user.id, type=int)
    
    # Check permission
    if current_user.role not in ['admin', 'doctor'] and patient_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    score = HealthScore.query.filter_by(patient_id=patient_id).order_by(
        HealthScore.calculated_at.desc()
    ).first()
    
    if not score:
        return jsonify({'health_score': None}), 200
    
    return jsonify({'health_score': score.to_dict()}), 200


@bp.route('/trend', methods=['GET'])
@login_required
def get_health_trend():
    """Get health trend analysis"""
    patient_id = request.args.get('patient_id', current_user.id, type=int)
    
    # Check permission
    if current_user.role not in ['admin', 'doctor'] and patient_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    weeks = request.args.get('weeks', 12, type=int)
    start_date = datetime.utcnow() - timedelta(weeks=weeks)
    
    scores = HealthScore.query.filter(
        HealthScore.patient_id == patient_id,
        HealthScore.calculated_at >= start_date
    ).order_by(HealthScore.calculated_at.asc()).all()
    
    # Group by week
    weekly_scores = {}
    for score in scores:
        week_key = score.calculated_at.strftime('%Y-W%W')
        if week_key not in weekly_scores:
            weekly_scores[week_key] = []
        weekly_scores[week_key].append(score.score)
    
    # Calculate weekly averages
    trend_data = []
    for week, scores_list in sorted(weekly_scores.items()):
        trend_data.append({
            'week': week,
            'average_score': round(sum(scores_list) / len(scores_list), 2),
            'min_score': round(min(scores_list), 2),
            'max_score': round(max(scores_list), 2)
        })
    
    # Future forecast (simple linear regression)
    forecast = forecast_future_score(trend_data, weeks=4)
    
    return jsonify({
        'trend_data': trend_data,
        'forecast': forecast,
        'period_weeks': weeks
    }), 200


def calculate_cardiovascular_score(vital):
    """Calculate cardiovascular health score"""
    if not vital:
        return 70.0  # Default neutral score
    
    score = 100.0
    
    # Heart rate assessment
    if vital.heart_rate:
        if 60 <= vital.heart_rate <= 100:
            score -= 0
        elif 50 <= vital.heart_rate < 60 or 100 < vital.heart_rate <= 110:
            score -= 10
        else:
            score -= 25
    
    # Blood pressure assessment
    if vital.blood_pressure_systolic and vital.blood_pressure_diastolic:
        if vital.blood_pressure_systolic < 120 and vital.blood_pressure_diastolic < 80:
            score -= 0
        elif vital.blood_pressure_systolic < 130 and vital.blood_pressure_diastolic < 85:
            score -= 10
        elif vital.blood_pressure_systolic < 140 or vital.blood_pressure_diastolic < 90:
            score -= 20
        else:
            score -= 35
    
    return max(0, score)


def calculate_respiratory_score(vital):
    """Calculate respiratory health score"""
    if not vital:
        return 70.0
    
    score = 100.0
    
    # Oxygen level assessment
    if vital.oxygen_level:
        if vital.oxygen_level >= 95:
            score -= 0
        elif vital.oxygen_level >= 92:
            score -= 15
        else:
            score -= 40
    
    return max(0, score)


def calculate_metabolic_score(prediction):
    """Calculate metabolic health score based on risk prediction"""
    if not prediction:
        return 70.0
    
    # Convert risk probability to score (inverse relationship)
    risk_prob = prediction.risk_probability
    score = 100 * (1 - risk_prob)
    
    return max(0, score)


def determine_trend(patient_id):
    """Determine health score trend"""
    # Get last 3 scores
    recent_scores = HealthScore.query.filter_by(patient_id=patient_id).order_by(
        HealthScore.calculated_at.desc()
    ).limit(3).all()
    
    if len(recent_scores) < 2:
        return 'stable'
    
    # Calculate trend
    score_diff = recent_scores[0].score - recent_scores[-1].score
    
    if score_diff > 5:
        return 'improving'
    elif score_diff < -5:
        return 'declining'
    else:
        return 'stable'


def forecast_future_score(trend_data, weeks=4):
    """Simple linear forecast for future scores"""
    if len(trend_data) < 2:
        return []
    
    # Simple linear regression
    x_values = list(range(len(trend_data)))
    y_values = [d['average_score'] for d in trend_data]
    
    n = len(x_values)
    sum_x = sum(x_values)
    sum_y = sum(y_values)
    sum_xy = sum(x * y for x, y in zip(x_values, y_values))
    sum_x2 = sum(x ** 2 for x in x_values)
    
    # Calculate slope and intercept
    slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
    intercept = (sum_y - slope * sum_x) / n
    
    # Generate forecast
    forecast = []
    for i in range(1, weeks + 1):
        future_x = len(trend_data) + i
        future_score = slope * future_x + intercept
        forecast.append({
            'week_offset': i,
            'predicted_score': round(max(0, min(100, future_score)), 2)
        })
    
    return forecast
