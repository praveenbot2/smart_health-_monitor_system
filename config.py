import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration"""
    
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Database settings
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///health_monitor.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT settings
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    
    # Mail settings
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', MAIL_USERNAME)
    
    # OpenAI settings (optional for chatbot)
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # Application settings
    UPLOAD_FOLDER = 'uploads'
    REPORTS_FOLDER = 'reports'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Health score thresholds
    HEALTH_SCORE_EXCELLENT = 80
    HEALTH_SCORE_GOOD = 60
    HEALTH_SCORE_FAIR = 40
    
    # Risk thresholds
    RISK_HIGH_THRESHOLD = 0.7
    RISK_MEDIUM_THRESHOLD = 0.4
    
    # Vital signs normal ranges
    VITAL_RANGES = {
        'heart_rate': {'min': 60, 'max': 100, 'critical_min': 40, 'critical_max': 120},
        'blood_pressure_systolic': {'min': 90, 'max': 120, 'critical_min': 70, 'critical_max': 180},
        'blood_pressure_diastolic': {'min': 60, 'max': 80, 'critical_min': 40, 'critical_max': 120},
        'oxygen_level': {'min': 95, 'max': 100, 'critical_min': 90, 'critical_max': 100},
        'temperature': {'min': 36.1, 'max': 37.2, 'critical_min': 35.0, 'critical_max': 39.5}
    }
