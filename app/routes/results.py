"""
Health Results & Risk Assessment Module
- Display health risk levels
- Provide detailed analysis and recommendations
- Health score calculation
- Risk-based medical advice
- Result export and sharing
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app import db
from database.models import User, HealthPrediction, VitalSign, MedicalReport, HealthScore
from ai_modules.gemini_api import get_gemini_assistant
from datetime import datetime, timedelta
import json

bp = Blueprint('results', __name__, url_prefix='/api/results')
gemini = get_gemini_assistant()


# Risk level descriptions and recommendations
RISK_LEVELS = {
    'low': {
        'display_name': 'Low Risk',
        'color': '#10b981',
        'icon': '✓',
        'description': 'Your health indicators are within normal ranges',
        'recommendations': [
            'Maintain your current lifestyle habits',
            'Continue regular health monitoring',
            'Annual health checkup recommended',
            'Stay active with 150 min/week exercise',
            'Balanced nutritional diet'
        ]
    },
    'medium': {
        'display_name': 'Moderate Risk',
        'color': '#f59e0b',
        'icon': '!',
        'description': 'Some health indicators need attention',
        'recommendations': [
            'Schedule a doctor consultation',
            'Monitor vitals more frequently (weekly)',
            'Lifestyle modifications recommended',
            'Reduce stress through meditation/yoga',
            'Improve diet and exercise routine'
        ]
    },
    'high': {
        'display_name': 'High Risk',
        'color': '#ef4444',
        'icon': '⚠',
        'description': 'Significant health concerns requiring medical attention',
        'recommendations': [
            'Schedule appointment with specialist urgently',
            'Monitor vitals daily',
            'Follow medical treatment plan strictly',
            'Medication compliance critical',
            'Frequent medical consultations required'
        ]
    },
    'critical': {
        'display_name': 'Critical Risk',
        'color': '#dc2626',
        'icon': '⚠️',
        'description': 'Urgent medical attention required',
        'recommendations': [
            'SEEK IMMEDIATE MEDICAL ATTENTION',
            'Go to nearest emergency room or call 911',
            'Monitor vitals continuously',
            'Follow physician orders strictly',
            'Regular emergency follow-ups'
        ]
    }
}


@bp.route('/latest', methods=['GET'])
@login_required
def get_latest_results():
    """Get the latest health assessment results"""
    try:
        # Get latest prediction
        prediction = HealthPrediction.query.filter_by(patient_id=current_user.id).order_by(
            HealthPrediction.predicted_at.desc()
        ).first()
        
        if not prediction:
            return jsonify({
                'result': None,
                'message': 'No health assessment available. Please complete your first assessment.',
                'success': True
            }), 200
        
        # Get risk level info
        risk_info = RISK_LEVELS.get(prediction.risk_level.lower(), RISK_LEVELS['medium'])
        
        # Get latest vitals
        vital = VitalSign.query.filter_by(patient_id=current_user.id).order_by(
            VitalSign.timestamp.desc()
        ).first()
        
        result = {
            'assessment_id': prediction.id,
            'assessed_at': prediction.predicted_at.isoformat(),
            'risk_level': prediction.risk_level.capitalize(),
            'risk_score': prediction.risk_score,
            'risk_percentage': min(100, max(0, prediction.risk_score)),
            'display_info': risk_info,
            'vitals_summary': {
                'heart_rate': vital.heart_rate if vital else None,
                'blood_pressure': f"{vital.blood_pressure_systolic}/{vital.blood_pressure_diastolic}" if vital and vital.blood_pressure_systolic else None,
                'temperature': vital.temperature if vital else None,
                'oxygen_saturation': vital.oxygen_saturation if vital else None,
                'measured_at': vital.timestamp.isoformat() if vital else None
            },
            'contributing_factors': json.loads(prediction.contributing_factors) if prediction.contributing_factors else [],
            'recommendations': risk_info['recommendations'],
            'action_required': prediction.risk_level.lower() in ['high', 'critical']
        }
        
        return jsonify({
            'result': result,
            'success': True
        }), 200
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@bp.route('/assessment/<int:assessment_id>', methods=['GET'])
@login_required
def get_assessment_result(assessment_id):
    """Get detailed assessment result by ID"""
    try:
        prediction = HealthPrediction.query.get(assessment_id)
        
        if not prediction:
            return jsonify({'error': 'Assessment not found', 'success': False}), 404
        
        if prediction.patient_id != current_user.id and current_user.role != 'admin':
            return jsonify({'error': 'Unauthorized', 'success': False}), 403
        
        # Get risk info
        risk_info = RISK_LEVELS.get(prediction.risk_level.lower(), RISK_LEVELS['medium'])
        
        result = {
            'assessment_id': prediction.id,
            'patient_name': prediction.patient.full_name,
            'assessed_at': prediction.predicted_at.isoformat(),
            'risk_level': prediction.risk_level.capitalize(),
            'risk_score': prediction.risk_score,
            'risk_percentage': min(100, max(0, prediction.risk_score)),
            'display_info': risk_info,
            'contributing_factors': json.loads(prediction.contributing_factors) if prediction.contributing_factors else [],
            'recommendations': risk_info['recommendations'],
            'detailed_analysis': prediction.detailed_analysis if hasattr(prediction, 'detailed_analysis') else None,
            'action_required': prediction.risk_level.lower() in ['high', 'critical']
        }
        
        return jsonify({
            'result': result,
            'success': True
        }), 200
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@bp.route('/history', methods=['GET'])
@login_required
def get_assessment_history():
    """
    Get history of health assessments
    
    Query params:
    - limit: max results (default: 20)
    - days: last n days (default: 90)
    """
    try:
        limit = request.args.get('limit', 20, type=int)
        days = request.args.get('days', 90, type=int)
        
        since = datetime.utcnow() - timedelta(days=days)
        
        predictions = HealthPrediction.query.filter_by(patient_id=current_user.id).filter(
            HealthPrediction.predicted_at >= since
        ).order_by(HealthPrediction.predicted_at.desc()).limit(limit).all()
        
        history = []
        for pred in predictions:
            risk_info = RISK_LEVELS.get(pred.risk_level.lower(), RISK_LEVELS['medium'])
            history.append({
                'id': pred.id,
                'assessed_at': pred.predicted_at.isoformat(),
                'risk_level': pred.risk_level.capitalize(),
                'risk_score': pred.risk_score,
                'color': risk_info['color'],
                'contributing_factors': json.loads(pred.contributing_factors) if pred.contributing_factors else []
            })
        
        return jsonify({
            'history': history,
            'count': len(history),
            'success': True
        }), 200
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@bp.route('/detailed-analysis', methods=['POST'])
@login_required
def get_detailed_analysis():
    """
    Get AI-powered detailed analysis of health results
    
    Expected JSON:
    {
        "assessment_id": 123,  # optional, uses latest if not provided
        "focus_areas": ["heart", "blood_pressure"]  # optional
    }
    """
    try:
        data = request.get_json() or {}
        assessment_id = data.get('assessment_id')
        focus_areas = data.get('focus_areas', [])
        
        # Get assessment
        if assessment_id:
            prediction = HealthPrediction.query.get(assessment_id)
            if not prediction:
                return jsonify({'error': 'Assessment not found', 'success': False}), 404
        else:
            prediction = HealthPrediction.query.filter_by(patient_id=current_user.id).order_by(
                HealthPrediction.predicted_at.desc()
            ).first()
        
        if not prediction:
            return jsonify({'error': 'No assessment available', 'success': False}), 404
        
        # Get patient context
        user = User.query.get(current_user.id)
        vital = VitalSign.query.filter_by(patient_id=current_user.id).order_by(
            VitalSign.timestamp.desc()
        ).first()
        
        patient_context = {
            'vital_signs': {
                'heart_rate': vital.heart_rate if vital else None,
                'blood_pressure': f"{vital.blood_pressure_systolic}/{vital.blood_pressure_diastolic}" if vital and vital.blood_pressure_systolic else None,
                'temperature': vital.temperature if vital else None,
                'oxygen_level': vital.oxygen_saturation if vital else None,
                'glucose': vital.blood_glucose if vital else None
            } if vital else {},
            'medical_history': user.medical_history if hasattr(user, 'medical_history') else None
        }
        
        # Build analysis prompt
        focus_text = f" Focus on: {', '.join(focus_areas)}" if focus_areas else ""
        
        prompt = f"""Provide a detailed health analysis for this patient:

