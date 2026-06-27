"""
Module 5: AI Health Assistant & Chatbot
- Health-related Q&A
- Prediction explanation
- Lifestyle recommendations
- System navigation support
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app import db
from database.models import ChatMessage, HealthPrediction, VitalSign
from datetime import datetime
import json
import re

bp = Blueprint('chatbot', __name__, url_prefix='/api/chatbot')

@bp.route('/chat', methods=['POST'])
@login_required
def chat():
    """Process chatbot message"""
    data = request.get_json()
    message = data.get('message', '').strip()
    
    if not message:
        return jsonify({'error': 'Message is required'}), 400
    
    # Determine message type and generate response
    message_type, response = process_message(message, current_user.id)
    
    # Save chat history
    chat_message = ChatMessage(
        user_id=current_user.id,
        message=message,
        response=response,
        message_type=message_type
    )
    
    db.session.add(chat_message)
    db.session.commit()
    
    return jsonify({
        'message': message,
        'response': response,
        'message_type': message_type
    }), 200


@bp.route('/history', methods=['GET'])
@login_required
def get_chat_history():
    """Get chat history for current user"""
    limit = request.args.get('limit', 20, type=int)
    
    messages = ChatMessage.query.filter_by(user_id=current_user.id).order_by(
        ChatMessage.created_at.desc()
    ).limit(limit).all()
    
    return jsonify({
        'messages': [m.to_dict() for m in messages[::-1]]  # Reverse to chronological order
    }), 200


@bp.route('/clear', methods=['DELETE'])
@login_required
def clear_history():
    """Clear chat history"""
    ChatMessage.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    
    return jsonify({'message': 'Chat history cleared'}), 200


def process_message(message, user_id):
    """Process user message and generate appropriate response"""
    message_lower = message.lower()
    
    # Health Q&A patterns
    if any(word in message_lower for word in ['symptom', 'pain', 'headache', 'fever', 'cough']):
        return 'health_qa', generate_symptom_response(message)
    
    # Prediction explanation
    elif any(word in message_lower for word in ['risk', 'prediction', 'why', 'explain']):
        return 'prediction_explanation', explain_latest_prediction(user_id)
    
    # Lifestyle recommendations
    elif any(word in message_lower for word in ['improve', 'lifestyle', 'diet', 'exercise', 'recommendation']):
        return 'lifestyle_advice', generate_lifestyle_advice(user_id)
    
    # Vital signs inquiry
    elif any(word in message_lower for word in ['vital', 'heart rate', 'blood pressure', 'oxygen', 'temperature']):
        return 'health_qa', get_vital_info(user_id)
    
    # System navigation
    elif any(word in message_lower for word in ['how', 'navigate', 'use', 'feature', 'appointment', 'doctor']):
        return 'navigation', generate_navigation_help(message)
    
    # General greeting
    elif any(word in message_lower for word in ['hello', 'hi', 'hey', 'help']):
        return 'greeting', generate_greeting()
    
    # Default response
    else:
        return 'general', generate_general_response(message)


def generate_greeting():
    """Generate greeting message"""
    return """Hello! I'm your AI Health Assistant. I can help you with:

• Understanding your health predictions and risk levels
• Explaining your vital signs
• Providing lifestyle and wellness recommendations
• Answering health-related questions
• Navigating the system

How can I assist you today?"""


def generate_symptom_response(message):
    """Generate response for symptom-related queries"""
    message_lower = message.lower()
    
    if 'headache' in message_lower:
        return """For headaches, here are some general recommendations:

• Stay hydrated - drink plenty of water
• Get adequate rest and sleep
• Reduce screen time
• Try relaxation techniques
• Monitor your blood pressure

If headaches persist or are severe, please consult a doctor."""
    
    elif 'fever' in message_lower:
        return """For fever management:

• Monitor your temperature regularly
• Stay hydrated
• Get plenty of rest
• Use fever-reducing medication if needed
• Wear light clothing

⚠️ Seek immediate medical attention if fever is above 39.5°C or persists for more than 3 days."""
    
    elif 'cough' in message_lower:
        return """For cough relief:

• Stay hydrated with warm fluids
• Use honey (for adults)
• Avoid irritants like smoke
• Use a humidifier
• Monitor your oxygen levels

Consult a doctor if cough persists for more than 2 weeks or is accompanied by difficulty breathing."""
    
    else:
        return """I understand you're experiencing symptoms. Here's what I recommend:

• Monitor your vital signs regularly
• Document your symptoms
• Get adequate rest
• Stay hydrated

⚠️ If symptoms are severe or worsening, please consult a healthcare professional immediately.
You can book an appointment through our system."""


def explain_latest_prediction(user_id):
    """Explain the latest health risk prediction"""
    prediction = HealthPrediction.query.filter_by(patient_id=user_id).order_by(
        HealthPrediction.predicted_at.desc()
    ).first()
    
    if not prediction:
        return """I don't have any recent health risk predictions for you. 
        
To get a risk assessment:
1. Ensure your vital signs are up to date
2. Navigate to the Health Prediction section
3. Run a new prediction

This will help me provide personalized health insights!"""
    
    risk_level = prediction.risk_level.upper()
    risk_prob = prediction.risk_probability * 100
    
    response = f"""📊 Your Latest Health Risk Assessment:

**Risk Level:** {risk_level}
**Probability:** {risk_prob:.1f}%
**Assessed on:** {prediction.predicted_at.strftime('%Y-%m-%d %H:%M')}

"""
    
    if prediction.risk_level == 'low':
        response += """✅ **Good news!** Your current health indicators show low risk.

**Contributing to your low risk:**
"""
    elif prediction.risk_level == 'medium':
        response += """⚠️ **Moderate risk detected.** Some health indicators need attention.

**Factors to watch:**
"""
    else:  # high
        response += """🚨 **High risk detected.** Please consult a healthcare professional.

**Critical factors:**
"""
    
    # Add contributing factors
    try:
        factors = json.loads(prediction.contributing_factors)
        for factor in factors[:3]:
            response += f"\n• {factor}"
    except:
        pass
    
    response += "\n\n**Recommendations:**\n"
    if prediction.risk_level == 'low':
        response += "• Continue your healthy lifestyle\n• Regular monitoring\n• Annual checkups"
    elif prediction.risk_level == 'medium':
        response += "• Consult with a doctor\n• Monitor vitals more frequently\n• Consider lifestyle modifications"
    else:
        response += "• Schedule an appointment immediately\n• Monitor vitals closely\n• Follow medical advice strictly"
    
    return response


def generate_lifestyle_advice(user_id):
    """Generate personalized lifestyle recommendations"""
    # Get latest vital signs
    vital = VitalSign.query.filter_by(patient_id=user_id).order_by(
        VitalSign.recorded_at.desc()
    ).first()
    
    # Get latest prediction
    prediction = HealthPrediction.query.filter_by(patient_id=user_id).order_by(
        HealthPrediction.predicted_at.desc()
    ).first()
    
    advice = """🌟 **Personalized Lifestyle Recommendations:**

"""
    
    # Cardiovascular health
    if vital and vital.heart_rate:
        if vital.heart_rate > 90:
            advice += """**Cardiovascular Health:**
• Practice deep breathing exercises
• Reduce caffeine intake
• Get 7-8 hours of sleep
• Include omega-3 rich foods
• Regular aerobic exercise (30 min/day)

"""
    
    # Blood pressure management
    if vital and vital.blood_pressure_systolic and vital.blood_pressure_systolic > 130:
        advice += """**Blood Pressure Management:**
• Reduce sodium intake (<2300mg/day)
• Eat potassium-rich foods (bananas, spinach)
• Maintain healthy weight
• Limit alcohol consumption
• Manage stress through meditation

"""
    
    # General wellness
    advice += """**General Wellness:**
