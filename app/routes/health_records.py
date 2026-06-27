"""
Health Records Module - Complete Patient Data Management
- Store and retrieve patient health data
- Medical history management
- Vital signs tracking
- Health trends and analysis
- Health data export/import
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app import db
from database.models import User, VitalSign, HealthPrediction, MedicalReport
from datetime import datetime, timedelta
import json
import csv
import io

bp = Blueprint('health_records', __name__, url_prefix='/api/health-records')


@bp.route('/profile', methods=['GET'])
@login_required
def get_patient_profile():
    """Get complete patient profile with health data"""
    try:
        user = User.query.get(current_user.id)
        
        profile = {
            'id': user.id,
            'name': user.full_name,
            'email': user.email,
            'phone': user.phone,
            'date_of_birth': user.date_of_birth.isoformat() if user.date_of_birth else None,
            'gender': user.gender,
            'address': user.address,
            'medical_history': user.medical_history,
            'current_medications': user.current_medications,
            'allergies': user.allergies,
            'blood_type': user.blood_type,
            'created_at': user.created_at.isoformat()
        }
        
        return jsonify({'profile': profile, 'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@bp.route('/profile/update', methods=['POST'])
@login_required
def update_patient_profile():
    """
    Update patient profile
    
    Expected JSON:
    {
        "full_name": "John Doe",
        "phone": "1234567890",
        "address": "123 Main St",
        "medical_history": "Diabetes, Hypertension",
        "current_medications": "Aspirin, Metformin",
        "allergies": "Penicillin",
        "blood_type": "O+"
    }
    """
    try:
        data = request.get_json()
        user = User.query.get(current_user.id)
        
        # Update basic fields
        if 'full_name' in data:
            user.full_name = data['full_name']
        if 'phone' in data:
            user.phone = data['phone']
        if 'address' in data:
            user.address = data['address']
        
        # Update health-specific fields
        if 'medical_history' in data:
            user.medical_history = data['medical_history']
        if 'current_medications' in data:
            user.current_medications = data['current_medications']
        if 'allergies' in data:
            user.allergies = data['allergies']
        if 'blood_type' in data:
            user.blood_type = data['blood_type']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Profile updated successfully',
            'profile': data,
            'success': True
        }), 200
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@bp.route('/vitals', methods=['GET', 'POST'])
@login_required
def manage_vitals():
    """Get vital signs history or add new vital signs"""
    if request.method == 'POST':
        # Add vital signs
        try:
            data = request.get_json()
            
            vital = VitalSign(
                patient_id=current_user.id,
                heart_rate=data.get('heart_rate'),
                blood_pressure_systolic=data.get('blood_pressure_systolic'),
                blood_pressure_diastolic=data.get('blood_pressure_diastolic'),
                temperature=data.get('temperature'),
                oxygen_level=data.get('oxygen_level'),
                weight=data.get('weight'),
                height=data.get('height'),
                cholesterol=data.get('cholesterol'),
                glucose=data.get('glucose'),
                notes=data.get('notes')
            )
            
            db.session.add(vital)
            db.session.commit()
            
            return jsonify({
                'message': 'Vital signs recorded',
                'vital_id': vital.id,
                'success': True
            }), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e), 'success': False}), 500
    
    # GET - Retrieve vitals history
    try:
        days = request.args.get('days', 30, type=int)
        limit = request.args.get('limit', 100, type=int)
        
        since = datetime.utcnow() - timedelta(days=days)
        
        vitals = VitalSign.query.filter_by(patient_id=current_user.id).filter(
            VitalSign.recorded_at >= since
        ).order_by(VitalSign.recorded_at.desc()).limit(limit).all()
        
        vitals_data = [vital.to_dict() for vital in vitals]
        
        return jsonify({
            'vitals': vitals_data,
            'count': len(vitals_data),
            'success': True
        }), 200
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@bp.route('/vitals/add', methods=['POST'])
@login_required
def add_vital_signs():
    """
    Record vital signs
    
    Expected JSON:
    {
        "heart_rate": 72,
        "blood_pressure_systolic": 120,
        "blood_pressure_diastolic": 80,
        "temperature": 37.2,
        "oxygen_level": 98,
        "glucose": 95,
        "weight": 70,
        "height": 175
    }
    """
    try:
        data = request.get_json()
        
        vital = VitalSign(
            patient_id=current_user.id,
            heart_rate=data.get('heart_rate'),
            blood_pressure_systolic=data.get('blood_pressure_systolic'),
            blood_pressure_diastolic=data.get('blood_pressure_diastolic'),
            temperature=data.get('temperature'),
            oxygen_level=data.get('oxygen_level'),
            weight=data.get('weight'),
            height=data.get('height'),
            cholesterol=data.get('cholesterol'),
            glucose=data.get('glucose'),
            notes=data.get('notes')
        )
        
        db.session.add(vital)
        db.session.commit()
        
        return jsonify({
            'message': 'Vital signs recorded',
            'vital_id': vital.id,
            'success': True
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e), 'success': False}), 500


@bp.route('/vitals/latest', methods=['GET'])
@login_required
def get_latest_vitals():
    """Get latest vital signs"""
    try:
        vital = VitalSign.query.filter_by(patient_id=current_user.id).order_by(
            VitalSign.recorded_at.desc()
        ).first()
        
        if not vital:
            return jsonify({'vital': None, 'success': True}), 200
        
        return jsonify({'vital': vital.to_dict(), 'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@bp.route('/vitals/history', methods=['GET'])
@login_required
def get_vitals_history():
    """
    Get vital signs history
    
    Query params:
    - days: number of days to retrieve (default: 30)
    - limit: max records to return (default: 100)
    """
    try:
        days = request.args.get('days', 30, type=int)
        limit = request.args.get('limit', 100, type=int)
        
        since = datetime.utcnow() - timedelta(days=days)
        
        vitals = VitalSign.query.filter_by(patient_id=current_user.id).filter(
            VitalSign.timestamp >= since
        ).order_by(VitalSign.timestamp.desc()).limit(limit).all()
        
        vitals_data = []
        for vital in vitals:
            vitals_data.append({
                'id': vital.id,
                'heart_rate': vital.heart_rate,
                'blood_pressure': f"{vital.blood_pressure_systolic}/{vital.blood_pressure_diastolic}" if vital.blood_pressure_systolic else None,
                'temperature': vital.temperature,
                'oxygen_saturation': vital.oxygen_saturation,
                'blood_glucose': vital.blood_glucose,
                'weight': vital.weight,
                'bmi': calculate_bmi(vital.weight, vital.height) if vital.weight and vital.height else None,
                'timestamp': vital.timestamp.isoformat()
            })
        
        return jsonify({
            'vitals': vitals_data,
            'count': len(vitals_data),
            'success': True
        }), 200
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@bp.route('/vitals/<int:vital_id>', methods=['DELETE'])
@login_required
def delete_vital_sign(vital_id):
    """Delete a vital sign record"""
    try:
        vital = VitalSign.query.get(vital_id)
        
        if not vital:
            return jsonify({'error': 'Vital sign not found', 'success': False}), 404
        
        if vital.patient_id != current_user.id:
            return jsonify({'error': 'Unauthorized', 'success': False}), 403
        
        db.session.delete(vital)
        db.session.commit()
        
        return jsonify({
            'message': 'Vital sign deleted',
            'success': True
        }), 200
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@bp.route('/vitals/<int:vital_id>', methods=['GET'])
@login_required
def get_vital_sign_detail(vital_id):
    """Get detailed information for a specific vital sign record with patient details"""
    try:
        vital = VitalSign.query.get(vital_id)
        
        if not vital:
            return jsonify({'error': 'Vital sign not found', 'success': False}), 404
        
        if vital.patient_id != current_user.id:
            return jsonify({'error': 'Unauthorized', 'success': False}), 403
        
        # Get patient information
        patient = User.query.get(vital.patient_id)
        
        # Calculate BMI if weight and height are available
        bmi = None
        if vital.weight and vital.height:
            height_m = vital.height / 100  # Convert cm to meters
            bmi = round(vital.weight / (height_m ** 2), 1)
        
        # Prepare detailed response
        detail = {
            'vital_record': {
                'id': vital.id,
                'recorded_at': vital.recorded_at.isoformat(),
                'source': vital.source,
                'notes': vital.notes,
                'heart_rate': vital.heart_rate,
                'blood_pressure_systolic': vital.blood_pressure_systolic,
                'blood_pressure_diastolic': vital.blood_pressure_diastolic,
                'temperature': vital.temperature,
                'oxygen_level': vital.oxygen_level,
                'weight': vital.weight,
                'height': vital.height,
                'cholesterol': vital.cholesterol,
                'glucose': vital.glucose,
                'bmi': bmi
            },
            'patient_info': {
                'id': patient.id,
                'name': patient.full_name,
                'email': patient.email,
                'phone': patient.phone,
                'date_of_birth': patient.date_of_birth.isoformat() if patient.date_of_birth else None,
                'age': calculate_age(patient.date_of_birth) if patient.date_of_birth else None,
                'gender': patient.gender,
                'blood_type': patient.blood_type,
                'address': patient.address,
                'medical_history': patient.medical_history,
                'current_medications': patient.current_medications,
                'allergies': patient.allergies
            },
            'health_status': {
                'heart_rate_status': get_heart_rate_status(vital.heart_rate),
                'bp_status': get_bp_status(vital.blood_pressure_systolic, vital.blood_pressure_diastolic),
                'temp_status': get_temp_status(vital.temperature),
                'oxygen_status': get_oxygen_status(vital.oxygen_level),
                'glucose_status': get_glucose_status(vital.glucose),
                'bmi_status': get_bmi_status(bmi)
            }
        }
        
        return jsonify({
            'detail': detail,
            'success': True
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@bp.route('/vitals/trends', methods=['GET'])
@login_required
def get_vitals_trends():
    """Get vital signs trends for analysis"""
    try:
        days = request.args.get('days', 7, type=int)
        since = datetime.utcnow() - timedelta(days=days)
        
        vitals = VitalSign.query.filter_by(patient_id=current_user.id).filter(
            VitalSign.timestamp >= since
        ).order_by(VitalSign.timestamp.asc()).all()
        
        if not vitals:
            return jsonify({'trends': {}, 'success': True}), 200
        
        # Calculate trends
        heart_rates = [v.heart_rate for v in vitals if v.heart_rate]
        blood_pressures = [(v.blood_pressure_systolic, v.blood_pressure_diastolic) for v in vitals if v.blood_pressure_systolic]
        temperatures = [v.temperature for v in vitals if v.temperature]
        oxygen_levels = [v.oxygen_saturation for v in vitals if v.oxygen_saturation]
        
        trends = {
            'heart_rate': {
                'avg': round(sum(heart_rates) / len(heart_rates), 1) if heart_rates else None,
                'min': min(heart_rates) if heart_rates else None,
                'max': max(heart_rates) if heart_rates else None,
                'trend': 'stable'  # Could be calculated from trend
            },
            'blood_pressure': {
                'avg_systolic': round(sum([bp[0] for bp in blood_pressures]) / len(blood_pressures), 1) if blood_pressures else None,
                'avg_diastolic': round(sum([bp[1] for bp in blood_pressures]) / len(blood_pressures), 1) if blood_pressures else None,
            },
            'temperature': {
                'avg': round(sum(temperatures) / len(temperatures), 1) if temperatures else None,
                'normal_readings': sum(1 for t in temperatures if 36.1 <= t <= 37.2) if temperatures else 0
            },
            'oxygen_level': {
                'avg': round(sum(oxygen_levels) / len(oxygen_levels), 1) if oxygen_levels else None,
                'below_95': sum(1 for o in oxygen_levels if o < 95) if oxygen_levels else 0
            }
        }
        
        return jsonify({'trends': trends, 'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@bp.route('/export/csv', methods=['GET'])
@login_required
def export_health_data_csv():
    """Export health data as CSV"""
    try:
        days = request.args.get('days', 30, type=int)
        since = datetime.utcnow() - timedelta(days=days)
        
        vitals = VitalSign.query.filter_by(patient_id=current_user.id).filter(
            VitalSign.timestamp >= since
        ).order_by(VitalSign.timestamp.asc()).all()
        
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Headers
        writer.writerow(['Timestamp', 'Heart Rate (bpm)', 'BP Systolic (mmHg)', 'BP Diastolic (mmHg)', 
                        'Temperature (°C)', 'Oxygen Saturation (%)', 'Blood Glucose (mg/dL)', 
                        'Weight (kg)', 'Height (cm)', 'BMI'])
        
        # Data rows
        for vital in vitals:
            writer.writerow([
                vital.timestamp.isoformat(),
                vital.heart_rate,
                vital.blood_pressure_systolic,
                vital.blood_pressure_diastolic,
                vital.temperature,
                vital.oxygen_saturation,
                vital.blood_glucose,
                vital.weight,
                vital.height,
                calculate_bmi(vital.weight, vital.height) if vital.weight and vital.height else None
            ])
        
        # Return as downloadable file
        from flask import send_file
        csv_file = io.BytesIO(output.getvalue().encode('utf-8'))
        csv_file.seek(0)
        
        return send_file(
            csv_file,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'health_records_{datetime.utcnow().strftime("%Y%m%d")}.csv'
        )
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@bp.route('/health-summary', methods=['GET'])
@login_required
def get_health_summary():
    """Get comprehensive health summary"""
    try:
        user = User.query.get(current_user.id)
        
        # Latest vitals
        latest_vital = VitalSign.query.filter_by(patient_id=current_user.id).order_by(
            VitalSign.timestamp.desc()
        ).first()
        
        # Latest prediction
        latest_prediction = HealthPrediction.query.filter_by(patient_id=current_user.id).order_by(
            HealthPrediction.predicted_at.desc()
        ).first()
        
        summary = {
            'patient_name': user.full_name,
            'age': calculate_age(user.date_of_birth) if user.date_of_birth else None,
            'medical_history': user.medical_history if hasattr(user, 'medical_history') else None,
            'current_medications': user.current_medications if hasattr(user, 'current_medications') else None,
            'latest_vitals': {
                'heart_rate': latest_vital.heart_rate if latest_vital else None,
                'blood_pressure': f"{latest_vital.blood_pressure_systolic}/{latest_vital.blood_pressure_diastolic}" if latest_vital and latest_vital.blood_pressure_systolic else None,
                'temperature': latest_vital.temperature if latest_vital else None,
                'oxygen_saturation': latest_vital.oxygen_saturation if latest_vital else None,
                'timestamp': latest_vital.timestamp.isoformat() if latest_vital else None
            },
            'latest_health_risk': {
                'risk_level': latest_prediction.risk_level if latest_prediction else None,
                'risk_score': latest_prediction.risk_score if latest_prediction else None,
                'predicted_at': latest_prediction.predicted_at.isoformat() if latest_prediction else None
            }
        }
        
        return jsonify({'summary': summary, 'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


# Helper functions
def calculate_bmi(weight, height):
    """Calculate BMI from weight (kg) and height (cm)"""
    if not weight or not height:
        return None
    height_m = height / 100
    return round(weight / (height_m ** 2), 1)


def calculate_age(date_of_birth):
    """Calculate age from date of birth"""
    if not date_of_birth:
        return None
    today = datetime.now()
    age = today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))
    return age


def get_heart_rate_status(heart_rate):
    """Determine heart rate status"""
    if not heart_rate:
        return {'status': 'unknown', 'message': 'Not recorded'}
    if heart_rate < 60:
        return {'status': 'low', 'message': 'Below normal range'}
    elif heart_rate > 100:
        return {'status': 'high', 'message': 'Above normal range'}
    else:
        return {'status': 'normal', 'message': 'Normal range'}


def get_bp_status(systolic, diastolic):
    """Determine blood pressure status"""
    if not systolic or not diastolic:
        return {'status': 'unknown', 'message': 'Not recorded'}
    if systolic < 90 or diastolic < 60:
        return {'status': 'low', 'message': 'Low blood pressure'}
    elif systolic >= 140 or diastolic >= 90:
        return {'status': 'high', 'message': 'High blood pressure'}
    elif systolic >= 120 and systolic < 140:
        return {'status': 'elevated', 'message': 'Elevated blood pressure'}
    else:
        return {'status': 'normal', 'message': 'Normal blood pressure'}


def get_temp_status(temperature):
    """Determine temperature status"""
    if not temperature:
        return {'status': 'unknown', 'message': 'Not recorded'}
    if temperature < 36.1:
        return {'status': 'low', 'message': 'Below normal (hypothermia risk)'}
    elif temperature > 37.5:
        return {'status': 'high', 'message': 'Fever detected'}
    else:
        return {'status': 'normal', 'message': 'Normal temperature'}


def get_oxygen_status(oxygen_level):
    """Determine oxygen saturation status"""
    if not oxygen_level:
        return {'status': 'unknown', 'message': 'Not recorded'}
    if oxygen_level < 90:
        return {'status': 'critical', 'message': 'Critically low oxygen'}
    elif oxygen_level < 95:
        return {'status': 'low', 'message': 'Low oxygen saturation'}
    else:
        return {'status': 'normal', 'message': 'Normal oxygen level'}


def get_glucose_status(glucose):
    """Determine glucose status"""
    if not glucose:
        return {'status': 'unknown', 'message': 'Not recorded'}
    if glucose < 70:
        return {'status': 'low', 'message': 'Low blood sugar (hypoglycemia)'}
    elif glucose > 140:
        return {'status': 'high', 'message': 'High blood sugar (hyperglycemia)'}
    else:
        return {'status': 'normal', 'message': 'Normal glucose level'}


def get_bmi_status(bmi):
    """Determine BMI status"""
    if not bmi:
        return {'status': 'unknown', 'message': 'Not available'}
    if bmi < 18.5:
        return {'status': 'underweight', 'message': 'Underweight'}
    elif bmi < 25:
        return {'status': 'normal', 'message': 'Normal weight'}
    elif bmi < 30:
        return {'status': 'overweight', 'message': 'Overweight'}
    else:
        return {'status': 'obese', 'message': 'Obese'}