Risk Level: {prediction.risk_level}
Risk Score: {prediction.risk_score}/100
Assessment Date: {prediction.predicted_at.isoformat()}
Contributing Factors: {json.loads(prediction.contributing_factors) if prediction.contributing_factors else []}
Patient Context: {json.dumps(patient_context)}

{focus_text}

Please provide:
1. **Detailed Interpretation**: What do these results mean?
2. **Primary Concerns**: Main health issues identified
3. **Actionable Steps**: Specific actions patient should take
4. **Timeline for Improvement**: Expected recovery/improvement timeframe
5. **Specialist Recommendations**: Who should the patient consult?
6. **Lifestyle Modifications**: Specific diet, exercise, habit changes
7. **Monitoring Plan**: What to track and how often"""
        
        # Get AI analysis
        response = gemini.model.generate_content(prompt) if gemini.model else None
        
        if response:
            analysis = response.text
        else:
            analysis = "AI analysis unavailable - using standard recommendations"
        
        # Get risk info
        risk_info = RISK_LEVELS.get(prediction.risk_level.lower(), RISK_LEVELS['medium'])
        
        return jsonify({
            'risk_level': prediction.risk_level.capitalize(),
            'risk_score': prediction.risk_score,
            'detailed_analysis': analysis,
            'recommendations': risk_info['recommendations'],
            'contributing_factors': json.loads(prediction.contributing_factors) if prediction.contributing_factors else [],
            'success': True
        }), 200
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@bp.route('/health-score', methods=['GET'])
@login_required
def get_health_score():
    """Get overall health score"""
    try:
        # Calculate health score from latest data
        latest_prediction = HealthPrediction.query.filter_by(patient_id=current_user.id).order_by(
            HealthPrediction.predicted_at.desc()
        ).first()
        
        latest_vital = VitalSign.query.filter_by(patient_id=current_user.id).order_by(
            VitalSign.timestamp.desc()
        ).first()
        
        # Score calculation (0-100)
        base_score = 100
        
        # Deduct based on risk
        if latest_prediction:
            risk_deductions = {
                'low': 0,
                'medium': 15,
                'high': 35,
                'critical': 50
            }
            base_score -= risk_deductions.get(latest_prediction.risk_level.lower(), 20)
        
        # Deduct based on vital abnormalities
        if latest_vital:
            abnormalities = 0
            if latest_vital.heart_rate and (latest_vital.heart_rate < 60 or latest_vital.heart_rate > 100):
                abnormalities += 1
            if latest_vital.blood_pressure_systolic and (latest_vital.blood_pressure_systolic > 140):
                abnormalities += 1
            if latest_vital.temperature and (latest_vital.temperature > 37.5 or latest_vital.temperature < 36.1):
                abnormalities += 1
            if latest_vital.oxygen_saturation and (latest_vital.oxygen_saturation < 95):
                abnormalities += 2
            
            base_score -= (abnormalities * 3)
        
        health_score = max(0, min(100, base_score))
        
        # Determine score grade
        if health_score >= 80:
            grade = 'A'
            status = 'Excellent'
        elif health_score >= 70:
            grade = 'B'
            status = 'Good'
        elif health_score >= 60:
            grade = 'C'
            status = 'Fair'
        elif health_score >= 50:
            grade = 'D'
            status = 'Poor'
        else:
            grade = 'F'
            status = 'Critical'
        
        return jsonify({
            'score': health_score,
            'grade': grade,
            'status': status,
            'assessed_at': datetime.utcnow().isoformat(),
            'success': True
        }), 200
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@bp.route('/comparison', methods=['GET'])
@login_required
def compare_assessments():
    """
    Compare two health assessments
    
    Query params:
    - assessment1_id: first assessment ID (optional, uses latest)
    - assessment2_id: second assessment ID (optional, uses second latest)
    """
    try:
        assessment1_id = request.args.get('assessment1_id', type=int)
        assessment2_id = request.args.get('assessment2_id', type=int)
        
        # Get assessments
        predictions = HealthPrediction.query.filter_by(patient_id=current_user.id).order_by(
            HealthPrediction.predicted_at.desc()
        ).limit(2).all()
        
        if len(predictions) < 2:
            return jsonify({
                'message': 'Need at least 2 assessments for comparison',
                'success': True
            }), 200
        
        if assessment1_id:
            pred1 = HealthPrediction.query.get(assessment1_id)
        else:
            pred1 = predictions[0]
        
        if assessment2_id:
            pred2 = HealthPrediction.query.get(assessment2_id)
        else:
            pred2 = predictions[1]
        
        # Compare
        comparison = {
            'assessment1': {
                'id': pred1.id,
                'date': pred1.predicted_at.isoformat(),
                'risk_level': pred1.risk_level.capitalize(),
                'risk_score': pred1.risk_score
            },
            'assessment2': {
                'id': pred2.id,
                'date': pred2.predicted_at.isoformat(),
                'risk_level': pred2.risk_level.capitalize(),
                'risk_score': pred2.risk_score
            },
            'score_change': pred1.risk_score - pred2.risk_score,
            'score_trend': 'improved' if pred1.risk_score < pred2.risk_score else 'worsened' if pred1.risk_score > pred2.risk_score else 'stable',
            'analysis': f"Your health score has {('improved' if pred1.risk_score < pred2.risk_score else 'worsened') if pred1.risk_score != pred2.risk_score else 'remained'} by {abs(pred1.risk_score - pred2.risk_score)} points."
        }
        
        return jsonify({
            'comparison': comparison,
            'success': True
        }), 200
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@bp.route('/export', methods=['GET'])
@login_required
def export_results():
    """Export health results as JSON"""
    try:
        prediction = HealthPrediction.query.filter_by(patient_id=current_user.id).order_by(
            HealthPrediction.predicted_at.desc()
        ).first()
        
        if not prediction:
            return jsonify({'error': 'No results to export', 'success': False}), 404
        
        risk_info = RISK_LEVELS.get(prediction.risk_level.lower(), RISK_LEVELS['medium'])
        
        export_data = {
            'export_date': datetime.utcnow().isoformat(),
            'patient_name': current_user.full_name,
            'assessment': {
                'assessed_at': prediction.predicted_at.isoformat(),
                'risk_level': prediction.risk_level.capitalize(),
                'risk_score': prediction.risk_score,
                'contributing_factors': json.loads(prediction.contributing_factors) if prediction.contributing_factors else [],
                'recommendations': risk_info['recommendations']
            }
        }
        
        return jsonify(export_data), 200
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500
