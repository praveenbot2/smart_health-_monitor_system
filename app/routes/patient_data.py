"""
Patient Data Collection & Analysis Module
- Collect comprehensive patient information
- Store health metrics
- Analyze health trends
- Generate risk predictions
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app import db, socketio
from database.models import User, VitalSign, HealthPrediction, Alert
from datetime import datetime, timedelta, date
import json
import csv
import io
import importlib.util
import os
import numpy as np
from statistics import mean, stdev

# Load predictor module
spec = importlib.util.spec_from_file_location(
    "prediction", 
    os.path.join(os.path.dirname(__file__), "../../ai_modules/prediction.py")
)
prediction_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prediction_module)
HealthRiskPredictor = prediction_module.HealthRiskPredictor

bp = Blueprint('patient_data', __name__, url_prefix='/api/patients')


@bp.route('/profile/update', methods=['POST'])
@login_required
def update_patient_profile():
    """
    Update patient profile with demographic information
    
    Expected JSON:
    {
        "full_name": "John Doe",
        "date_of_birth": "1980-05-15",
        "gender": "M",
        "phone": "1234567890",
        "address": "123 Main St",
        "medical_history": "Asthma, Allergies",
        "current_medications": "Aspirin, Vitamin D"
    }
    """
    try:
        data = request.get_json()
        patient = current_user
        
        # Update basic info
        if 'full_name' in data:
            patient.full_name = data['full_name']
        if 'date_of_birth' in data:
            dob = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
            patient.date_of_birth = dob
        if 'gender' in data:
            patient.gender = data['gender']
        if 'phone' in data:
            patient.phone = data['phone']
        if 'address' in data:
            patient.address = data['address']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Patient profile updated successfully',
            'patient': patient.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@bp.route('/health-data/submit', methods=['POST'])
@login_required
def submit_health_data():
    """
    Submit comprehensive health data for a patient
    
    Expected JSON:
    {
        "heart_rate": 72,
        "blood_pressure_systolic": 120,
        "blood_pressure_diastolic": 80,
        "oxygen_level": 98,
        "temperature": 37.0,
        "weight": 75.5,
        "height": 1.75,
        "cholesterol": 200,
        "glucose": 100,
        "notes": "Regular checkup"
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = [
            'heart_rate', 'blood_pressure_systolic', 'blood_pressure_diastolic',
            'oxygen_level', 'weight', 'height'
        ]
        
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Create vital sign record
        vital = VitalSign(
            patient_id=current_user.id,
            heart_rate=data.get('heart_rate'),
            blood_pressure_systolic=data.get('blood_pressure_systolic'),
            blood_pressure_diastolic=data.get('blood_pressure_diastolic'),
            oxygen_level=data.get('oxygen_level'),
            temperature=data.get('temperature'),
            weight=data.get('weight'),
            height=data.get('height'),
            cholesterol=data.get('cholesterol'),
            glucose=data.get('glucose'),
            notes=data.get('notes'),
            source=data.get('source', 'manual')
        )
        
        db.session.add(vital)
        db.session.commit()
        
        # Automatically generate prediction
        prediction_result = generate_prediction_for_patient(current_user.id, vital)
        
        return jsonify({
            'message': 'Health data submitted successfully',
            'vital_id': vital.id,
            'vital': vital.to_dict(),
            'prediction': prediction_result
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@bp.route('/analyze', methods=['GET'])
@login_required
def analyze_patient_health():
    """
    Analyze patient's health data and trends
    
    Query Parameters:
    - days: Number of days to analyze (default: 30)
    """
    try:
        days = request.args.get('days', 30, type=int)
        patient_id = current_user.id
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get all vitals in period
        vitals = VitalSign.query.filter(
            VitalSign.patient_id == patient_id,
            VitalSign.recorded_at >= start_date
        ).order_by(VitalSign.recorded_at.desc()).all()
        
        if not vitals:
            return jsonify({'error': 'No health data available for analysis'}), 404
        
        # Calculate statistics
        analysis = calculate_health_statistics(vitals)
        
        # Get latest prediction
        latest_prediction = HealthPrediction.query.filter_by(
            patient_id=patient_id
        ).order_by(HealthPrediction.predicted_at.desc()).first()
        
        return jsonify({
            'patient_id': patient_id,
            'period_days': days,
            'total_records': len(vitals),
            'analysis': analysis,
            'latest_prediction': latest_prediction.to_dict() if latest_prediction else None
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/predict', methods=['POST'])
@login_required
def predict_patient_health():
    """
    Generate health risk prediction for patient
    
    Expected JSON (optional - uses latest vitals if not provided):
    {
        "age": 45,
        "bmi": 28.5,
        "heart_rate": 82,
        "blood_pressure_systolic": 135,
        "blood_pressure_diastolic": 88,
        "oxygen_level": 96,
        "cholesterol": 220,
        "glucose": 115
    }
    """
    try:
        data = request.get_json()
        
        # If no data provided, use latest vitals
        if not data:
            vital = VitalSign.query.filter_by(
                patient_id=current_user.id
            ).order_by(VitalSign.recorded_at.desc()).first()
            
            if not vital:
                return jsonify({'error': 'No vital signs recorded'}), 404
        else:
            vital = data
        
        # Generate prediction
        prediction = generate_prediction_for_patient(current_user.id, vital)
        
        return jsonify(prediction), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/bulk-import', methods=['POST'])
@login_required
def bulk_import_patients():
    """
    Bulk import patient data from CSV
    
    CSV Format:
    name,age,gender,heart_rate,blood_pressure_systolic,blood_pressure_diastolic,oxygen_level,weight,height,cholesterol,glucose
    John Doe,45,M,72,120,80,98,75.5,1.75,200,100
    """
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Parse CSV
        stream = io.StringIO(file.stream.read().decode('UTF8'), newline=None)
        csv_reader = csv.DictReader(stream)
        
        imported = 0
        errors = []
        
        for row_num, row in enumerate(csv_reader, 1):
            try:
                # Check for admin permission
                if current_user.role not in ['admin', 'doctor']:
                    return jsonify({'error': 'Only admins/doctors can bulk import'}), 403
                
                # Parse patient data
                name = row.get('name', '')
                age = int(row.get('age', 30))
                gender = row.get('gender', 'M')
                
                # Try to find existing user or create new one
                user = User.query.filter_by(username=name.lower().replace(' ', '_')).first()
                if not user:
                    user = User(
                        username=f"{name.lower().replace(' ', '_')}_{imported}",
                        email=f"{name.lower().replace(' ', '_')}_{imported}@patient.local",
                        full_name=name,
                        gender=gender,
                        role='patient'
                    )
                    user.set_password('temp_password_123')
                    db.session.add(user)
                    db.session.flush()
                
                # Create vital record
                vital = VitalSign(
                    patient_id=user.id,
                    heart_rate=int(row.get('heart_rate', 75)),
                    blood_pressure_systolic=int(row.get('blood_pressure_systolic', 120)),
                    blood_pressure_diastolic=int(row.get('blood_pressure_diastolic', 80)),
                    oxygen_level=float(row.get('oxygen_level', 98)),
                    weight=float(row.get('weight', 70)),
                    height=float(row.get('height', 1.75)),
                    cholesterol=float(row.get('cholesterol', 200)),
                    glucose=float(row.get('glucose', 100)),
                    source='bulk_import'
                )
                db.session.add(vital)
                imported += 1
                
            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")
        
        db.session.commit()
        
        return jsonify({
            'message': f'Imported {imported} patients successfully',
            'imported': imported,
            'errors': errors
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Import failed: {str(e)}'}), 500


@bp.route('/export', methods=['GET'])
@login_required
def export_patient_data():
    """
    Export patient's health data as CSV
    """
    try:
        days = request.args.get('days', 90, type=int)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        vitals = VitalSign.query.filter(
            VitalSign.patient_id == current_user.id,
            VitalSign.recorded_at >= start_date
        ).order_by(VitalSign.recorded_at.asc()).all()
        
        if not vitals:
            return jsonify({'error': 'No data to export'}), 404
        
        # Create CSV
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            'date', 'heart_rate', 'blood_pressure_systolic', 'blood_pressure_diastolic',
            'oxygen_level', 'temperature', 'weight', 'height', 'cholesterol', 'glucose'
        ])
        
        writer.writeheader()
        for vital in vitals:
            writer.writerow({
                'date': vital.recorded_at.isoformat(),
                'heart_rate': vital.heart_rate,
                'blood_pressure_systolic': vital.blood_pressure_systolic,
                'blood_pressure_diastolic': vital.blood_pressure_diastolic,
                'oxygen_level': vital.oxygen_level,
                'temperature': vital.temperature,
                'weight': vital.weight,
                'height': vital.height,
                'cholesterol': vital.cholesterol,
                'glucose': vital.glucose
            })
        
        return output.getvalue(), 200, {
            'Content-Disposition': f'attachment; filename=patient_data_{current_user.id}.csv',
            'Content-Type': 'text/csv'
        }
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/health-summary', methods=['GET'])
@login_required
def get_health_summary():
    """
    Get comprehensive health summary for patient
    """
    try:
        patient = current_user
        
        # Get basic info
        age = None
        if patient.date_of_birth:
            today = date.today()
            age = today.year - patient.date_of_birth.year - (
                (today.month, today.day) < (patient.date_of_birth.month, patient.date_of_birth.day)
            )
        
        # Get latest vitals
        latest_vital = VitalSign.query.filter_by(
            patient_id=patient.id
        ).order_by(VitalSign.recorded_at.desc()).first()
        
        # Get latest prediction
        latest_prediction = HealthPrediction.query.filter_by(
            patient_id=patient.id
        ).order_by(HealthPrediction.predicted_at.desc()).first()
        
        # Get recent alerts
        recent_alerts = Alert.query.filter_by(
            patient_id=patient.id
        ).order_by(Alert.created_at.desc()).limit(5).all()
        
        return jsonify({
            'patient': {
                'id': patient.id,
                'name': patient.full_name or patient.username,
                'age': age,
                'gender': patient.gender,
                'email': patient.email,
                'phone': patient.phone
            },
            'latest_vital': latest_vital.to_dict() if latest_vital else None,
            'latest_prediction': latest_prediction.to_dict() if latest_prediction else None,
            'recent_alerts': [alert.to_dict() for alert in recent_alerts]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Helper Functions

def calculate_health_statistics(vitals):
    """Calculate health statistics from vital signs"""
    if not vitals:
        return {}
    
    hr_values = [v.heart_rate for v in vitals if v.heart_rate]
    bp_sys_values = [v.blood_pressure_systolic for v in vitals if v.blood_pressure_systolic]
    bp_dias_values = [v.blood_pressure_diastolic for v in vitals if v.blood_pressure_diastolic]
    o2_values = [v.oxygen_level for v in vitals if v.oxygen_level]
    weight_values = [v.weight for v in vitals if v.weight]
    glucose_values = [v.glucose for v in vitals if v.glucose]
    
    def get_stats(values):
        if not values:
            return None
        return {
            'min': round(min(values), 2),
            'max': round(max(values), 2),
            'avg': round(mean(values), 2),
            'latest': round(values[0], 2)
        }
    
    return {
        'heart_rate': get_stats(hr_values),
        'blood_pressure_systolic': get_stats(bp_sys_values),
        'blood_pressure_diastolic': get_stats(bp_dias_values),
        'oxygen_level': get_stats(o2_values),
        'weight': get_stats(weight_values),
        'glucose': get_stats(glucose_values),
        'bmi': calculate_bmi(weight_values[-1] if weight_values else None, 
                           vitals[0].height if vitals[0].height else None)
    }


def calculate_bmi(weight_kg, height_m):
    """Calculate BMI"""
    if weight_kg and height_m and height_m > 0:
        return round(weight_kg / (height_m ** 2), 2)
    return None


def generate_prediction_for_patient(patient_id, vital_data):
    """Generate and store health prediction"""
    try:
        patient = User.query.get(patient_id)
        
        # Calculate age
        age = 30
        if patient.date_of_birth:
            today = date.today()
            age = today.year - patient.date_of_birth.year - (
                (today.month, today.day) < (patient.date_of_birth.month, patient.date_of_birth.day)
            )
        
        # Get height and weight for BMI
        height = vital_data.height if hasattr(vital_data, 'height') else 1.75
        weight = vital_data.weight if hasattr(vital_data, 'weight') else 70
        bmi = calculate_bmi(weight, height)
        
        # Prepare features
        features = {
            'age': age,
            'bmi': bmi or 25,
            'heart_rate': vital_data.heart_rate or 75,
            'blood_pressure_systolic': vital_data.blood_pressure_systolic or 120,
            'blood_pressure_diastolic': vital_data.blood_pressure_diastolic or 80,
            'oxygen_level': vital_data.oxygen_level or 98,
            'cholesterol': vital_data.cholesterol or 200,
            'glucose': vital_data.glucose or 100
        }
        
        # Run prediction
        predictor = HealthRiskPredictor()
        prediction = predictor.predict(features)
        
        # Store prediction
        health_pred = HealthPrediction(
            patient_id=patient_id,
            risk_level=prediction['risk_level'],
            risk_probability=prediction['risk_probability'],
            predicted_conditions=json.dumps(prediction.get('predicted_conditions', [])),
            contributing_factors=json.dumps(prediction.get('contributing_factors', [])),
            model_version=prediction.get('model_version', '1.0.0'),
            confidence_score=prediction.get('confidence_score', 0.0),
            age=features['age'],
            bmi=features['bmi'],
            heart_rate=features['heart_rate'],
            blood_pressure_systolic=features['blood_pressure_systolic'],
            blood_pressure_diastolic=features['blood_pressure_diastolic'],
            oxygen_level=features['oxygen_level'],
            cholesterol=features['cholesterol'],
            glucose=features['glucose']
        )
        db.session.add(health_pred)
        db.session.commit()
        
        return {
            'risk_level': prediction['risk_level'],
            'risk_probability': round(prediction['risk_probability'], 3),
            'confidence_score': round(prediction['confidence_score'], 3),
            'predicted_conditions': prediction.get('predicted_conditions', []),
            'contributing_factors': prediction.get('contributing_factors', [])
        }
        
    except Exception as e:
        return {'error': str(e)}
