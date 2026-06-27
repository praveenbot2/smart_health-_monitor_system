"""
Main routes for the application
"""

from flask import Blueprint, jsonify, send_from_directory, current_app, make_response
from flask_login import login_required
import os

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """Home page - Modern login interface"""
    static_folder = os.path.join(current_app.root_path, 'static')
    return send_from_directory(static_folder, 'login.html')


@bp.route('/login')
def login_page():
    """Login page - Modern"""
    static_folder = os.path.join(current_app.root_path, 'static')
    return send_from_directory(static_folder, 'login.html')


@bp.route('/register')
def register_page():
    """Register page"""
    static_folder = os.path.join(current_app.root_path, 'static')
    return send_from_directory(static_folder, 'register.html')

@bp.route('/dashboard')
@login_required
def dashboard():
    """Dashboard page"""
    static_folder = os.path.join(current_app.root_path, 'static')
    return send_from_directory(static_folder, 'dashboard-v2.html')

@bp.route('/dashboard-v2')
@bp.route('/v2/dashboard')
@login_required
def dashboard_v2():
    """Dashboard v2 page"""
    static_folder = os.path.join(current_app.root_path, 'static')
    return send_from_directory(static_folder, 'dashboard-v2.html')

@bp.route('/patient-data')
@login_required
def patient_data():
    """Full-screen Patient Data module"""
    static_folder = os.path.join(current_app.root_path, 'static')
    response = make_response(send_from_directory(static_folder, 'patient-data-fullscreen.html'))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@bp.route('/chatbot')
@login_required
def chatbot():
    """Full-screen AI Chatbot module"""
    static_folder = os.path.join(current_app.root_path, 'static')
    return send_from_directory(static_folder, 'chatbot-fullscreen.html')

@bp.route('/doctor-booking')
@login_required
def doctor_booking():
    """Full-screen Doctor Booking module"""
    static_folder = os.path.join(current_app.root_path, 'static')
    return send_from_directory(static_folder, 'doctor-booking-fullscreen.html')

@bp.route('/alerts')
@login_required
def alerts():
    """Full-screen Health Alerts module"""
    static_folder = os.path.join(current_app.root_path, 'static')
    return send_from_directory(static_folder, 'alerts-fullscreen.html')

@bp.route('/results')
@login_required
def results():
    """Full-screen Health Results module"""
    static_folder = os.path.join(current_app.root_path, 'static')
    return send_from_directory(static_folder, 'results-fullscreen.html')

@bp.route('/records')
@login_required
def records():
    """Full-screen Health Records module"""
    static_folder = os.path.join(current_app.root_path, 'static')
    return send_from_directory(static_folder, 'records-fullscreen.html')

@bp.route('/family-members')
@login_required
def family_members():
    """Full-screen Family Members module"""
    static_folder = os.path.join(current_app.root_path, 'static')
    return send_from_directory(static_folder, 'family-members-fullscreen.html')


@bp.route('/api')
def api_info():
    """API information endpoint"""
    return jsonify({
        'application': 'Smart Health Monitor System',
        'version': '2.0.0',
        'status': 'running',
        'modules': {
            'ai_assistant': 'Gemini-powered AI health assistant (like ChatGPT)',
            'health_records': 'Complete patient data management',
            'doctor_booking': 'Doctor appointments with slot management',
            'risk_alerts': 'Real-time risk-based health alerts',
            'health_predictions': 'AI-powered health risk predictions',
            'results': 'Health reports and results'
        },
        'api_endpoints': {
            'authentication': '/api/auth',
            'vital_signs': '/api/vitals',
            'health_records': '/api/health-records',
            'predictions': '/api/predictions',
            'results': '/api/results',
            'health_score': '/api/health-score',
            'chatbot': '/api/chatbot',
            'doctors': '/api/doctors',
            'doctor_booking': '/api/doctor-booking',
            'appointments': '/api/appointments',
            'alerts': '/api/alerts',
            'reports': '/api/reports',
            'admin': '/api/admin'
        },
        'features': [
            'AI Assistant (Gemini API)',
            'Real-time Health Monitoring',
            'Doctor Booking System',
            'Risk-based Alerts',
            'Health Predictions',
            'Vibrant Dashboard UI'
        ],
        'documentation': 'See README.md for complete API documentation'
    }), 200