• 🥗 **Nutrition:** Eat colorful fruits and vegetables
• 💪 **Exercise:** 150 minutes moderate activity per week
• 💧 **Hydration:** Drink 8 glasses of water daily
• 😴 **Sleep:** Maintain consistent sleep schedule
• 🧘 **Stress:** Practice mindfulness or yoga
• 🚭 **Avoid:** Smoking and excessive alcohol

"""
    
    if prediction and prediction.risk_level != 'low':
        advice += """⚕️ **Important:** Given your risk level, please consult with a healthcare professional for personalized medical advice."""
    
    return advice


def get_vital_info(user_id):
    """Get information about latest vital signs"""
    vital = VitalSign.query.filter_by(patient_id=user_id).order_by(
        VitalSign.recorded_at.desc()
    ).first()
    
    if not vital:
        return """I don't have any vital signs recorded for you yet.

To monitor your health effectively, please:
1. Record your vital signs regularly
2. Use our IoT simulation feature for testing
3. Connect your health monitoring devices

Regular monitoring helps provide better health insights!"""
    
    response = f"""📊 **Your Latest Vital Signs**
*Recorded: {vital.recorded_at.strftime('%Y-%m-%d %H:%M')}*

"""
    
    if vital.heart_rate:
        status = "Normal" if 60 <= vital.heart_rate <= 100 else "⚠️ Needs attention"
        response += f"❤️ **Heart Rate:** {vital.heart_rate} bpm - {status}\n"
    
    if vital.blood_pressure_systolic and vital.blood_pressure_diastolic:
        status = "Normal" if vital.blood_pressure_systolic < 120 and vital.blood_pressure_diastolic < 80 else "⚠️ Needs attention"
        response += f"🩸 **Blood Pressure:** {vital.blood_pressure_systolic}/{vital.blood_pressure_diastolic} mmHg - {status}\n"
    
    if vital.oxygen_level:
        status = "Normal" if vital.oxygen_level >= 95 else "⚠️ Needs attention"
        response += f"🫁 **Oxygen Level:** {vital.oxygen_level}% - {status}\n"
    
    if vital.temperature:
        status = "Normal" if 36.1 <= vital.temperature <= 37.2 else "⚠️ Needs attention"
        response += f"🌡️ **Temperature:** {vital.temperature}°C - {status}\n"
    
    return response


def generate_navigation_help(message):
    """Generate system navigation guidance"""
    message_lower = message.lower()
    
    if 'appointment' in message_lower:
        return """📅 **Booking an Appointment:**

1. Navigate to 'Appointments' section
2. Click 'Book New Appointment'
3. Select a doctor and specialty
4. Choose available time slot
5. Add reason for visit
6. Confirm booking

You'll receive a confirmation and reminder notifications!"""
    
    elif 'doctor' in message_lower:
        return """👨‍⚕️ **Finding a Doctor:**

1. Go to 'Doctors' section
2. Filter by specialization
3. View doctor profiles and ratings
4. Check availability
5. Book an appointment

Our smart system recommends doctors based on your health risk level!"""
    
    elif 'report' in message_lower:
        return """📄 **Accessing Reports:**

1. Navigate to 'Medical Reports'
2. View prediction history
3. Download PDF reports
4. Check doctor remarks

Reports include your health scores, predictions, and vital trends!"""
    
    else:
        return """🧭 **System Navigation:**

**Main Features:**
• 📊 Dashboard - Overview of your health
• ❤️ Vital Signs - Monitor real-time data
• 🤖 Predictions - AI health risk assessment
• 📈 Health Score - Track your progress
• 👨‍⚕️ Doctors - Find and book specialists
• 📅 Appointments - Manage your schedule
• 📄 Reports - View medical reports
• 🔔 Alerts - Important notifications

Need help with a specific feature? Just ask!"""


def generate_general_response(message):
    """Generate general response"""
    return """I'm here to help with your health and wellness journey!

I can assist you with:
• Health risk assessments and explanations
• Understanding your vital signs
• Lifestyle and wellness recommendations
• Booking appointments
• Navigating the system

Please feel free to ask specific questions about:
- Your symptoms or health concerns
- Your latest predictions
- How to improve your health score
- System features and navigation

What would you like to know?"""
