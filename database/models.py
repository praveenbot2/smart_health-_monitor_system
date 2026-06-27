from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from database import db

class User(UserMixin, db.Model):
    """User model for authentication"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='patient')  # admin, doctor, patient
    full_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))
    address = db.Column(db.Text)
    medical_history = db.Column(db.Text)  # Past medical conditions
    current_medications = db.Column(db.Text)  # Current medications
    allergies = db.Column(db.Text)  # Known allergies
    blood_type = db.Column(db.String(5))  # Blood type (e.g., O+, A-, AB+)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    vital_signs = db.relationship('VitalSign', backref='patient', lazy='dynamic', cascade='all, delete-orphan')
    health_predictions = db.relationship('HealthPrediction', backref='patient', lazy='dynamic', cascade='all, delete-orphan')
    health_scores = db.relationship('HealthScore', backref='patient', lazy='dynamic', cascade='all, delete-orphan')
    appointments_as_patient = db.relationship('Appointment', foreign_keys='Appointment.patient_id', backref='patient', lazy='dynamic')
    appointments_as_doctor = db.relationship('Appointment', foreign_keys='Appointment.doctor_id', backref='doctor', lazy='dynamic')
    alerts = db.relationship('Alert', backref='patient', lazy='dynamic', cascade='all, delete-orphan')
    medical_reports = db.relationship('MedicalReport', foreign_keys='MedicalReport.patient_id', backref='patient', lazy='dynamic', cascade='all, delete-orphan')
    settings = db.relationship('UserSettings', backref=db.backref('user', uselist=False), uselist=False, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'full_name': self.full_name,
            'phone': self.phone,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'gender': self.gender,
            'address': self.address,
            'medical_history': self.medical_history,
            'current_medications': self.current_medications,
            'allergies': self.allergies,
            'blood_type': self.blood_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active,
            'settings': self.settings.to_dict() if self.settings else None
        }


class UserSettings(db.Model):
    """Per-user settings for notifications and privacy controls"""
    __tablename__ = 'user_settings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True, index=True)

    # Notification preferences
    email_notifications = db.Column(db.Boolean, default=True)
    sms_notifications = db.Column(db.Boolean, default=False)
    push_notifications = db.Column(db.Boolean, default=True)

    # Privacy settings
    profile_visibility = db.Column(db.String(20), default='private')  # private, care_team, public
    share_anonymized_data = db.Column(db.Boolean, default=False)
    allow_family_access = db.Column(db.Boolean, default=True)
    data_export_consent = db.Column(db.Boolean, default=True)

    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'email_notifications': self.email_notifications,
            'sms_notifications': self.sms_notifications,
            'push_notifications': self.push_notifications,
            'profile_visibility': self.profile_visibility,
            'share_anonymized_data': self.share_anonymized_data,
            'allow_family_access': self.allow_family_access,
            'data_export_consent': self.data_export_consent,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class DoctorProfile(db.Model):
    """Extended profile for doctors"""
    __tablename__ = 'doctor_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    specialization = db.Column(db.String(100), nullable=False)
    license_number = db.Column(db.String(50), unique=True)
    experience_years = db.Column(db.Integer)
    qualification = db.Column(db.String(200))
    consultation_fee = db.Column(db.Float)
    available_days = db.Column(db.String(100))  # JSON string
    available_time_start = db.Column(db.Time)
    available_time_end = db.Column(db.Time)
    rating = db.Column(db.Float, default=0.0)
    total_consultations = db.Column(db.Integer, default=0)
    
    user = db.relationship('User', backref=db.backref('doctor_profile', uselist=False))
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'doctor_name': self.user.full_name,
            'specialization': self.specialization,
            'license_number': self.license_number,
            'experience_years': self.experience_years,
            'qualification': self.qualification,
            'consultation_fee': self.consultation_fee,
            'available_days': self.available_days,
            'available_time_start': self.available_time_start.isoformat() if self.available_time_start else None,
            'available_time_end': self.available_time_end.isoformat() if self.available_time_end else None,
            'rating': self.rating,
            'total_consultations': self.total_consultations
        }


class VitalSign(db.Model):
    """Real-time vital signs monitoring"""
    __tablename__ = 'vital_signs'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    heart_rate = db.Column(db.Integer)  # bpm
    blood_pressure_systolic = db.Column(db.Integer)  # mmHg
    blood_pressure_diastolic = db.Column(db.Integer)  # mmHg
    oxygen_level = db.Column(db.Float)  # %
    temperature = db.Column(db.Float)  # Celsius
    weight = db.Column(db.Float)  # kg
    height = db.Column(db.Float)  # meters
    cholesterol = db.Column(db.Float)  # mg/dL
    glucose = db.Column(db.Float)  # mg/dL
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    source = db.Column(db.String(50), default='manual')  # manual, iot_device
    notes = db.Column(db.Text)  # Additional notes
    
    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'heart_rate': self.heart_rate,
            'blood_pressure_systolic': self.blood_pressure_systolic,
            'blood_pressure_diastolic': self.blood_pressure_diastolic,
            'oxygen_level': self.oxygen_level,
            'temperature': self.temperature,
            'weight': self.weight,
            'height': self.height,
            'cholesterol': self.cholesterol,
            'glucose': self.glucose,
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None,
            'source': self.source,
            'notes': self.notes
        }


class HealthPrediction(db.Model):
    """AI-based health risk predictions"""
    __tablename__ = 'health_predictions'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    risk_level = db.Column(db.String(20))  # low, medium, high
    risk_probability = db.Column(db.Float)  # 0.0 - 1.0
    predicted_conditions = db.Column(db.Text)  # JSON string
    contributing_factors = db.Column(db.Text)  # JSON string
    model_version = db.Column(db.String(20))
    confidence_score = db.Column(db.Float)
    predicted_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Input features used for prediction
    age = db.Column(db.Integer)
    bmi = db.Column(db.Float)
    heart_rate = db.Column(db.Integer)
    blood_pressure_systolic = db.Column(db.Integer)
    blood_pressure_diastolic = db.Column(db.Integer)
    oxygen_level = db.Column(db.Float)
    cholesterol = db.Column(db.Float)
    glucose = db.Column(db.Float)
    
    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'risk_level': self.risk_level,
            'risk_probability': self.risk_probability,
            'predicted_conditions': self.predicted_conditions,
            'contributing_factors': self.contributing_factors,
            'model_version': self.model_version,
            'confidence_score': self.confidence_score,
            'predicted_at': self.predicted_at.isoformat() if self.predicted_at else None,
            'age': self.age,
            'bmi': self.bmi,
            'heart_rate': self.heart_rate,
            'blood_pressure_systolic': self.blood_pressure_systolic,
            'blood_pressure_diastolic': self.blood_pressure_diastolic,
            'oxygen_level': self.oxygen_level,
            'cholesterol': self.cholesterol,
            'glucose': self.glucose
        }


class HealthScore(db.Model):
    """Dynamic health score calculation"""
    __tablename__ = 'health_scores'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    score = db.Column(db.Float, nullable=False)  # 0-100
    cardiovascular_score = db.Column(db.Float)
    respiratory_score = db.Column(db.Float)
    metabolic_score = db.Column(db.Float)
    mental_health_score = db.Column(db.Float)  # Mental health score
    trend = db.Column(db.String(20))  # improving, stable, declining
    calculated_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'score': self.score,
            'cardiovascular_score': self.cardiovascular_score,
            'respiratory_score': self.respiratory_score,
            'metabolic_score': self.metabolic_score,
            'mental_health_score': self.mental_health_score,
            'trend': self.trend,
            'calculated_at': self.calculated_at.isoformat() if self.calculated_at else None
        }


class Appointment(db.Model):
    """Appointment scheduling"""
    __tablename__ = 'appointments'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    appointment_date = db.Column(db.DateTime, nullable=False, index=True)
    duration_minutes = db.Column(db.Integer, default=30)
    status = db.Column(db.String(20), default='scheduled')  # scheduled, completed, cancelled
    reason = db.Column(db.Text)
    notes = db.Column(db.Text)
    urgency = db.Column(db.String(20), default='normal')  # normal, urgent, emergency
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'patient_name': self.patient.full_name,
            'doctor_id': self.doctor_id,
            'doctor_name': self.doctor.full_name,
            'appointment_date': self.appointment_date.isoformat() if self.appointment_date else None,
            'duration_minutes': self.duration_minutes,
            'status': self.status,
            'reason': self.reason,
            'notes': self.notes,
            'urgency': self.urgency,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Alert(db.Model):
    """Alert and emergency notifications"""
    __tablename__ = 'alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    alert_type = db.Column(db.String(50), nullable=False)  # critical_vitals, high_risk, appointment_reminder
    severity = db.Column(db.String(20))  # info, warning, critical
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    is_resolved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    resolved_at = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'alert_type': self.alert_type,
            'severity': self.severity,
            'title': self.title,
            'message': self.message,
            'is_read': self.is_read,
            'is_resolved': self.is_resolved,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None
        }


class MedicalReport(db.Model):
    """Medical reports and prediction history"""
    __tablename__ = 'medical_reports'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    report_type = db.Column(db.String(50))  # health_summary, risk_assessment, vitals_report
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text)  # JSON string
    file_path = db.Column(db.String(255))
    doctor_remarks = db.Column(db.Text)
    generated_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    generated_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    generator = db.relationship('User', foreign_keys=[generated_by], backref='generated_reports')
    
    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'report_type': self.report_type,
            'title': self.title,
            'content': self.content,
            'file_path': self.file_path,
            'doctor_remarks': self.doctor_remarks,
            'generated_by': self.generated_by,
            'generated_at': self.generated_at.isoformat() if self.generated_at else None
        }


class ChatMessage(db.Model):
    """AI chatbot conversation history"""
    __tablename__ = 'chat_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.String(50))  # health_qa, prediction_explanation, lifestyle_advice
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    user = db.relationship('User', backref='chat_messages')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'message': self.message,
            'response': self.response,
            'message_type': self.message_type,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class ChatFeedback(db.Model):
    """User feedback for chatbot response satisfaction"""
    __tablename__ = 'chat_feedback'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    chat_message_id = db.Column(db.Integer, db.ForeignKey('chat_messages.id'), nullable=False, index=True)
    satisfaction_level = db.Column(db.Integer, nullable=False)  # 1-5
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    user = db.relationship('User', backref='chat_feedback')
    chat_message = db.relationship('ChatMessage', backref='feedback_entries')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'chat_message_id': self.chat_message_id,
            'satisfaction_level': self.satisfaction_level,
            'comment': self.comment,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class MentalHealthEntry(db.Model):
    """Mental health tracking and mood monitoring"""
    __tablename__ = 'mental_health_entries'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    mood_score = db.Column(db.Integer, nullable=False)  # 1-10 scale
    stress_level = db.Column(db.Integer, nullable=False)  # 1-10 scale
    sleep_quality = db.Column(db.Integer)  # 1-10 scale
    energy_level = db.Column(db.Integer)  # 1-10 scale
    
    # Common symptoms (stored as boolean flags)
    has_anxiety = db.Column(db.Boolean, default=False)
    has_insomnia = db.Column(db.Boolean, default=False)
    has_fatigue = db.Column(db.Boolean, default=False)
    has_mood_swings = db.Column(db.Boolean, default=False)
    has_irritability = db.Column(db.Boolean, default=False)
    has_concentration_issues = db.Column(db.Boolean, default=False)
    
    notes = db.Column(db.Text)  # Additional notes/thoughts
    entry_date = db.Column(db.Date, nullable=False, default=datetime.utcnow, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    user = db.relationship('User', backref='mental_health_entries')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'mood_score': self.mood_score,
            'stress_level': self.stress_level,
            'sleep_quality': self.sleep_quality,
            'energy_level': self.energy_level,
            'has_anxiety': self.has_anxiety,
            'has_insomnia': self.has_insomnia,
            'has_fatigue': self.has_fatigue,
            'has_mood_swings': self.has_mood_swings,
            'has_irritability': self.has_irritability,
            'has_concentration_issues': self.has_concentration_issues,
            'notes': self.notes,
            'entry_date': self.entry_date.isoformat() if self.entry_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class MentalHealthJournal(db.Model):
    """Journal entries for mental wellness reflection"""
    __tablename__ = 'mental_health_journals'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    reflection = db.Column(db.Text, nullable=False)
    gratitude = db.Column(db.Text)
    challenges = db.Column(db.Text)
    entry_date = db.Column(db.Date, nullable=False, default=datetime.utcnow, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    user = db.relationship('User', backref='mental_health_journals')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'reflection': self.reflection,
            'gratitude': self.gratitude,
            'challenges': self.challenges,
            'entry_date': self.entry_date.isoformat() if self.entry_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class FamilyMember(db.Model):
    """Family member health tracking"""
    __tablename__ = 'family_members'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer)
    relation = db.Column(db.String(50), nullable=False)  # Mother, Father, Sister, Brother, Spouse, Child, etc.
    health_history = db.Column(db.Text)  # Medical history
    blood_type = db.Column(db.String(5))  # Blood type
    chronic_conditions = db.Column(db.Text)  # Chronic conditions
    current_medications = db.Column(db.Text)  # Current medications
    contact_number = db.Column(db.String(20))  # Emergency contact
    is_active = db.Column(db.Boolean, default=True)  # Active status
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref='family_members')
    vital_signs = db.relationship('FamilyVitalSign', backref='family_member', lazy='dynamic', cascade='all, delete-orphan')
    health_scores = db.relationship('FamilyMemberHealthScore', backref='family_member', lazy='dynamic', cascade='all, delete-orphan')
    alerts = db.relationship('FamilyMemberAlert', backref='family_member', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'age': self.age,
            'relation': self.relation,
            'health_history': self.health_history,
            'blood_type': self.blood_type,
            'chronic_conditions': self.chronic_conditions,
            'current_medications': self.current_medications,
            'contact_number': self.contact_number,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class FamilyVitalSign(db.Model):
    """Vital signs for tracked family members"""
    __tablename__ = 'family_vital_signs'

    id = db.Column(db.Integer, primary_key=True)
    family_member_id = db.Column(db.Integer, db.ForeignKey('family_members.id'), nullable=False, index=True)
    heart_rate = db.Column(db.Integer)  # bpm
    blood_pressure_systolic = db.Column(db.Integer)  # mmHg
    blood_pressure_diastolic = db.Column(db.Integer)  # mmHg
    oxygen_level = db.Column(db.Float)  # %
    temperature = db.Column(db.Float)  # Celsius
    weight = db.Column(db.Float)  # kg
    notes = db.Column(db.Text)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            'id': self.id,
            'family_member_id': self.family_member_id,
            'heart_rate': self.heart_rate,
            'blood_pressure_systolic': self.blood_pressure_systolic,
            'blood_pressure_diastolic': self.blood_pressure_diastolic,
            'oxygen_level': self.oxygen_level,
            'temperature': self.temperature,
            'weight': self.weight,
            'notes': self.notes,
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None
        }


class FamilyMemberHealthScore(db.Model):
    """Health score snapshots for family members"""
    __tablename__ = 'family_member_health_scores'

    id = db.Column(db.Integer, primary_key=True)
    family_member_id = db.Column(db.Integer, db.ForeignKey('family_members.id'), nullable=False, index=True)
    score = db.Column(db.Float, nullable=False)
    cardiovascular_score = db.Column(db.Float)
    respiratory_score = db.Column(db.Float)
    metabolic_score = db.Column(db.Float)
    trend = db.Column(db.String(20), default='stable')  # improving, stable, declining
    calculated_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            'id': self.id,
            'family_member_id': self.family_member_id,
            'score': self.score,
            'cardiovascular_score': self.cardiovascular_score,
            'respiratory_score': self.respiratory_score,
            'metabolic_score': self.metabolic_score,
            'trend': self.trend,
            'calculated_at': self.calculated_at.isoformat() if self.calculated_at else None
        }


class FamilyMemberAlert(db.Model):
    """Alerts for family member monitoring (including parent-specific alerts)"""
    __tablename__ = 'family_member_alerts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    family_member_id = db.Column(db.Integer, db.ForeignKey('family_members.id'), nullable=False, index=True)
    alert_type = db.Column(db.String(50), nullable=False)  # critical_vitals, warning_vitals, low_health_score
    severity = db.Column(db.String(20), nullable=False)  # info, warning, critical
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_parent_alert = db.Column(db.Boolean, default=False)
    is_read = db.Column(db.Boolean, default=False)
    is_resolved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    resolved_at = db.Column(db.DateTime)

    user = db.relationship('User', backref='family_member_alerts')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'family_member_id': self.family_member_id,
            'alert_type': self.alert_type,
            'severity': self.severity,
            'title': self.title,
            'message': self.message,
            'is_parent_alert': self.is_parent_alert,
            'is_read': self.is_read,
            'is_resolved': self.is_resolved,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None
        }


class EmergencyContact(db.Model):
    """Emergency contact information for SOS alerts"""
    __tablename__ = 'emergency_contacts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    relationship = db.Column(db.String(50))  # Spouse, Parent, Sibling, Friend, Doctor, etc.
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120))
    priority = db.Column(db.Integer, default=1)  # 1=Primary, 2=Secondary, 3=Tertiary
    notify_via_sms = db.Column(db.Boolean, default=True)
    notify_via_email = db.Column(db.Boolean, default=True)
    is_active = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', backref='emergency_contacts')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'relationship': self.relationship,
            'phone': self.phone,
            'email': self.email,
            'priority': self.priority,
            'notify_via_sms': self.notify_via_sms,
            'notify_via_email': self.notify_via_email,
            'is_active': self.is_active,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class SOSEvent(db.Model):
    """Emergency SOS activation log"""
    __tablename__ = 'sos_events'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    location_address = db.Column(db.Text)
    emergency_type = db.Column(db.String(50))  # Medical, Accident, Other
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='active')  # active, resolved, cancelled
    contacts_notified = db.Column(db.Text)  # JSON list of notified contact IDs
    emergency_services_notified = db.Column(db.Boolean, default=False)
    response_time = db.Column(db.Integer)  # seconds until help arrived
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    resolved_at = db.Column(db.DateTime)

    user = db.relationship('User', backref='sos_events')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'location_address': self.location_address,
            'emergency_type': self.emergency_type,
            'description': self.description,
            'status': self.status,
            'contacts_notified': self.contacts_notified,
            'emergency_services_notified': self.emergency_services_notified,
            'response_time': self.response_time,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None
        }


class HealthProgramEvent(db.Model):
    """Health programs and event reminders for users"""
    __tablename__ = 'health_program_events'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    event_type = db.Column(db.String(50), default='program')  # yoga, camp, meditation, reminder
    start_datetime = db.Column(db.DateTime, nullable=False, index=True)
    end_datetime = db.Column(db.DateTime)
    location = db.Column(db.String(255))
    is_virtual = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    user = db.relationship('User', backref='health_program_events')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'description': self.description,
            'event_type': self.event_type,
            'start_datetime': self.start_datetime.isoformat() if self.start_datetime else None,
            'end_datetime': self.end_datetime.isoformat() if self.end_datetime else None,
            'location': self.location,
            'is_virtual': self.is_virtual,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class FitnessChallenge(db.Model):
    """Fitness challenges (e.g. 10,000 steps challenge)"""
    __tablename__ = 'fitness_challenges'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    target_value = db.Column(db.Integer, nullable=False, default=10000)
    current_value = db.Column(db.Integer, default=0)
    unit = db.Column(db.String(20), default='steps')
    start_date = db.Column(db.Date, nullable=False, index=True)
    end_date = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)
    completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    user = db.relationship('User', backref='fitness_challenges')

    def to_dict(self):
        progress_pct = 0
        if self.target_value and self.target_value > 0:
            progress_pct = min(round((self.current_value / self.target_value) * 100, 2), 100)
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'description': self.description,
            'target_value': self.target_value,
            'current_value': self.current_value,
            'unit': self.unit,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'is_active': self.is_active,
            'progress_pct': progress_pct,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class DailyReminder(db.Model):
    """Daily reminders for wellness routines"""
    __tablename__ = 'daily_reminders'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    reminder_type = db.Column(db.String(50), default='wellness')  # hydration, steps, meditation, yoga
    message = db.Column(db.Text)
    reminder_time = db.Column(db.String(5), default='08:00')  # HH:MM
    days_of_week = db.Column(db.String(50), default='Mon,Tue,Wed,Thu,Fri,Sat,Sun')
    is_enabled = db.Column(db.Boolean, default=True)
    last_sent_at = db.Column(db.DateTime, nullable=True, index=True)  # Track when last notification was sent
    notification_count = db.Column(db.Integer, default=0)  # Count of notifications sent
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', backref='daily_reminders')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'reminder_type': self.reminder_type,
            'message': self.message,
            'reminder_time': self.reminder_time,
            'days_of_week': self.days_of_week,
            'is_enabled': self.is_enabled,
            'last_sent_at': self.last_sent_at.isoformat() if self.last_sent_at else None,
            'notification_count': self.notification_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