@bp.route('/vitals')
@login_required
def vitals_page():
    """Vitals alias -> Full-screen Patient Data module"""
    static_folder = os.path.join(current_app.root_path, 'static')
    response = make_response(send_from_directory(static_folder, 'patient-data-fullscreen.html'))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@bp.route('/reports')
@login_required
def reports_page():
    """Reports alias -> Full-screen Records module"""
    static_folder = os.path.join(current_app.root_path, 'static')
    return send_from_directory(static_folder, 'records-fullscreen.html')

@bp.route('/predictions')
@login_required
def predictions_page():
    """Predictions alias -> Full-screen Results module"""
    static_folder = os.path.join(current_app.root_path, 'static')
    return send_from_directory(static_folder, 'results-fullscreen.html')

@bp.route('/doctors')
@login_required
def doctors_page():
    """Doctors alias -> Full-screen Doctor Booking module"""
    static_folder = os.path.join(current_app.root_path, 'static')
    return send_from_directory(static_folder, 'doctor-booking-fullscreen.html')

@bp.route('/appointments')
@login_required
def appointments_page():
    """Appointments alias -> Full-screen Doctor Booking module"""
    static_folder = os.path.join(current_app.root_path, 'static')
    return send_from_directory(static_folder, 'doctor-booking-fullscreen.html')

@bp.route('/ai-assistant')
@login_required
def ai_assistant_alias_page():
    """AI assistant alias -> Full-screen Chatbot module"""
    static_folder = os.path.join(current_app.root_path, 'static')
    return send_from_directory(static_folder, 'chatbot-fullscreen.html')

@bp.route('/settings')
@login_required
def settings_page():
    """User settings page"""
    static_folder = os.path.join(current_app.root_path, 'static')
    return send_from_directory(static_folder, 'settings-fullscreen.html')


@bp.route('/events')
@login_required
def events_page():
    """Full-screen Events module"""
    static_folder = os.path.join(current_app.root_path, 'static')
    return send_from_directory(static_folder, 'events-fullscreen.html')

@bp.route('/mental-health')
@login_required
def mental_health_page():
    """Full-screen Mental Health module"""
    static_folder = os.path.join(current_app.root_path, 'static')
    return send_from_directory(static_folder, 'mental-health-enhanced.html')

@bp.route('/health-score')
@login_required
def health_score_page():
    """Full-screen Health Score module"""
    static_folder = os.path.join(current_app.root_path, 'static')
    return send_from_directory(static_folder, 'health-score-fullscreen.html')

@bp.route('/health-trends')
@login_required
def health_trends_page():
    """Full-screen Health Trends & Forecast module"""
    static_folder = os.path.join(current_app.root_path, 'static')
    return send_from_directory(static_folder, 'health-trends-fullscreen.html')

@bp.route('/symptom-analyzer')
@login_required
def symptom_analyzer_page():
    """Full-screen Symptom Analyzer module"""
    static_folder = os.path.join(current_app.root_path, 'static')
    return send_from_directory(static_folder, 'symptom-analyzer-fullscreen.html')

@bp.route('/emergency-sos')
@login_required
def emergency_sos_page():
    """Full-screen Emergency SOS module"""
    static_folder = os.path.join(current_app.root_path, 'static')
    return send_from_directory(static_folder, 'emergency-sos-fullscreen.html')

@bp.route('/medical-report')
@login_required
def medical_report_page():
    """Full-screen Medical Report Generator module"""
    static_folder = os.path.join(current_app.root_path, 'static')
    return send_from_directory(static_folder, 'medical-report-fullscreen.html')

@bp.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'System is operational'
    }), 200
