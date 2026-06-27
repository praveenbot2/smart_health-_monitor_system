import os

from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
from flask_mail import Mail
from config import Config

# Import extensions from database module
from database import db, login_manager

# Other extensions


def _get_socketio_async_mode():
    """Pick a stable SocketIO async mode with graceful fallback."""
    preferred_mode = os.getenv('SOCKETIO_ASYNC_MODE', 'threading').strip().lower()

    if preferred_mode == 'eventlet':
        try:
            import eventlet  # noqa: F401
            return 'eventlet'
        except Exception:
            return 'threading'

    return preferred_mode


socketio = SocketIO(cors_allowed_origins="*", async_mode=_get_socketio_async_mode())
mail = Mail()

def create_app(config_class=Config):
    """Application factory"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    CORS(app)
    socketio.init_app(app)
    mail.init_app(app)
    
    # Login manager settings
    login_manager.login_view = 'main.login_page'
    login_manager.login_message = 'Please log in to access this page.'
    
    # Register user_loader after login_manager is initialized
    @login_manager.user_loader
    def load_user(user_id):
        from database.models import User
        return User.query.get(int(user_id))
    
    # Register blueprints
    from app.routes import auth, vitals, predictions, health_score, chatbot, doctors, appointments, alerts, reports, admin, main
    from app.routes import health_records, doctor_booking, results, mental_health, events
    
    # Register main routes first
    app.register_blueprint(main.bp)
    
    # Register authentication
    app.register_blueprint(auth.bp)
    
    # Register vitals and health monitoring
    app.register_blueprint(vitals.bp)
    app.register_blueprint(health_records.bp)
    
    # Register predictions and health score
    app.register_blueprint(predictions.bp)
    app.register_blueprint(health_score.bp)
    app.register_blueprint(results.bp)
    
    # Register AI chatbot
    app.register_blueprint(chatbot.bp)
    
    # Register doctor and appointment management
    app.register_blueprint(doctors.bp)
    app.register_blueprint(appointments.bp)
    app.register_blueprint(doctor_booking.bp)
    
    # Register alerts and reports
    app.register_blueprint(alerts.bp)
    app.register_blueprint(reports.bp)
    app.register_blueprint(events.bp)
    
    # Register emergency SOS module
    from app.routes import emergency
    app.register_blueprint(emergency.bp)
    
    # Register mental health module
    app.register_blueprint(mental_health.bp)
    
    # Register family members module
    from app.routes import family
    app.register_blueprint(family.bp)
    
    # Register admin
    app.register_blueprint(admin.bp)
    
    # Register patient data blueprint
    try:
        from app.routes import patient_data
        app.register_blueprint(patient_data.bp)
    except Exception as e:
        print(f'Warning: Could not register patient_data blueprint: {e}')
    
    # Create database tables
    with app.app_context():
        db.create_all()
        
        # Initialize ML models
        try:
            from app.ml.model_trainer import initialize_models
            initialize_models()
        except Exception as e:
            app.logger.warning(f'Could not initialize ML models: {e}')
    
    return app
