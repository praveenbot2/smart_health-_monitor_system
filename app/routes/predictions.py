"""
Module 3: AI-Based Health Risk Prediction
- Machine Learning model integration
- Risk classification (Low / Medium / High)
- Probability estimation
- Model evaluation metrics
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app import db
from database.models import HealthPrediction, VitalSign, User
from app.ml.predictor import HealthRiskPredictor
from datetime import datetime, timedelta
import json

bp = Blueprint('predictions', __name__, url_prefix='/api/predictions')

# Initialize predictor
predictor = HealthRiskPredictor()

@bp.route('/predict', methods=['POST'])
@login_required
def predict_health_risk():
    """Predict health risk for a patient"""
    data = request.get_json()
    patient_id = data.get('patient_id', current_user.id)
    
    # Check permission
    if current_user.role not in ['admin', 'doctor'] and patient_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get patient info
    patient = User.query.get(patient_id)
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    
    # Calculate age if date of birth available
    age = data.get('age')
    if not age and patient.date_of_birth:
        today = datetime.today()
        age = today.year - patient.date_of_birth.year - (
            (today.month, today.day) < (patient.date_of_birth.month, patient.date_of_birth.day)
        )
    
    # Prepare features for prediction
    features = {
        'age': age or 30,
        'bmi': data.get('bmi', 25.0),
        'heart_rate': data.get('heart_rate', 75),
        'blood_pressure_systolic': data.get('blood_pressure_systolic', 120),
        'blood_pressure_diastolic': data.get('blood_pressure_diastolic', 80),
        'oxygen_level': data.get('oxygen_level', 98.0),
        'cholesterol': data.get('cholesterol', 200.0),
        'glucose': data.get('glucose', 100.0)
    }
    
    # Get latest vitals if not provided
    if not all([features['heart_rate'], features['blood_pressure_systolic'], 
                features['blood_pressure_diastolic'], features['oxygen_level']]):
        latest_vital = VitalSign.query.filter_by(patient_id=patient_id).order_by(
            VitalSign.recorded_at.desc()
        ).first()
        
        if latest_vital:
            features['heart_rate'] = latest_vital.heart_rate or features['heart_rate']
            features['blood_pressure_systolic'] = latest_vital.blood_pressure_systolic or features['blood_pressure_systolic']
            features['blood_pressure_diastolic'] = latest_vital.blood_pressure_diastolic or features['blood_pressure_diastolic']
            features['oxygen_level'] = latest_vital.oxygen_level or features['oxygen_level']
    
    # Make prediction
    prediction_result = predictor.predict(features)
    
    # Save prediction
    prediction = HealthPrediction(
        patient_id=patient_id,
        risk_level=prediction_result['risk_level'],
        risk_probability=prediction_result['risk_probability'],
        predicted_conditions=json.dumps(prediction_result['predicted_conditions']),
        contributing_factors=json.dumps(prediction_result['contributing_factors']),
        model_version=prediction_result['model_version'],
        confidence_score=prediction_result['confidence_score'],
        **features
    )
    
    db.session.add(prediction)
    db.session.commit()
    
    # Create alert if high risk
    if prediction_result['risk_level'] == 'high':
        from database.models import Alert
        alert = Alert(
            patient_id=patient_id,
            alert_type='high_risk',
            severity='warning',
            title='High Health Risk Detected',
            message=f"AI prediction shows high health risk ({prediction_result['risk_probability']:.1%}). Please consult a doctor."
        )
        db.session.add(alert)
        db.session.commit()
    
    return jsonify({
        'message': 'Prediction completed successfully',
        'prediction': prediction.to_dict(),
        'details': prediction_result
    }), 201


@bp.route('/history', methods=['GET'])
@login_required
def get_prediction_history():
    """Get prediction history for a patient"""
    patient_id = request.args.get('patient_id', current_user.id, type=int)
    
    # Check permission
    if current_user.role not in ['admin', 'doctor'] and patient_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    limit = request.args.get('limit', 10, type=int)
    
    predictions = HealthPrediction.query.filter_by(patient_id=patient_id).order_by(
        HealthPrediction.predicted_at.desc()
    ).limit(limit).all()
    
    return jsonify({
        'predictions': [p.to_dict() for p in predictions]
    }), 200


@bp.route('/latest', methods=['GET'])
@login_required
def get_latest_prediction():
    """Get latest prediction for a patient"""
    patient_id = request.args.get('patient_id', current_user.id, type=int)
    
    # Check permission
    if current_user.role not in ['admin', 'doctor'] and patient_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    prediction = HealthPrediction.query.filter_by(patient_id=patient_id).order_by(
        HealthPrediction.predicted_at.desc()
    ).first()
    
    if not prediction:
        return jsonify({'prediction': None}), 200
    
    return jsonify({'prediction': prediction.to_dict()}), 200


@bp.route('/statistics', methods=['GET'])
@login_required
def get_prediction_statistics():
    """Get prediction statistics for a patient"""
    patient_id = request.args.get('patient_id', current_user.id, type=int)
    
    # Check permission
    if current_user.role not in ['admin', 'doctor'] and patient_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    days = request.args.get('days', 30, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)
    
    predictions = HealthPrediction.query.filter(
        HealthPrediction.patient_id == patient_id,
        HealthPrediction.predicted_at >= start_date
    ).all()
    
    if not predictions:
        return jsonify({'statistics': None}), 200
    
    # Calculate statistics
    risk_counts = {'low': 0, 'medium': 0, 'high': 0}
    total_probability = 0
    
    for pred in predictions:
        risk_counts[pred.risk_level] += 1
        total_probability += pred.risk_probability
    
    stats = {
        'total_predictions': len(predictions),
        'risk_distribution': risk_counts,
        'average_risk_probability': round(total_probability / len(predictions), 3),
        'latest_risk_level': predictions[0].risk_level if predictions else None,
        'period_days': days
    }
    
    return jsonify({'statistics': stats}), 200


@bp.route('/model/info', methods=['GET'])
def get_model_info():
    """Get ML model information"""
    model_info = predictor.get_model_info()
    return jsonify({'model_info': model_info}), 200


@bp.route('/model/retrain', methods=['POST'])
def retrain_model():
    """Retrain the ML model with new data"""
    try:
        result = predictor.retrain_model()
        return jsonify({
            'message': 'Model retrained successfully',
            'result': result
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
