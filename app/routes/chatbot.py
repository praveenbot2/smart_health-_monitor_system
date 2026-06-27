"""
AI Health Assistant Module
- Gemini-powered chatbot (like ChatGPT)
- Multi-turn conversations
- Health Q&A
- Symptom analysis
- Health risk assessment
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app import db
from database.models import ChatMessage, ChatFeedback, HealthPrediction, VitalSign
from ai_modules.gemini_api import get_gemini_assistant
from datetime import datetime, timedelta
import json

bp = Blueprint('chatbot', __name__, url_prefix='/api/chatbot')
gemini = get_gemini_assistant()


@bp.route('/chat', methods=['POST'])
@login_required
def chat():
    """
    Multi-turn health assistant conversation
    
    Expected JSON:
    {
        "message": "User question",
        "include_context": true/false  # Include patient's health data
    }
    """
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        include_context = data.get('include_context', False)
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Prepare patient context if requested
        patient_context = None
        if include_context:
            patient_context = _get_patient_context(current_user.id)
        
        # Get Gemini response
        response = gemini.chat(
            user_id=str(current_user.id),
            message=message,
            context=patient_context
        )
        
        if response.get('success'):
            # Save to chat history
            chat_msg = ChatMessage(
                user_id=current_user.id,
                message=message,
                response=response.get('response', ''),
                message_type=response.get('mode', 'general')
            )
            db.session.add(chat_msg)
            db.session.commit()
            
            return jsonify({
                'message': message,
                'response': response['response'],
                'timestamp': response.get('timestamp'),
                'message_id': chat_msg.id,
                'mode': response.get('mode', 'gemini'),
                'success': True
            }), 200
        else:
            return jsonify({
                'error': response.get('response', 'Error processing request'),
                'success': False
            }), 500
            
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@bp.route('/feedback', methods=['POST'])
@login_required
def submit_feedback():
    """Save user satisfaction level for a chatbot response"""
    try:
        data = request.get_json() or {}
        chat_message_id = data.get('chat_message_id')
        level = data.get('satisfaction_level')
        comment = (data.get('comment') or '').strip()

        if not chat_message_id:
            return jsonify({'error': 'chat_message_id is required', 'success': False}), 400

        if level is None:
            return jsonify({'error': 'satisfaction_level is required', 'success': False}), 400

        try:
            level = int(level)
        except (TypeError, ValueError):
            return jsonify({'error': 'satisfaction_level must be an integer', 'success': False}), 400

        if level < 1 or level > 5:
            return jsonify({'error': 'satisfaction_level must be between 1 and 5', 'success': False}), 400

        chat_message = ChatMessage.query.filter_by(id=chat_message_id, user_id=current_user.id).first()
        if not chat_message:
            return jsonify({'error': 'Chat message not found', 'success': False}), 404

        existing = ChatFeedback.query.filter_by(
            user_id=current_user.id,
            chat_message_id=chat_message_id
        ).first()

        if existing:
            existing.satisfaction_level = level
            existing.comment = comment or existing.comment
            saved_feedback = existing
        else:
            saved_feedback = ChatFeedback(
                user_id=current_user.id,
                chat_message_id=chat_message_id,
                satisfaction_level=level,
                comment=comment
            )
            db.session.add(saved_feedback)

        db.session.commit()

        return jsonify({
            'message': 'Feedback saved',
            'feedback': saved_feedback.to_dict(),
            'success': True
        }), 200
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@bp.route('/satisfaction', methods=['GET'])
@login_required
def satisfaction_stats():
    """Get satisfaction summary for current user chatbot sessions"""
    try:
        entries = ChatFeedback.query.filter_by(user_id=current_user.id).all()
        if not entries:
            return jsonify({
                'average': 0,
                'count': 0,
                'distribution': {'1': 0, '2': 0, '3': 0, '4': 0, '5': 0},
                'success': True
            }), 200

        count = len(entries)
        avg = round(sum(e.satisfaction_level for e in entries) / count, 2)
        distribution = {'1': 0, '2': 0, '3': 0, '4': 0, '5': 0}
        for e in entries:
            distribution[str(e.satisfaction_level)] += 1

        return jsonify({
            'average': avg,
            'count': count,
            'distribution': distribution,
            'success': True
        }), 200
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@bp.route('/analyze-symptoms', methods=['POST'])
@login_required
def analyze_symptoms():
    """
    Analyze reported symptoms
    
    Expected JSON:
    {
        "symptoms": ["fever", "headache", "cough"],
        "duration": "2 days"
    }
    """
    try:
        data = request.get_json()
        symptoms = data.get('symptoms', [])
        
        if not symptoms:
            return jsonify({'error': 'Symptoms list is required'}), 400
        
        # Get analysis from Gemini
        result = gemini.analyze_symptoms(symptoms)
        
        if result.get('success'):
            return jsonify({
                'analysis': result.get('analysis'),
                'severity': result.get('severity', 'unknown'),
                'timestamp': result.get('timestamp'),
                'success': True
            }), 200
        else:
            return jsonify({'error': result.get('error', 'Analysis failed'), 'success': False}), 500
            
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@bp.route('/health-risk', methods=['POST'])
@login_required
def assess_health_risk():
    """
    Assess health risk based on current vitals
    
    Expected JSON:
    {
        "vitals": {
            "heart_rate": 85,
            "blood_pressure": "120/80",
            "temperature": 37.5,
            "oxygen_level": 98
        }
    }
    """
    try:
        data = request.get_json()
        vitals = data.get('vitals', {})
        
        # Get patient info
        patient_data = {
            'age': current_user.age if hasattr(current_user, 'age') else None,
            'gender': current_user.gender if hasattr(current_user, 'gender') else None,
            'medical_history': current_user.medical_history if hasattr(current_user, 'medical_history') else None,
        }
        
        # Get risk assessment from Gemini
        result = gemini.assess_health_risk(vitals, patient_data)
        
        if result.get('success'):
            return jsonify({
                'risk_level': result.get('risk_level', 'Medium'),
                'risk_score': result.get('risk_score', 50),
                'analysis': result.get('analysis'),
                'recommendations': result.get('recommendations', []),
                'timestamp': result.get('timestamp'),
                'success': True
            }), 200
        else:
            return jsonify({'error': result.get('error', 'Assessment failed'), 'success': False}), 500
            
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@bp.route('/health-report', methods=['GET'])
@login_required
def generate_health_report():
    """Generate comprehensive health report"""
    try:
        # Collect patient health data
        patient_data = _compile_patient_data(current_user.id)
        
        # Generate report
        result = gemini.generate_health_report(patient_data)
        
        if result.get('success'):
            return jsonify({
                'report': result.get('report'),
                'summary': result.get('summary'),
                'timestamp': result.get('timestamp'),
                'success': True
            }), 200
        else:
            return jsonify({'error': result.get('error', 'Report generation failed'), 'success': False}), 500
            
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@bp.route('/history', methods=['GET'])
@login_required
def get_chat_history():
    """Get conversation history (Gemini memory)"""
    try:
        limit = request.args.get('limit', 20, type=int)
        
        # Get from Gemini conversation history
        history = gemini.get_history(str(current_user.id), limit)
        
        # Also get from database for persistence
        db_messages = ChatMessage.query.filter_by(user_id=current_user.id).order_by(
            ChatMessage.created_at.desc()
        ).limit(limit).all()
        
        return jsonify({
            'messages': [m.to_dict() for m in db_messages[::-1]],
            'success': True
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@bp.route('/clear-history', methods=['DELETE'])
@login_required
def clear_chat_history():
    """Clear chat history"""
    try:
        # Clear from Gemini
        gemini.clear_history(str(current_user.id))
        
        # Clear from database
        ChatMessage.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
        
        return jsonify({'message': 'Chat history cleared', 'success': True}), 200
        
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


def _get_patient_context(user_id):
    """Compile patient health context for analysis"""
    context = {}
    
    # Get latest vital signs
    latest_vitals = VitalSign.query.filter_by(patient_id=user_id).order_by(
        VitalSign.recorded_at.desc()
    ).first()
    
    if latest_vitals:
        context['vitals'] = {
            'heart_rate': latest_vitals.heart_rate,
            'blood_pressure': f"{latest_vitals.blood_pressure_systolic}/{latest_vitals.blood_pressure_diastolic}",
            'temperature': latest_vitals.temperature,
            'oxygen_level': latest_vitals.oxygen_level
        }
    
    # Get recent health data
    from database.models import User
    user = User.query.get(user_id)
    
    if user:
        context['symptoms'] = getattr(user, 'current_symptoms', None)
        context['history'] = getattr(user, 'medical_history', None)
    
    return context if context else None


def _compile_patient_data(user_id):
    """Compile comprehensive patient health data for reporting"""
    from database.models import User
    
    user = User.query.get(user_id)
    patient_data = {
        'name': user.full_name,
        'age': user.date_of_birth,
        'gender': user.gender,
        'medical_history': user.medical_history if hasattr(user, 'medical_history') else None
    }
    
    # Get recent vital signs
    vitals = VitalSign.query.filter_by(patient_id=user_id).order_by(
        VitalSign.recorded_at.desc()
    ).limit(5).all()
    
    if vitals:
        patient_data['recent_vitals'] = [{
            'timestamp': v.recorded_at.isoformat(),
            'heart_rate': v.heart_rate,
            'blood_pressure': f"{v.blood_pressure_systolic}/{v.blood_pressure_diastolic}",
            'temperature': v.temperature,
            'oxygen': v.oxygen_level
        } for v in vitals]
    
    # Get recent predictions
    predictions = HealthPrediction.query.filter_by(patient_id=user_id).order_by(
        HealthPrediction.predicted_at.desc()
    ).limit(3).all()
    
    if predictions:
        patient_data['health_predictions'] = [{
            'risk_level': p.risk_level,
            'score': round((p.risk_probability or 0) * 100, 1),
            'predicted_at': p.predicted_at.isoformat()
        } for p in predictions]
    
    return patient_data

