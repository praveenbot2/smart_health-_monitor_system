"""
Module 6: Intelligent Doctor Recommendation
- Specialist suggestion
- Risk-based mapping
- Urgency classification
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app import db
from database.models import User, DoctorProfile, HealthPrediction
from sqlalchemy import or_, and_
import json

bp = Blueprint('doctors', __name__, url_prefix='/api/doctors')

@bp.route('/list', methods=['GET'])
@login_required
def get_doctors():
    """Get list of all doctors"""
    specialization = request.args.get('specialization')
    
    query = User.query.filter_by(role='doctor', is_active=True)
    
    doctors = query.all()
    
    result = []
    for doctor in doctors:
        if hasattr(doctor, 'doctor_profile') and doctor.doctor_profile:
            profile = doctor.doctor_profile
            
            # Filter by specialization if specified
            if specialization and profile.specialization.lower() != specialization.lower():
                continue
            
            doctor_data = doctor.to_dict()
            doctor_data['profile'] = profile.to_dict()
            result.append(doctor_data)
    
    return jsonify({'doctors': result}), 200


@bp.route('/<int:doctor_id>', methods=['GET'])
@login_required
def get_doctor_details(doctor_id):
    """Get detailed information about a doctor"""
    doctor = User.query.filter_by(id=doctor_id, role='doctor').first()
    
    if not doctor:
        return jsonify({'error': 'Doctor not found'}), 404
    
    doctor_data = doctor.to_dict()
    
    if hasattr(doctor, 'doctor_profile') and doctor.doctor_profile:
        doctor_data['profile'] = doctor.doctor_profile.to_dict()
    
    return jsonify({'doctor': doctor_data}), 200


@bp.route('/recommend', methods=['GET'])
@login_required
def recommend_doctors():
    """Get intelligent doctor recommendations based on patient's health risk"""
    patient_id = request.args.get('patient_id', current_user.id, type=int)
    
    # Check permission
    if current_user.role not in ['admin', 'doctor'] and patient_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get latest health prediction
    prediction = HealthPrediction.query.filter_by(patient_id=patient_id).order_by(
        HealthPrediction.predicted_at.desc()
    ).first()
    
    # Determine recommended specializations based on risk
    recommended_specs = get_recommended_specializations(prediction)
    
    # Get urgency level
    urgency = determine_urgency(prediction)
    
    # Get doctors matching specializations
    doctor_profiles = DoctorProfile.query.join(User).filter(
        User.role == 'doctor',
        User.is_active == True
    ).all()
    
    recommendations = []
    
    for profile in doctor_profiles:
        match_score = 0
        
        # Calculate match score
        if profile.specialization in recommended_specs:
            match_score += 50
        
        # Prioritize more experienced doctors for high-risk patients
        if prediction and prediction.risk_level == 'high':
            match_score += min(profile.experience_years * 2, 30)
        
        # Consider rating
        match_score += profile.rating * 4
        
        doctor_data = profile.user.to_dict()
        doctor_data['profile'] = profile.to_dict()
        doctor_data['match_score'] = round(match_score, 2)
        doctor_data['recommended_for'] = [spec for spec in recommended_specs if spec == profile.specialization]
        
        recommendations.append(doctor_data)
    
    # Sort by match score
    recommendations.sort(key=lambda x: x['match_score'], reverse=True)
    
    return jsonify({
        'recommendations': recommendations[:5],  # Top 5
        'urgency': urgency,
        'risk_level': prediction.risk_level if prediction else 'unknown',
        'recommended_specializations': recommended_specs
    }), 200


@bp.route('/specializations', methods=['GET'])
@login_required
def get_specializations():
    """Get list of all specializations"""
    specializations = db.session.query(DoctorProfile.specialization).distinct().all()
    
    spec_list = [s[0] for s in specializations if s[0]]
    
    return jsonify({'specializations': spec_list}), 200


@bp.route('/search', methods=['GET'])
@login_required
def search_doctors():
    """Search doctors by name or specialization"""
    query_param = request.args.get('q', '').strip()
    
    if not query_param:
        return jsonify({'doctors': []}), 200
    
    # Search in doctor names and specializations
    doctors = User.query.filter(
        User.role == 'doctor',
        User.is_active == True,
        or_(
            User.full_name.ilike(f'%{query_param}%'),
            User.username.ilike(f'%{query_param}%')
        )
    ).all()
    
    # Also search in specializations
    profiles = DoctorProfile.query.join(User).filter(
        User.role == 'doctor',
        User.is_active == True,
        DoctorProfile.specialization.ilike(f'%{query_param}%')
    ).all()
    
    result = []
    seen_ids = set()
    
    for doctor in doctors:
        if doctor.id not in seen_ids:
            doctor_data = doctor.to_dict()
            if hasattr(doctor, 'doctor_profile') and doctor.doctor_profile:
                doctor_data['profile'] = doctor.doctor_profile.to_dict()
            result.append(doctor_data)
            seen_ids.add(doctor.id)
    
    for profile in profiles:
        if profile.user_id not in seen_ids:
            doctor_data = profile.user.to_dict()
            doctor_data['profile'] = profile.to_dict()
            result.append(doctor_data)
            seen_ids.add(profile.user_id)
    
    return jsonify({'doctors': result}), 200


def get_recommended_specializations(prediction):
    """Determine recommended specializations based on health prediction"""
    if not prediction:
        return ['General Physician']
    
    specializations = []
    
    try:
        predicted_conditions = json.loads(prediction.predicted_conditions)
    except:
        predicted_conditions = []
    
    # Map conditions to specializations
    condition_mapping = {
        'cardiovascular': 'Cardiologist',
        'cardiac': 'Cardiologist',
        'heart': 'Cardiologist',
        'hypertension': 'Cardiologist',
        'diabetes': 'Endocrinologist',
        'thyroid': 'Endocrinologist',
        'respiratory': 'Pulmonologist',
        'lung': 'Pulmonologist',
        'kidney': 'Nephrologist',
        'liver': 'Gastroenterologist',
        'neurological': 'Neurologist',
        'mental': 'Psychiatrist'
    }
    
    for condition in predicted_conditions:
        condition_lower = condition.lower()
        for key, value in condition_mapping.items():
            if key in condition_lower and value not in specializations:
                specializations.append(value)
    
    # Based on vital signs
    if prediction.blood_pressure_systolic and prediction.blood_pressure_systolic > 140:
        if 'Cardiologist' not in specializations:
            specializations.append('Cardiologist')
    
    if prediction.glucose and prediction.glucose > 126:
        if 'Endocrinologist' not in specializations:
            specializations.append('Endocrinologist')
    
    if prediction.oxygen_level and prediction.oxygen_level < 92:
        if 'Pulmonologist' not in specializations:
            specializations.append('Pulmonologist')
    
    # Default to general physician if no specific specialization
    if not specializations or prediction.risk_level == 'low':
        specializations.insert(0, 'General Physician')
    
    return specializations


def determine_urgency(prediction):
    """Determine urgency level based on health prediction"""
    if not prediction:
        return 'normal'
    
    if prediction.risk_level == 'high':
        if prediction.risk_probability > 0.8:
            return 'emergency'
        else:
            return 'urgent'
    elif prediction.risk_level == 'medium':
        return 'moderate'
    else:
        return 'normal'
